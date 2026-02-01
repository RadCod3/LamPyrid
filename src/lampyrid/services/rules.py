"""Rule Service for LamPyrid.

This service handles rule-related business logic and orchestrates
operations between the MCP tools and the Firefly III client.
"""

import re
from typing import List

from pydantic import ValidationError

from ..clients.firefly import FireflyClient
from ..models.firefly_models import RuleTriggerUpdate, RuleUpdate
from ..models.lampyrid_models import (
    ExecuteRuleRequest,
    GetRuleRequest,
    Rule,
    RuleActionSimple,
    RuleExecuteResult,
    RuleTestResult,
    RuleTriggerSimple,
    SearchRulesRequest,
    TestRuleRequest,
    Transaction,
    UpdateRuleRequest,
)


class RuleService:
    """Service for managing Firefly III rules.

    This service provides a high-level interface for rule operations,
    handling filtering, regex matching, and multi-call orchestration
    while delegating HTTP operations to the FireflyClient.
    """

    def __init__(self, client: FireflyClient) -> None:
        """Initialize the rule service with a FireflyClient instance."""
        self._client = client

    async def search_rules(self, req: SearchRulesRequest) -> List[Rule]:
        """Search rules with client-side filtering.

        Since Firefly III has no server-side rule search, this fetches all rules
        and filters them client-side using keyword matching and regex patterns.

        Args:
            req: Request containing search criteria

        Returns:
            List of rules matching the filter criteria

        Raises:
            ValueError: If regex patterns are invalid

        """
        # Compile regex patterns early to catch errors
        trigger_pattern = None
        action_pattern = None

        if req.trigger_value_pattern:
            try:
                trigger_pattern = re.compile(req.trigger_value_pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f'Invalid trigger_value_pattern regex: {e}')

        if req.action_value_pattern:
            try:
                action_pattern = re.compile(req.action_value_pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f'Invalid action_value_pattern regex: {e}')

        # Fetch all rules with pagination
        all_rules = []
        page = 1
        while True:
            rule_array = await self._client.get_rules(page)
            all_rules.extend(rule_array.data)

            # Check pagination safely (can be None)
            if (
                not rule_array.meta.pagination
                or rule_array.meta.pagination.current_page >= rule_array.meta.pagination.total_pages
            ):
                break
            page += 1

        # Filter client-side
        filtered_rules = []
        for rule_read in all_rules:
            rule_attrs = rule_read.attributes

            # Filter by active status if specified
            if req.active is not None and rule_attrs.active != req.active:
                continue

            # Filter by title if specified
            if req.title_contains:
                if req.title_contains.lower() not in rule_attrs.title.lower():
                    continue

            # Filter by trigger type keyword if specified
            if req.trigger_type:
                trigger_keywords = [t.type.value for t in rule_attrs.triggers]
                if not any(req.trigger_type.lower() in kw.lower() for kw in trigger_keywords):
                    continue

            # Filter by trigger value pattern if specified
            if trigger_pattern:
                trigger_values = [t.value for t in rule_attrs.triggers if t.value]
                if not any(trigger_pattern.search(v) for v in trigger_values):
                    continue

            # Filter by action type keyword if specified
            if req.action_type:
                action_keywords = [a.type.value for a in rule_attrs.actions]
                if not any(req.action_type.lower() in kw.lower() for kw in action_keywords):
                    continue

            # Filter by action value pattern if specified
            if action_pattern:
                action_values = [a.value for a in rule_attrs.actions if a.value]
                if not any(action_pattern.search(v) for v in action_values):
                    continue

            # All filters passed, include this rule
            filtered_rules.append(rule_read)

        # Convert to simplified models
        return [
            Rule(
                id=rule_read.id,
                title=rule_read.attributes.title,
                description=rule_read.attributes.description,
                active=rule_read.attributes.active or True,
                strict=rule_read.attributes.strict,
                stop_processing=rule_read.attributes.stop_processing or False,
                trigger=rule_read.attributes.trigger.value,
                triggers=[
                    RuleTriggerSimple(
                        type=t.type,
                        value=t.value,
                        prohibited=t.prohibited or False,
                    )
                    for t in rule_read.attributes.triggers
                ],
                actions=[
                    RuleActionSimple(
                        type=a.type,
                        value=a.value,
                    )
                    for a in rule_read.attributes.actions
                ],
            )
            for rule_read in filtered_rules
        ]

    async def get_rule(self, req: GetRuleRequest) -> Rule:
        """Get detailed information for a single rule.

        Args:
            req: Request containing the rule ID

        Returns:
            Rule details

        """
        rule_single = await self._client.get_rule(req.id)
        rule_attrs = rule_single.data.attributes

        return Rule(
            id=rule_single.data.id,
            title=rule_attrs.title,
            description=rule_attrs.description,
            active=rule_attrs.active or True,
            strict=rule_attrs.strict,
            stop_processing=rule_attrs.stop_processing or False,
            trigger=rule_attrs.trigger.value,
            triggers=[
                RuleTriggerSimple(
                    type=t.type,
                    value=t.value,
                    prohibited=t.prohibited or False,
                )
                for t in rule_attrs.triggers
            ],
            actions=[
                RuleActionSimple(
                    type=a.type,
                    value=a.value,
                )
                for a in rule_attrs.actions
            ],
        )

    async def update_rule(self, req: UpdateRuleRequest) -> Rule:
        """Update an existing rule.

        Args:
            req: Request containing the rule ID and updates

        Returns:
            Updated rule details

        Raises:
            ValueError: If trigger/action dicts have invalid formats

        """
        # Build the RuleUpdate object from the request
        rule_update = RuleUpdate(
            title=req.title,
            description=req.description,
            rule_group_id=req.rule_group_id,
            active=req.active,
            strict=req.strict,
            stop_processing=req.stop_processing,
        )

        # Convert triggers array to RuleTriggerUpdate objects if provided
        if req.triggers is not None:
            try:
                rule_update.triggers = [RuleTriggerUpdate(**t) for t in req.triggers]
            except ValidationError as e:
                raise ValueError(f'Invalid trigger format: {e}')

        # Convert actions array to RuleActionUpdate objects if provided
        if req.actions is not None:
            try:
                from ..models.firefly_models import RuleActionUpdate

                rule_update.actions = [RuleActionUpdate(**a) for a in req.actions]
            except ValidationError as e:
                raise ValueError(f'Invalid action format: {e}')

        # Call the client to update the rule
        rule_single = await self._client.update_rule(req.rule_id, rule_update)
        rule_attrs = rule_single.data.attributes

        return Rule(
            id=rule_single.data.id,
            title=rule_attrs.title,
            description=rule_attrs.description,
            active=rule_attrs.active or True,
            strict=rule_attrs.strict,
            stop_processing=rule_attrs.stop_processing or False,
            trigger=rule_attrs.trigger.value,
            triggers=[
                RuleTriggerSimple(
                    type=t.type,
                    value=t.value,
                    prohibited=t.prohibited or False,
                )
                for t in rule_attrs.triggers
            ],
            actions=[
                RuleActionSimple(
                    type=a.type,
                    value=a.value,
                )
                for a in rule_attrs.actions
            ],
        )

    async def test_rule(self, req: TestRuleRequest) -> RuleTestResult:
        """Test a rule in preview mode (show matches without changes).

        Args:
            req: Request containing rule ID and date range

        Returns:
            Test result with matched transactions (preview mode)

        """
        # Get the rule for its title
        rule_single = await self._client.get_rule(req.rule_id)
        rule_title = rule_single.data.attributes.title

        # Test the rule on the transactions
        transaction_array = await self._client.test_rule(
            req.rule_id, req.start_date, req.end_date, req.account_ids
        )

        # Convert transactions to simplified models
        matched_transactions = [
            Transaction.from_transaction_read(trx_read) for trx_read in transaction_array.data
        ]

        return RuleTestResult(
            rule_id=req.rule_id,
            rule_title=rule_title,
            matched_transaction_count=len(matched_transactions),
            matched_transactions=matched_transactions,
        )

    async def execute_rule(self, req: ExecuteRuleRequest) -> RuleExecuteResult:
        """Execute a rule (apply changes to matching transactions).

        Args:
            req: Request containing rule ID and execution parameters

        Returns:
            Execution result

        Raises:
            ValueError: If confirm is not True (safety check)

        """
        # Safety check: require explicit confirmation
        if not req.confirm:
            raise ValueError(
                'Rule execution requires confirm=True to prevent accidental '
                'modifications. Use test_rule first to preview matches.'
            )

        # Get the rule for its title
        rule_single = await self._client.get_rule(req.rule_id)
        rule_title = rule_single.data.attributes.title

        # Execute the rule
        success = await self._client.trigger_rule(
            req.rule_id, req.start_date, req.end_date, req.account_ids
        )

        return RuleExecuteResult(
            rule_id=req.rule_id,
            rule_title=rule_title,
            success=success,
            message=(
                'Rule execution accepted and queued for processing. '
                'Firefly III applies rule changes asynchronously. '
                'Check the rule or transactions later to confirm changes.'
            ),
        )

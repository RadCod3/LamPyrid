"""Rule Management MCP Tools.

This module provides MCP tools for managing Firefly III rules including
searching, retrieving, updating, testing (preview), and executing rules.
"""

from typing import List

from fastmcp import FastMCP

from ..clients.firefly import FireflyClient
from ..models.lampyrid_models import (
    ExecuteRuleRequest,
    GetRuleRequest,
    Rule,
    RuleExecuteResult,
    RuleTestResult,
    SearchRulesRequest,
    TestRuleRequest,
    UpdateRuleRequest,
)
from ..services.rules import RuleService


def create_rules_server(client: FireflyClient) -> FastMCP:
    """Create a standalone FastMCP server for rule management tools.

    Args:
        client: The FireflyClient instance for API interactions

    Returns:
        FastMCP server instance with rule management tools registered

    """
    rule_service = RuleService(client)

    rules_mcp = FastMCP('rules')

    @rules_mcp.tool(tags={'rules', 'search'})
    async def search_rules(req: SearchRulesRequest) -> List[Rule]:
        """Search your rules using multiple filter criteria.

        Since Firefly III doesn't have a built-in rule search API, this tool
        fetches all rules and filters them client-side using keyword matching
        and regex patterns for maximum flexibility.

        Provide at least one search criterion. All criteria are combined with AND logic.
        """
        return await rule_service.search_rules(req)

    @rules_mcp.tool(tags={'rules'})
    async def get_rule(req: GetRuleRequest) -> Rule:
        """Retrieve a single rule by ID with all its triggers and actions.

        Returns the complete rule configuration including triggers (conditions)
        and actions (what to do when the rule matches).
        """
        return await rule_service.get_rule(req)

    @rules_mcp.tool(tags={'rules', 'modify'})
    async def update_rule(req: UpdateRuleRequest) -> Rule:
        """Update an existing rule's configuration.

        You can update any combination of:
        - Basic settings (title, description, active status)
        - Logic control (strict mode, stop processing)
        - Triggers (conditions that must match)
        - Actions (changes to apply)

        Note: The 'prohibited' field on triggers is read-only and cannot be modified.
        """
        return await rule_service.update_rule(req)

    @rules_mcp.tool(tags={'rules', 'test'})
    async def test_rule(req: TestRuleRequest) -> RuleTestResult:
        """Preview which transactions a rule would match WITHOUT applying changes.

        Use this before executing a rule to see what would be affected.
        This is a read-only operation - no transactions are modified.

        Returns the list of matching transactions that would be changed
        if the rule is executed.
        """
        return await rule_service.test_rule(req)

    @rules_mcp.tool(tags={'rules', 'execute'})
    async def execute_rule(req: ExecuteRuleRequest) -> RuleExecuteResult:
        """Execute a rule to apply changes to matching transactions.

        WARNING: This is a destructive operation that modifies your transactions.
        - Always use test_rule first to preview what will be changed
        - Requires confirm=True to prevent accidental execution
        - Execution happens asynchronously - changes may take a moment
        - Date ranges are REQUIRED - no defaults are applied

        Rule execution in Firefly III is asynchronous. The rule will be queued
        for processing and applied in the background. Check your transactions
        later to confirm the changes have been applied.
        """
        return await rule_service.execute_rule(req)

    return rules_mcp

# LamPyrid

A Model Context Protocol (MCP) server providing comprehensive tools for interacting with Firefly III personal finance software. LamPyrid enables automated personal finance workflows and analysis through 17+ MCP tools with support for account management, transaction operations, and budget management.

## Features

- **Comprehensive Account Management**: List, search, and retrieve account information across all Firefly III account types
- **Transaction Operations**: Full CRUD operations for transactions with support for withdrawals, deposits, and transfers
- **Budget Management**: Complete budget analysis with spending tracking, allocation, and summary reporting
- **Type Safety**: Full type hints and Pydantic validation throughout the codebase
- **Async Operations**: Non-blocking HTTP operations for optimal performance
- **Robust Error Handling**: Comprehensive error handling across all API interactions

## Quick Start

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) package manager
- Access to a Firefly III instance with API token

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LamPyrid
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
# Create a .env file or set environment variables
FIREFLY_BASE_URL=https://your-firefly-instance.com
FIREFLY_TOKEN=your-api-token
```

4. Run the MCP server:
```bash
uv run lampyrid
```

## Configuration

LamPyrid uses environment variables for configuration:

- `FIREFLY_BASE_URL`: URL of your Firefly III instance
- `FIREFLY_TOKEN`: Bearer token for API authentication

Configuration can be provided via a `.env` file in the project root or as environment variables.

## Available MCP Tools

### Account Management
- `list_accounts` - List accounts by type (asset, expense, revenue, etc.)
- `search_accounts` - Search accounts by name with optional type filtering
- `get_account` - Get detailed information for a single account

### Transaction Management
- `get_transactions` - Retrieve transactions with time range and type filtering
- `search_transactions` - Search transactions by description or text fields
- `get_transaction` - Get detailed information for a single transaction
- `create_withdrawal` - Create withdrawal transactions with budget allocation
- `create_deposit` - Create deposit transactions
- `create_transfer` - Create transfer transactions between accounts
- `delete_transaction` - Delete transactions by ID
- `update_transaction_budget` - Update or clear budget allocation for transactions

### Budget Management
- `list_budgets` - List all budgets with optional filtering
- `get_budget` - Get detailed budget information
- `get_budget_spending` - Analyze spending for specific budgets and periods
- `get_budget_summary` - Comprehensive summary of all budgets with spending
- `get_available_budget` - Check available budget amounts for periods

All tools include comprehensive error handling and return structured data optimized for MCP integration.

## Development

### Setup Development Environment

```bash
# Install with test dependencies
uv sync --group test

# Format code
uv run ruff format

# Lint code
uv run ruff check --fix

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=lampyrid --cov-report=term-missing
```

### Project Structure

```
LamPyrid/
+-- src/lampyrid/           # Main package
|   +-- server.py          # FastMCP server with MCP tools
|   +-- config.py          # Environment configuration
|   +-- clients/
|   |   \-- firefly.py     # Firefly III HTTP client
|   \-- models/
|       +-- firefly_models.py    # Auto-generated API models
|       \-- lampyrid_models.py   # Simplified MCP models
+-- tests/                 # Test suite
|   +-- unit/             # Unit tests
|   +-- integration/      # Integration tests
|   \-- conftest.py       # Test fixtures
\-- pyproject.toml        # Project configuration
```

### Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit
uv run pytest tests/integration

# Run with coverage
uv run pytest --cov=lampyrid

# Run specific tests
uv run pytest -k "test_account"
```

Test categories:
- Unit tests (`@pytest.mark.unit`): Fast, isolated component tests
- Integration tests (`@pytest.mark.integration`): End-to-end workflow tests with mocked APIs

## Architecture

LamPyrid follows a clean layered architecture:

- **Server Layer**: FastMCP server exposing MCP tools with comprehensive tagging
- **Client Layer**: HTTP client for Firefly III API with full CRUD support
- **Models Layer**: Type-safe data models with Pydantic validation
- **Configuration**: Environment-based settings management

The architecture enables easy extension and modification while maintaining type safety and comprehensive error handling throughout.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Run the test suite and ensure all tests pass
5. Submit a pull request

Please ensure all code follows the project's style guidelines:
- Use tabs for indentation
- Single quotes for strings
- 100 character line limit
- Type hints for all functions
- Comprehensive test coverage

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
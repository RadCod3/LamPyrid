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

- Python 3.13+
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

### Required Configuration

- `FIREFLY_BASE_URL`: URL of your Firefly III instance
- `FIREFLY_TOKEN`: Personal access token for API authentication

### Optional: Google OAuth Authentication

For remote server deployments requiring authentication, you can enable Google OAuth:

- `GOOGLE_CLIENT_ID`: Google OAuth 2.0 client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 2.0 client secret
- `SERVER_BASE_URL`: Your server's public URL (e.g., `http://localhost:8000`)

**Note**: Authentication is optional and only needed for remote server deployments. All three OAuth variables must be provided together to enable authentication.

Configuration can be provided via a `.env` file in the project root or as environment variables.

### Setting Up Google OAuth

If you need authentication for remote server deployment:

1. **Go to Google Cloud Console**: Visit [console.cloud.google.com](https://console.cloud.google.com)
2. **Create or select a project**: Choose an existing project or create a new one
3. **Enable APIs**:
   - Navigate to "APIs & Services" → "Library"
   - Search for and enable "Google+ API"
4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type (unless you have Google Workspace)
   - Fill in required fields: app name, user support email, developer contact
   - Add scopes: `openid`, `email`, `profile`
   - Save and continue
5. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "LamPyrid MCP Server"
   - Add authorized redirect URI: `{SERVER_BASE_URL}/auth/callback`
     - For local development: `http://localhost:8000/auth/callback`
     - For production: `https://your-domain.com/auth/callback`
   - Click "Create"
   - Copy the Client ID and Client Secret
6. **Configure Environment**: Add to your `.env` file:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   SERVER_BASE_URL=http://localhost:8000
   ```

## Claude Desktop Integration

To use LamPyrid with Claude Desktop, add the following configuration to your Claude Desktop MCP settings:

### Configuration Steps

1. **Install LamPyrid**: Ensure LamPyrid is installed and configured with your Firefly III credentials
2. **Configure Claude Desktop**: Add the server configuration to your Claude Desktop settings file

### Claude Desktop Settings

**Option 1: Local Installation (stdio mode)**
```json
{
  "mcpServers": {
    "lampyrid": {
      "command": "uv",
      "args": ["run", "lampyrid"],
      "cwd": "/path/to/your/LamPyrid",
      "env": {
        "FIREFLY_BASE_URL": "https://your-firefly-instance.com",
        "FIREFLY_TOKEN": "your-personal-access-token"
      }
    }
  }
}
```

**Option 2: Docker Container (HTTP mode)**
```json
{
  "mcpServers": {
    "lampyrid": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "MCP_TRANSPORT=stdio",
        "-e", "FIREFLY_BASE_URL=https://your-firefly-instance.com",
        "-e", "FIREFLY_TOKEN=your-personal-access-token",
        "ghcr.io/radcod3/lampyrid:latest"
      ]
    }
  }
}
```

**Option 3: HTTP Connection to Running Container**
If you have LamPyrid running in HTTP mode (e.g., via docker-compose), you can connect directly:
```json
{
  "mcpServers": {
    "lampyrid": {
      "url": "http://localhost:3000"
    }
  }
}
```

### Environment Variables

You can also use a `.env` file in your LamPyrid directory instead of inline environment variables:

```bash
# .env file in LamPyrid directory
FIREFLY_BASE_URL=https://your-firefly-instance.com
FIREFLY_TOKEN=your-personal-access-token
```

After configuration, restart Claude Desktop. LamPyrid tools will be available for account management, transaction operations, and budget analysis.

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
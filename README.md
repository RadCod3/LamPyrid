# LamPyrid

A Model Context Protocol (MCP) server providing comprehensive tools for interacting with Firefly III personal finance software. LamPyrid enables automated personal finance workflows and analysis through 18 MCP tools with support for account management, transaction operations, and budget management.

## Features

- **Comprehensive Account Management**: List, search, and retrieve account information across all Firefly III account types
- **Transaction Operations**: Full CRUD operations for transactions with support for withdrawals, deposits, and transfers
- **Bulk Operations**: Efficient bulk transaction creation and updates for high-volume workflows
- **Budget Management**: Complete budget analysis with spending tracking, allocation, and summary reporting
- **Docker Support**: Production-ready Docker images with multi-platform support (amd64/arm64)
- **Type Safety**: Full type hints and Pydantic validation throughout the codebase
- **Async Operations**: Non-blocking HTTP operations for optimal performance
- **Robust Error Handling**: Comprehensive error handling across all API interactions

## Quick Start

### Option 1: Docker (Recommended)

The fastest way to get started is using the published Docker image:

```bash
# Pull the latest image
docker pull ghcr.io/radcod3/lampyrid:latest

# Run with stdio mode (for Claude Desktop)
docker run --rm -i \
  -e MCP_TRANSPORT=stdio \
  -e FIREFLY_BASE_URL=https://your-firefly-instance.com \
  -e FIREFLY_TOKEN=your-api-token \
  ghcr.io/radcod3/lampyrid:latest

# Or use docker-compose
cat > docker-compose.yml <<EOF
services:
  lampyrid:
    image: ghcr.io/radcod3/lampyrid:latest
    ports:
      - "3000:3000"
    environment:
      FIREFLY_BASE_URL: https://your-firefly-instance.com
      FIREFLY_TOKEN: your-api-token
    volumes:
      # Persist OAuth tokens if authentication is enabled
      - ./data/oauth:/app/data/oauth
    restart: unless-stopped
EOF
docker-compose up -d
```

### Option 2: Local Installation

#### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- Access to a Firefly III instance with API token

#### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/RadCod3/LamPyrid.git
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

### Server Configuration (Optional)

- `MCP_TRANSPORT`: Transport protocol (stdio/http/sse, default: stdio)
- `MCP_HOST`: Host binding for HTTP/SSE transports (default: 0.0.0.0)
- `MCP_PORT`: Port binding for HTTP/SSE transports (default: 3000)
- `LOGGING_LEVEL`: Logging verbosity (DEBUG/INFO/WARNING/ERROR/CRITICAL, default: INFO)

### Google OAuth Authentication (Optional)

For remote server deployments requiring authentication, you can enable Google OAuth:

- `GOOGLE_CLIENT_ID`: Google OAuth 2.0 client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 2.0 client secret
- `SERVER_BASE_URL`: Your server's public URL (e.g., `http://localhost:8000`)

**Note**: Authentication is optional and only needed for remote server deployments. All three OAuth variables must be provided together to enable authentication.

### OAuth Token Persistence (Optional)

By default, OAuth tokens are stored in memory and lost on server restarts. To enable persistent authentication across restarts, configure encrypted token storage:

- `JWT_SIGNING_KEY`: JWT signing key for OAuth tokens
- `OAUTH_STORAGE_ENCRYPTION_KEY`: Fernet encryption key for token storage
- `OAUTH_STORAGE_PATH`: Storage path (default: `~/.local/share/lampyrid/oauth` for local, `/app/data/oauth` for Docker)

**Generate encryption keys:**
```bash
# Generate JWT signing key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**IMPORTANT**: Keep these keys secure and consistent across deployments. Changing keys will invalidate existing tokens and require users to re-authenticate.

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

### Account Management (3 tools)
- `list_accounts` - List accounts by type (asset, expense, revenue, etc.)
- `search_accounts` - Search accounts by name with optional type filtering
- `get_account` - Get detailed information for a single account

### Transaction Management (10 tools)
- `get_transactions` - Retrieve transactions with time range and type filtering
- `search_transactions` - Search transactions by description or text fields
- `get_transaction` - Get detailed information for a single transaction
- `create_withdrawal` - Create withdrawal transactions with budget allocation
- `create_deposit` - Create deposit transactions
- `create_transfer` - Create transfer transactions between accounts
- `create_bulk_transactions` - Create multiple transactions efficiently in a single operation
- `update_transaction` - Update existing transaction details (amount, description, accounts, budget, etc.)
- `bulk_update_transactions` - Update multiple transactions efficiently in a single operation
- `delete_transaction` - Delete transactions by ID

### Budget Management (5 tools)
- `list_budgets` - List all budgets with optional filtering
- `get_budget` - Get detailed budget information
- `get_budget_spending` - Analyze spending for specific budgets and periods
- `get_budget_summary` - Comprehensive summary of all budgets with spending
- `get_available_budget` - Check available budget amounts for periods

All tools include comprehensive error handling and return structured data optimized for MCP integration.

## Development

### Setup Development Environment

```bash
# Install dependencies
uv sync

# Format code
uv run ruff format

# Lint code
uv run ruff check --fix

# Build Docker image locally
docker build -t lampyrid:dev .

# Run local development server
uv run lampyrid
```

### Project Structure

```text
LamPyrid/
├── src/lampyrid/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Main entry point for MCP server
│   ├── server.py             # FastMCP server initialization and tool composition
│   ├── config.py             # Environment configuration
│   ├── utils.py              # Custom HTTP routes (favicon, etc.)
│   ├── clients/
│   │   └── firefly.py        # HTTP client for Firefly III API
│   ├── models/
│   │   ├── firefly_models.py # Auto-generated Firefly III API models
│   │   └── lampyrid_models.py# Simplified MCP interface models
│   └── tools/
│       ├── __init__.py       # Tool server composition coordinator
│       ├── accounts.py       # Account management tools (3 tools)
│       ├── transactions.py   # Transaction management tools (10 tools)
│       └── budgets.py        # Budget management tools (5 tools)
├── .github/workflows/        # CI/CD workflows
├── assets/                   # Project assets
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── pyproject.toml            # Project configuration and dependencies
└── README.md                 # Project documentation
```

## Architecture

LamPyrid follows a clean layered architecture with modular tool organization:

- **Server Layer** (`server.py`): FastMCP server initialization, authentication setup, and tool registration orchestration
- **Tools Layer** (`tools/`): Modular MCP tool definitions organized by domain
  - `accounts.py`: Account management tools (3 tools)
  - `transactions.py`: Transaction management tools (10 tools)
  - `budgets.py`: Budget management tools (5 tools)
- **Client Layer** (`clients/firefly.py`): HTTP client for Firefly III API with full CRUD support
- **Models Layer**:
  - `firefly_models.py`: Auto-generated Pydantic models from Firefly III OpenAPI spec
  - `lampyrid_models.py`: Simplified models for MCP tool interfaces
- **Configuration** (`config.py`): Environment-based settings using pydantic-settings

### Tool Registration Pattern
Tools are registered using FastMCP's native static composition pattern:
- Each tool module exports a `create_*_server(client)` function that returns a standalone FastMCP instance
- The `tools/__init__.py` module provides `compose_all_servers()` to coordinate composition
- The `server.py` uses `mcp.import_server()` to compose all domain servers into the main server
- This leverages FastMCP's built-in server composition while keeping modular organization

The architecture enables easy extension and modification while maintaining type safety and comprehensive error handling throughout.

## Docker Deployment

LamPyrid provides production-ready Docker images published to GitHub Container Registry.

### Available Images

- **Latest Stable**: `ghcr.io/radcod3/lampyrid:latest` (latest release - recommended for production)
- **Development**: `ghcr.io/radcod3/lampyrid:edge` (main branch - latest features, may be unstable)
- **Versioned**: `ghcr.io/radcod3/lampyrid:0.2.0`, `ghcr.io/radcod3/lampyrid:0.2`, `ghcr.io/radcod3/lampyrid:0`
- **Platforms**: linux/amd64, linux/arm64

### Running with Docker

```bash
# Run in stdio mode (for Claude Desktop integration)
docker run --rm -i \
  -e MCP_TRANSPORT=stdio \
  -e FIREFLY_BASE_URL=https://your-firefly-instance.com \
  -e FIREFLY_TOKEN=your-api-token \
  ghcr.io/radcod3/lampyrid:latest

# Run in HTTP mode
docker run -d \
  -p 3000:3000 \
  -e FIREFLY_BASE_URL=https://your-firefly-instance.com \
  -e FIREFLY_TOKEN=your-api-token \
  --name lampyrid \
  ghcr.io/radcod3/lampyrid:latest
```

### Using Docker Compose

```yaml
services:
  lampyrid:
    image: ghcr.io/radcod3/lampyrid:latest
    ports:
      - "3000:3000"
    environment:
      FIREFLY_BASE_URL: https://your-firefly-instance.com
      FIREFLY_TOKEN: your-api-token
      # Optional: Configure transport and logging
      MCP_TRANSPORT: http
      LOGGING_LEVEL: INFO
      # Optional: Enable OAuth token persistence
      # JWT_SIGNING_KEY: your-jwt-signing-key
      # OAUTH_STORAGE_ENCRYPTION_KEY: your-fernet-encryption-key
      # OAUTH_STORAGE_PATH: /app/data/oauth
    volumes:
      # Persist OAuth tokens across container restarts (if OAuth is enabled)
      - ./data/oauth:/app/data/oauth
    restart: unless-stopped
```

### Building Custom Images

```bash
# Build locally
docker build -t lampyrid:custom .

# Build for specific platform
docker buildx build --platform linux/amd64 -t lampyrid:custom .
```

## CI/CD and Releases

LamPyrid uses GitHub Actions for continuous integration and deployment:

### Automated Workflows

- **CI Workflow**: Runs on all pull requests
  - Code linting and formatting validation
  - Package build verification
  - Docker image build test

- **Docker Publish Workflow**: Runs on main branch and version tags
  - Multi-platform image builds (amd64/arm64)
  - Security scanning with Trivy
  - Publishes to ghcr.io with appropriate tags

- **Release Workflow**: Runs on version tags (e.g., `v0.2.0`)
  - Generates changelog from git commits
  - Creates GitHub release with installation instructions
  - Links to published Docker images

### Creating a Release

To create a new release:

1. Merge all features to main via pull requests
2. Create a release branch and update version in `pyproject.toml`
3. Merge the version bump PR
4. Create and push a version tag (e.g., `v0.2.0`)
5. GitHub Actions automatically builds and publishes the release

## Contributing

Contributions are welcome! Please follow this workflow:

1. **Fork the repository**
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following the code style guidelines below
4. **Test locally**:
   ```bash
   uv run ruff format
   uv run ruff check --fix
   uv run lampyrid  # Verify the server starts
   ```
5. **Commit your changes** with clear, descriptive messages
6. **Push to your fork** and create a pull request

### Code Style Guidelines

- **Indentation**: Use tabs for indentation
- **Quotes**: Single quotes for strings
- **Line Length**: 100 character line limit
- **Type Safety**: Type hints required for all functions and methods
- **Async Operations**: Use async/await pattern for HTTP operations
- **Documentation**: Include docstrings for all MCP tools and complex functions

### CI/CD Process

The main branch is protected with the following requirements:
- All pull requests must pass CI checks (linting, formatting, Docker build)
- GitHub Actions automatically run on all PRs
- Docker images are published on version tags and main branch pushes

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
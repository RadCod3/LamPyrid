# LamPyrid

A Model Context Protocol (MCP) server providing comprehensive tools for interacting with [Firefly III](https://github.com/firefly-iii/firefly-iii) personal finance software. LamPyrid enables automated personal finance workflows and analysis through 18 MCP tools with support for account management, transaction operations, and budget management.

> **What is Firefly III?** [Firefly III](https://www.firefly-iii.org/) is a free and open-source personal finance manager that helps you track expenses, income, budgets, and more. LamPyrid provides an MCP interface to automate interactions with your Firefly III instance.

## Features

- **Account Management**: List, search, and retrieve account information across all Firefly III account types
- **Transaction Operations**: Full CRUD operations for withdrawals, deposits, and transfers
- **Bulk Operations**: Efficient bulk transaction creation and updates
- **Budget Management**: Budget analysis with spending tracking and allocation
- **Docker Support**: Production-ready multi-platform images (amd64/arm64)

## Prerequisites

- Access to a Firefly III instance with a [Personal Access Token](https://docs.firefly-iii.org/how-to/firefly-iii/features/api/#personal-access-token)
- For local installation: Python 3.14+ and [uv](https://github.com/astral-sh/uv)
- For Docker: Docker installed on your system

## Adding to Claude

### Option 1: Local Setup (Claude Desktop)

Clone and install LamPyrid:

```bash
git clone https://github.com/RadCod3/LamPyrid.git
cd LamPyrid
uv sync
```

Add to your Claude Desktop configuration file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lampyrid": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/LamPyrid", "lampyrid"],
      "env": {
        "FIREFLY_BASE_URL": "https://your-firefly-instance.com",
        "FIREFLY_TOKEN": "your-personal-access-token"
      }
    }
  }
}
```

Restart Claude Desktop to enable LamPyrid tools.

### Option 2: Remote Setup (Claude Connector)

When hosted on a remote server, LamPyrid can be added as a **Claude Connector**, allowing you to use it across all Claude interfaces including **Claude mobile apps** (iOS/Android), Claude web, and Claude Desktop.

**1. Deploy LamPyrid to a remote server:**

```yaml
# docker-compose.yml
services:
  lampyrid:
    image: ghcr.io/radcod3/lampyrid:latest
    ports:
      - "3000:3000"
    env_file:
      - .env
    restart: unless-stopped
```

```bash
# .env
FIREFLY_BASE_URL=https://your-firefly-instance.com
FIREFLY_TOKEN=your-api-token
MCP_TRANSPORT=http
```

```bash
docker compose up -d
```

**2. Add as Claude Connector:**

1. Go to Claude **Settings** > **Connectors** > **Add connector**
2. Enter your server URL: `https://your-server-url.com/mcp`
3. LamPyrid is now available on all your Claude devices!

> **Security Note**: If hosting on a public server, it is strongly recommended to enable authentication. LamPyrid currently supports Google OAuth - see the [Authentication](#authentication-optional) section below.

## Configuration

### Required

| Variable | Description |
|----------|-------------|
| `FIREFLY_BASE_URL` | URL of your Firefly III instance |
| `FIREFLY_TOKEN` | Personal access token for API authentication |

### Server Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport protocol: `stdio`, `http`, or `sse` |
| `MCP_HOST` | `0.0.0.0` | Host binding for HTTP/SSE transports |
| `MCP_PORT` | `3000` | Port binding for HTTP/SSE transports |
| `LOGGING_LEVEL` | `INFO` | Logging verbosity: DEBUG/INFO/WARNING/ERROR/CRITICAL |

### Authentication (Optional)

Recommended for remote deployments. Currently supports Google OAuth.

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 client secret |
| `SERVER_BASE_URL` | Your server's public URL (e.g., `https://lampyrid.example.com`) |

**Setting up Google OAuth:**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Navigate to **APIs & Services** > **OAuth consent screen** and configure
4. Go to **Credentials** > **Create Credentials** > **OAuth client ID**
5. Application type: **Web application**
6. Add authorized redirect URI: `{SERVER_BASE_URL}/auth/callback`
7. Copy the Client ID and Client Secret to your environment

### Token Persistence (Optional)

Enable persistent authentication across server restarts:

| Variable | Description |
|----------|-------------|
| `JWT_SIGNING_KEY` | JWT signing key (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `OAUTH_STORAGE_ENCRYPTION_KEY` | Fernet key (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `OAUTH_STORAGE_PATH` | Storage path (default: `/app/data/oauth` for Docker) |

## Available Tools

### Account Management (3 tools)
| Tool | Description |
|------|-------------|
| `list_accounts` | List accounts by type (asset, expense, revenue, etc.) |
| `search_accounts` | Search accounts by name with optional type filtering |
| `get_account` | Get detailed information for a single account |

### Transaction Management (10 tools)
| Tool | Description |
|------|-------------|
| `get_transactions` | Retrieve transactions with time range and type filtering |
| `search_transactions` | Search transactions by description or text fields |
| `get_transaction` | Get detailed information for a single transaction |
| `create_withdrawal` | Create withdrawal transactions with budget allocation |
| `create_deposit` | Create deposit transactions |
| `create_transfer` | Create transfer transactions between accounts |
| `create_bulk_transactions` | Create multiple transactions in a single operation |
| `update_transaction` | Update existing transaction details |
| `bulk_update_transactions` | Update multiple transactions in a single operation |
| `delete_transaction` | Delete transactions by ID |

### Budget Management (5 tools)
| Tool | Description |
|------|-------------|
| `list_budgets` | List all budgets with optional filtering |
| `get_budget` | Get detailed budget information |
| `get_budget_spending` | Analyze spending for specific budgets and periods |
| `get_budget_summary` | Comprehensive summary of all budgets with spending |
| `get_available_budget` | Check available budget amounts for periods |

## Docker

### Available Images

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release (recommended) |
| `edge` | Main branch (latest features, may be unstable) |
| `0.3.0`, `0.3`, `0` | Specific versions |

All images support `linux/amd64` and `linux/arm64` platforms.

```bash
docker pull ghcr.io/radcod3/lampyrid:latest
```

### Volume Permissions

If you encounter permission errors with OAuth storage, set the correct ownership:

```bash
mkdir -p ./data/oauth
sudo chown -R 65532:65532 ./data/oauth
```

## Development

```bash
# Install dependencies
uv sync

# Format and lint
uv run ruff format
uv run ruff check --fix

# Run the server
uv run lampyrid

# Run tests
uv run pytest
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make changes following the code style (run `uv run ruff format && uv run ruff check --fix`)
4. Submit a pull request

## License

GNU Affero General Public License v3.0 (AGPL-3.0) - see [LICENSE](LICENSE).

## Support

For issues and feature requests, use the [GitHub issue tracker](https://github.com/RadCod3/LamPyrid/issues).

import asyncio

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.utilities.logging import configure_logging
from fastmcp.utilities.types import Image
from mcp.types import Icon

from .clients.firefly import FireflyClient
from .config import settings
from .tools import compose_all_servers
from .utils import get_assets_path, register_custom_routes


def _create_auth_provider() :
	"""
	Create Google authentication provider if credentials are configured.

	Returns:
		GoogleProvider if all required credentials are present, None otherwise
	"""
	if settings.is_auth_enabled:
		return GoogleProvider(
			client_id=settings.google_client_id,  # ty:ignore[invalid-argument-type]
			client_secret=settings.google_client_secret,  # ty:ignore[invalid-argument-type]
			base_url=str(settings.server_base_url),
			required_scopes=[
				'openid',
				'https://www.googleapis.com/auth/userinfo.email',
			],
		)
	return None


def _initialize_server() -> FastMCP:
	"""
	Initialize and configure the FastMCP server with all domain servers.

	This function:
	1. Creates the main FastMCP server with authentication and icons
	2. Composes domain-specific servers (accounts, transactions, budgets) using static composition
	3. Registers custom HTTP routes

	Returns:
		Fully configured FastMCP server instance
	"""
	# Initialize FastMCP with optional authentication
	auth_provider = _create_auth_provider()

	# Load favicon icon
	favicon_icon = Icon(src=Image(path=str(get_assets_path('favicon.png'))).to_data_uri())

	server = FastMCP('lampyrid', auth=auth_provider, icons=[favicon_icon])
	client = FireflyClient()

	# Configure logging
	configure_logging(level='DEBUG')

	# Compose all domain servers using static composition (import_server)
	asyncio.run(compose_all_servers(server, client))

	# Register custom HTTP routes
	register_custom_routes(server)

	return server


# Create the main MCP server instance
mcp = _initialize_server()

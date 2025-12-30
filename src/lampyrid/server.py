from typing import Optional

from fastmcp import FastMCP
from fastmcp.server.auth.auth import AuthProvider
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.utilities.logging import configure_logging

from .clients.firefly import FireflyClient
from .config import settings
from .tools import register_all_tools


def _create_auth_provider() -> Optional[AuthProvider]:
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


# Initialize FastMCP with optional authentication
auth_provider = _create_auth_provider()
mcp = FastMCP('lampyrid', auth=auth_provider)
_client = FireflyClient()

# Configure logging
configure_logging(level='DEBUG')

# Register all MCP tools
register_all_tools(mcp, _client)

"""Google OIDC authentication provider for LamPyrid."""

from fastmcp.server.auth.oidc_proxy import OIDCProxy


class GoogleProvider(OIDCProxy):
	"""
	Google OIDC authentication provider.

	This provider uses Google's OpenID Connect implementation to authenticate
	users accessing the LamPyrid MCP server.

	Required configuration:
	- client_id: OAuth 2.0 client ID from Google Cloud Console
	- client_secret: OAuth 2.0 client secret from Google Cloud Console
	- base_url: Public URL of your FastMCP server

	Example:
		>>> from lampyrid.auth import GoogleProvider
		>>> auth = GoogleProvider(
		...     client_id='your-client-id.apps.googleusercontent.com',
		...     client_secret='your-client-secret',
		...     base_url='http://localhost:8000',
		... )
	"""

	def __init__(
		self,
		client_id: str,
		client_secret: str,
		base_url: str,
		**kwargs,
	):
		"""
		Initialize Google OIDC provider.

		Args:
			client_id: Google OAuth 2.0 client ID
			client_secret: Google OAuth 2.0 client secret
			base_url: Public URL of your FastMCP server
			**kwargs: Additional arguments passed to OIDCProxy
		"""
		# Google's OIDC discovery endpoint
		config_url = 'https://accounts.google.com/.well-known/openid-configuration'

		# Default scopes for Google authentication
		default_scopes = ['openid', 'email', 'profile']

		# Merge with any user-provided scopes
		required_scopes = kwargs.pop('required_scopes', default_scopes)

		super().__init__(
			config_url=config_url,
			client_id=client_id,
			client_secret=client_secret,
			base_url=base_url,
			required_scopes=required_scopes,
			**kwargs,
		)

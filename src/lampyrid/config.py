from pydantic import HttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Self


class Settings(BaseSettings):
	"""Application settings loaded from environment variables or .env file."""

	model_config = SettingsConfigDict(
		env_file='.env',
		env_file_encoding='utf-8',
		extra='ignore',
		case_sensitive=False,  # Allow FIREFLY_BASE_URL or firefly_base_url
	)

	# Firefly III Configuration (Required)
	firefly_base_url: HttpUrl = Field(
		description='Firefly III instance URL (e.g., https://firefly.example.com)'
	)
	firefly_token: str = Field(
		min_length=1,
		description='Personal access token for Firefly III API authentication',
	)

	# MCP Server Configuration (Optional - for transport settings)
	mcp_transport: str = Field(
		default='stdio',
		description='MCP transport mode: stdio (default), http, or sse',
	)
	mcp_host: str = Field(
		default='0.0.0.0',
		description='Host to bind the MCP server to (for http/sse transports)',
	)
	mcp_port: int = Field(
		default=3000,
		ge=1,
		le=65535,
		description='Port to bind the MCP server to (for http/sse transports)',
	)

	# Google OAuth Configuration (Optional - all three required together for remote auth)
	google_client_id: Optional[str] = Field(
		default=None, description='Google OAuth 2.0 client ID from Google Cloud Console'
	)
	google_client_secret: Optional[str] = Field(
		default=None, description='Google OAuth 2.0 client secret from Google Cloud Console'
	)
	server_base_url: Optional[HttpUrl] = Field(
		default=None,
		description="This server's base URL (e.g., http://localhost:8000 for development)",
	)

	@model_validator(mode='after')
	def validate_google_oauth_settings(self) -> Self:
		"""Ensure Google OAuth settings are all provided together or all absent."""
		oauth_fields = [self.google_client_id, self.google_client_secret, self.server_base_url]
		provided = [f for f in oauth_fields if f is not None]

		# If some but not all are provided, raise an error
		if 0 < len(provided) < 3:
			raise ValueError(
				'Google OAuth configuration is incomplete. All three fields must be provided together: '
				'GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and SERVER_BASE_URL. '
				f'Currently provided: {len(provided)}/3'
			)

		return self

	@property
	def is_auth_enabled(self) -> bool:
		"""Check if Google OAuth authentication is enabled."""
		return all([self.google_client_id, self.google_client_secret, self.server_base_url])


def _init_settings() -> Settings:
	"""Initialize settings with user-friendly error handling."""
	try:
		return Settings.model_validate({})
	except Exception as e:
		import sys
		from pydantic_core import ValidationError

		if isinstance(e, ValidationError):
			print(
				'\n❌ Configuration Error: Missing required environment variables\n',
				file=sys.stderr,
			)
			print('The following required settings are missing or invalid:\n', file=sys.stderr)

			for error in e.errors():
				field = str(error['loc'][0]) if error['loc'] else 'unknown'
				error_type = error['type']

				if error_type == 'missing':
					print(f'  • {field.upper()}: This field is required', file=sys.stderr)
				else:
					msg = error.get('msg', 'Invalid value')
					print(f'  • {field.upper()}: {msg}', file=sys.stderr)

			print('\nPlease set these variables in your .env file or environment.', file=sys.stderr)
			print('Example .env file:\n', file=sys.stderr)
			print('  FIREFLY_BASE_URL=https://firefly.example.com', file=sys.stderr)
			print('  FIREFLY_TOKEN=your_token_here', file=sys.stderr)
			print('\nSee .env.example for a complete configuration template.', file=sys.stderr)
			sys.exit(1)
		else:
			# Re-raise unexpected errors
			raise


# Initialize settings - will fail gracefully with clear errors if required settings are missing
settings = _init_settings()

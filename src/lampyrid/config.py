from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
	# Explicitly set environment variables config
	model_config = SettingsConfigDict(
		env_file='.env',
		env_file_encoding='utf-8',
		extra='ignore',
	)

	# Firefly III settings
	firefly_base_url: Optional[HttpUrl] = Field(default=None)
	firefly_token: Optional[str] = Field(default=None)

	# AuthKit settings (optional - if not provided, server runs without auth)
	authkit_domain: Optional[str] = Field(
		default=None, description='AuthKit domain URL (e.g., https://your-project.authkit.app)'
	)
	server_base_url: Optional[str] = Field(
		default=None, description="This server's base URL (e.g., https://api.yourcompany.com)"
	)

	@property
	def is_authkit_enabled(self) -> bool:
		"""Check if AuthKit is properly configured."""
		return all([self.authkit_domain, self.server_base_url])


# Initialize settings
settings = Settings()

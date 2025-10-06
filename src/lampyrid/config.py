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

	# Firefly III Configuration
	firefly_base_url: Optional[HttpUrl] = Field(default=None)
	firefly_token: Optional[str] = Field(default=None)

	# Google OAuth Configuration (Optional - for remote server authentication)
	google_client_id: Optional[str] = Field(default=None)
	google_client_secret: Optional[str] = Field(default=None)
	server_base_url: Optional[HttpUrl] = Field(default=None)


# Initialize settings
settings = Settings()

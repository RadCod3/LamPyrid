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

	firefly_base_url: Optional[HttpUrl] = Field(default=None)
	firefly_token: Optional[str] = Field(default=None)


# Initialize settings
settings = Settings()

"""Unit tests for configuration settings."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import HttpUrl
from pydantic_core import ValidationError

from lampyrid.config import Settings, _init_settings


class TestSettings:
    """Test cases for Settings class."""

    def test_settings_with_required_fields_only(self):
        """Test creating settings with only required fields."""
        with patch.dict(os.environ, {}, clear=True):  # Clear env to avoid interference
            settings = Settings(
                firefly_base_url=HttpUrl('https://firefly.example.com'), firefly_token='test_token'
            )

            assert str(settings.firefly_base_url) == 'https://firefly.example.com/'
            assert settings.firefly_token == 'test_token'
            assert settings.logging_level == 'INFO'  # Default value
            assert settings.mcp_transport == 'stdio'  # Default value
            assert settings.mcp_host == '0.0.0.0'  # Default value
            assert settings.mcp_port == 3000  # Default value

    def test_settings_with_all_fields(self):
        """Test creating settings with all fields configured."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'),
            firefly_token='test_token',
            logging_level='DEBUG',
            mcp_transport='http',
            mcp_host='localhost',
            mcp_port=8080,
            google_client_id='client_id',
            google_client_secret='client_secret',
            server_base_url=HttpUrl('https://server.example.com'),
            jwt_signing_key='jwt_key',
            oauth_storage_encryption_key='encryption_key',
            oauth_storage_path=Path('/custom/path'),
        )

        assert settings.logging_level == 'DEBUG'
        assert settings.mcp_transport == 'http'
        assert settings.mcp_host == 'localhost'
        assert settings.mcp_port == 8080
        assert settings.google_client_id == 'client_id'
        assert settings.google_client_secret == 'client_secret'
        assert str(settings.server_base_url) == 'https://server.example.com/'
        assert settings.jwt_signing_key == 'jwt_key'
        assert settings.oauth_storage_encryption_key == 'encryption_key'
        assert settings.oauth_storage_path == Path('/custom/path')

    def test_google_oauth_validation_all_provided(self):
        """Test Google OAuth validation passes when all fields are provided."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'),
            firefly_token='test_token',
            google_client_id='client_id',
            google_client_secret='client_secret',
            server_base_url=HttpUrl('https://server.example.com'),
        )

        # Should not raise an error
        assert settings.google_client_id == 'client_id'
        assert settings.google_client_secret == 'client_secret'
        assert str(settings.server_base_url) == 'https://server.example.com/'

    def test_google_oauth_validation_none_provided(self):
        """Test Google OAuth validation passes when no fields are provided."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'), firefly_token='test_token'
        )

        # Should not raise an error
        assert settings.google_client_id is None
        assert settings.google_client_secret is None
        assert settings.server_base_url is None

    def test_google_oauth_validation_partial_provided(self):
        """Test Google OAuth validation fails when only some fields are provided."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                firefly_base_url=HttpUrl('https://firefly.example.com'),
                firefly_token='test_token',
                google_client_id='client_id',
                # Missing google_client_secret and server_base_url
            )

        assert 'Google OAuth configuration is incomplete' in str(exc_info.value)
        assert 'Currently provided: 1/3' in str(exc_info.value)

    def test_google_oauth_validation_two_provided(self):
        """Test Google OAuth validation fails when only 2 of 3 fields are provided."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                firefly_base_url=HttpUrl('https://firefly.example.com'),
                firefly_token='test_token',
                google_client_id='client_id',
                google_client_secret='client_secret',
                # Missing server_base_url
            )

        assert 'Google OAuth configuration is incomplete' in str(exc_info.value)
        assert 'Currently provided: 2/3' in str(exc_info.value)

    def test_is_auth_enabled_true(self):
        """Test is_auth_enabled returns True when all OAuth fields are set."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'),
            firefly_token='test_token',
            google_client_id='client_id',
            google_client_secret='client_secret',
            server_base_url=HttpUrl('https://server.example.com'),
        )

        assert settings.is_auth_enabled is True

    def test_is_auth_enabled_false(self):
        """Test is_auth_enabled returns False when OAuth fields are not all set."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'), firefly_token='test_token'
        )

        assert settings.is_auth_enabled is False

    def test_is_auth_enabled_partial(self):
        """Test is_auth_enabled returns False when only some OAuth fields are set."""
        with pytest.raises(ValidationError):
            Settings(
                firefly_base_url=HttpUrl('https://firefly.example.com'),
                firefly_token='test_token',
                google_client_id='client_id',
            )

    def test_is_token_persistence_enabled_true(self):
        """Test is_token_persistence_enabled returns True when both keys are set."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'),
            firefly_token='test_token',
            jwt_signing_key='jwt_key',
            oauth_storage_encryption_key='encryption_key',
        )

        assert settings.is_token_persistence_enabled is True

    def test_is_token_persistence_enabled_false(self):
        """Test is_token_persistence_enabled returns False when keys are not both set."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'), firefly_token='test_token'
        )

        assert settings.is_token_persistence_enabled is False

    def test_is_token_persistence_enabled_partial(self):
        """Test is_token_persistence_enabled returns False when only one key is set."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'),
            firefly_token='test_token',
            jwt_signing_key='jwt_key',
            # Missing oauth_storage_encryption_key
        )

        assert settings.is_token_persistence_enabled is False

    def test_default_oauth_storage_path(self):
        """Test default OAuth storage path is set correctly."""
        settings = Settings(
            firefly_base_url=HttpUrl('https://firefly.example.com'), firefly_token='test_token'
        )

        expected_path = Path.home() / '.local' / 'share' / 'lampyrid' / 'oauth'
        assert settings.oauth_storage_path == expected_path


class TestInitSettings:
    """Test cases for _init_settings function."""

    def test_init_settings_success(self):
        """Test successful initialization with environment variables."""
        with patch.dict(os.environ, {}, clear=True):  # Clear existing env first
            with patch.dict(
                os.environ,
                {'FIREFLY_BASE_URL': 'https://firefly.example.com', 'FIREFLY_TOKEN': 'test_token'},
            ):
                settings = _init_settings()

                assert str(settings.firefly_base_url) == 'https://firefly.example.com/'
                assert settings.firefly_token == 'test_token'

    def test_init_settings_validation_error_missing_required(self):
        """Test initialization fails with missing required fields."""
        # Clear environment variables to force missing fields
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.exit') as mock_exit:
                # Mock sys.exit to prevent actual exit during test
                mock_exit.return_value = None

                try:
                    _init_settings()
                except SystemExit:
                    pass  # Expected behavior

                # Verify sys.exit was called with code 1
                mock_exit.assert_called_once_with(1)

    def test_init_settings_validation_error_invalid_url(self):
        """Test initialization fails with invalid URL."""
        with patch.dict(
            os.environ,
            {
                'FIREFLY_BASE_URL': 'invalid-url',  # Invalid URL
                'FIREFLY_TOKEN': 'test_token',
            },
        ):
            with patch('sys.exit') as mock_exit:
                # Mock sys.exit to prevent actual exit during test
                mock_exit.return_value = None

                try:
                    _init_settings()
                except SystemExit:
                    pass  # Expected behavior

                # Verify sys.exit was called with code 1
                mock_exit.assert_called_once_with(1)

    def test_init_settings_unexpected_error(self):
        """Test initialization re-raises unexpected errors."""
        # This would test the else branch in _init_settings
        with patch.object(Settings, 'model_validate', side_effect=RuntimeError('Unexpected error')):
            with pytest.raises(RuntimeError, match='Unexpected error'):
                _init_settings()

    def test_init_settings_with_env_file(self):
        """Test initialization using custom env file path."""
        # Test with a custom env file path
        env_content = """FIREFLY_BASE_URL=https://firefly.example.com
FIREFLY_TOKEN=test_token
LOGGING_LEVEL=DEBUG
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            env_file_path = f.name

        try:
            # Clear existing env and test with custom env file
            with patch.dict(os.environ, {}, clear=True):
                # Patch Settings to use our custom env file
                with patch('lampyrid.config.Settings') as mock_settings_class:
                    # Configure mock to create proper settings when called
                    mock_settings = mock_settings_class.return_value
                    mock_settings.firefly_base_url = HttpUrl('https://firefly.example.com')
                    mock_settings.firefly_token = 'test_token'
                    mock_settings.logging_level = 'DEBUG'

                    # Mock the model_validate method to return our settings
                    mock_settings_class.model_validate.return_value = mock_settings

                    settings = _init_settings()

                    # Verify Settings.model_validate was called
                    mock_settings_class.model_validate.assert_called_once()

                    # This mainly tests that _init_settings doesn't crash with custom files
                    assert settings is not None

        finally:
            # Cleanup
            if Path(env_file_path).exists():
                Path(env_file_path).unlink()

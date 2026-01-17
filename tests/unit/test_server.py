"""Unit tests for server initialization and configuration."""

from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from lampyrid.server import _create_auth_provider, _initialize_server


class TestServer:
    """Test cases for server initialization functions."""

    def test_create_auth_provider_no_auth(self):
        """Test _create_auth_provider returns None when auth is disabled."""
        with patch('lampyrid.server.settings') as mock_settings:
            mock_settings.is_auth_enabled = False

            result = _create_auth_provider()

            assert result is None

    def test_create_auth_provider_without_persistence(self):
        """Test _create_auth_provider creates GoogleProvider without persistence."""
        with patch('lampyrid.server.settings') as mock_settings:
            mock_settings.is_auth_enabled = True
            mock_settings.is_token_persistence_enabled = False
            mock_settings.google_client_id = 'test_client_id'
            mock_settings.google_client_secret = 'test_client_secret'
            mock_settings.server_base_url = 'https://example.com'
            mock_settings.jwt_signing_key = 'test_jwt_key'

            with patch('lampyrid.server.GoogleProvider') as mock_google_provider:
                mock_google_provider.return_value = MagicMock()

                result = _create_auth_provider()

                assert result is not None
                mock_google_provider.assert_called_once_with(
                    client_id='test_client_id',
                    client_secret='test_client_secret',
                    base_url='https://example.com',
                    required_scopes=[
                        'openid',
                        'https://www.googleapis.com/auth/userinfo.email',
                    ],
                    jwt_signing_key='test_jwt_key',
                    client_storage=None,
                )

    def test_create_auth_provider_with_persistence(self):
        """Test _create_auth_provider creates GoogleProvider with persistence."""
        with patch('lampyrid.server.settings') as mock_settings:
            mock_settings.is_auth_enabled = True
            mock_settings.is_token_persistence_enabled = True
            mock_settings.google_client_id = 'test_client_id'
            mock_settings.google_client_secret = 'test_client_secret'
            mock_settings.server_base_url = 'https://example.com'
            mock_settings.jwt_signing_key = 'test_jwt_key'
            mock_settings.oauth_storage_encryption_key = Fernet.generate_key().decode()
            mock_settings.oauth_storage_path = MagicMock()
            mock_settings.oauth_storage_path.mkdir = MagicMock()

            with (
                patch('lampyrid.server.GoogleProvider') as mock_google_provider,
                patch('lampyrid.server.DiskStore') as mock_disk_store,
                patch('lampyrid.server.FernetEncryptionWrapper') as mock_encryption_wrapper,
            ):
                mock_google_provider.return_value = MagicMock()
                mock_disk_store.return_value = MagicMock()
                mock_encryption_wrapper.return_value = MagicMock()

                result = _create_auth_provider()

                assert result is not None
                # Verify storage directory was created
                mock_settings.oauth_storage_path.mkdir.assert_called_once_with(
                    parents=True, exist_ok=True
                )
                # Verify disk store and encryption wrapper were initialized
                mock_disk_store.assert_called_once_with(directory=mock_settings.oauth_storage_path)
                mock_encryption_wrapper.assert_called_once()
                # Verify GoogleProvider was called with client_storage
                args, kwargs = mock_google_provider.call_args
                assert 'client_storage' in kwargs
                assert kwargs['client_storage'] is not None

    def test_initialize_server(self):
        """Test _initialize_server creates and configures FastMCP server."""
        with (
            patch('lampyrid.server.settings') as mock_settings,
            patch('lampyrid.server.FireflyClient') as mock_firefly_client,
            patch('lampyrid.server.compose_all_servers') as mock_compose_servers,
            patch('lampyrid.server.register_custom_routes') as mock_register_routes,
            patch('lampyrid.server.FastMCP') as mock_fastmcp,
            patch('lampyrid.server.configure_logging') as mock_configure_logging,
            patch('lampyrid.server.get_assets_path') as mock_get_assets_path,
            patch('lampyrid.server.asyncio.run') as mock_asyncio_run,
            patch('lampyrid.server._create_auth_provider') as mock_create_auth,
        ):
            # Mock settings
            mock_settings.logging_level = 'INFO'

            # Mock dependencies
            mock_settings.is_auth_enabled = False
            mock_create_auth.return_value = None
            mock_firefly_client.return_value = MagicMock()

            # Mock the Image object to avoid file operations
            with patch('lampyrid.server.Image') as mock_image:
                mock_icon = MagicMock()
                mock_icon.to_data_uri.return_value = 'data:image/png;base64,test'
                mock_image.return_value = mock_icon

                mock_get_assets_path.return_value = '/path/to/favicon.png'
                mock_fastmcp.return_value = MagicMock()

                # Call the function
                result = _initialize_server()

                # Verify auth provider was created
                mock_create_auth.assert_called_once()

                # Verify FastMCP was created with correct parameters
                mock_fastmcp.assert_called_once()
                fastmcp_args = mock_fastmcp.call_args
                assert fastmcp_args[0][0] == 'lampyrid'  # name
                assert fastmcp_args[1]['auth'] is None
                assert 'icons' in fastmcp_args[1]

                # Verify FireflyClient was created
                mock_firefly_client.assert_called_once()

                # Verify logging was configured
                mock_configure_logging.assert_called_once_with(level='INFO')

                # Verify servers were composed
                mock_asyncio_run.assert_called_once()
                mock_compose_servers.assert_called_once()

                # Verify custom routes were registered
                mock_register_routes.assert_called_once()

                # Verify the server instance was returned
                assert result is not None

    def test_initialize_server_with_auth(self):
        """Test _initialize_server with authentication enabled."""
        with (
            patch('lampyrid.server.settings') as mock_settings,
            patch('lampyrid.server.FireflyClient') as mock_firefly_client,
            patch('lampyrid.server.compose_all_servers'),
            patch('lampyrid.server.register_custom_routes'),
            patch('lampyrid.server.FastMCP') as mock_fastmcp,
            patch('lampyrid.server.configure_logging') as mock_configure_logging,
            patch('lampyrid.server.get_assets_path') as mock_get_assets_path,
            patch('lampyrid.server.asyncio.run'),
            patch('lampyrid.server._create_auth_provider') as mock_create_auth,
        ):
            # Mock settings with auth enabled
            mock_settings.logging_level = 'DEBUG'
            mock_settings.is_auth_enabled = True

            auth_provider = MagicMock()
            mock_create_auth.return_value = auth_provider
            mock_firefly_client.return_value = MagicMock()

            # Mock the Image object to avoid file operations
            with patch('lampyrid.server.Image') as mock_image:
                mock_icon = MagicMock()
                mock_icon.to_data_uri.return_value = 'data:image/png;base64,test'
                mock_image.return_value = mock_icon

                mock_get_assets_path.return_value = '/path/to/favicon.png'
                mock_fastmcp.return_value = MagicMock()

                # Call the function
                _initialize_server()

                # Verify FastMCP was created with auth provider
                mock_fastmcp.assert_called_once()
                args, kwargs = mock_fastmcp.call_args
                assert kwargs['auth'] is auth_provider

                # Verify logging was configured with correct level
                mock_configure_logging.assert_called_once_with(level='DEBUG')

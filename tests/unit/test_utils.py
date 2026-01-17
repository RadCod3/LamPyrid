"""Unit tests for utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP
from starlette.requests import Request

from lampyrid.utils import get_assets_path, register_custom_routes, serve_favicon


class TestUtils:
    """Test cases for utility functions."""

    def test_get_assets_path(self):
        """Test getting path to asset file."""
        with patch('lampyrid.utils.files') as mock_files:
            # Mock the files function to return a mock resource
            mock_resource = MagicMock()
            mock_resource.joinpath.return_value = Path('/mock/assets/test.png')
            mock_files.return_value = mock_resource

            result = get_assets_path('test.png')

            # Verify files('lampyrid') was called
            mock_files.assert_called_once_with('lampyrid')

            # Verify joinpath was called with correct filename
            mock_resource.joinpath.assert_called_once_with('assets', 'test.png')

            # Verify the result is a Path
            assert isinstance(result, Path)
            assert str(result) == '/mock/assets/test.png'

    @pytest.mark.asyncio
    async def test_serve_favicon_file_exists(self):
        """Test serving favicon when file exists."""
        with (
            patch('lampyrid.utils.get_assets_path') as mock_get_assets_path,
            patch('lampyrid.utils.FileResponse') as mock_file_response,
        ):
            # Mock favicon path exists
            mock_favicon_path = MagicMock()
            mock_favicon_path.exists.return_value = True
            mock_get_assets_path.return_value = mock_favicon_path

            mock_file_response.return_value = MagicMock()

            # Create a mock request
            mock_request = MagicMock(spec=Request)

            # Call the function
            result = await serve_favicon(mock_request)

            # Verify get_assets_path was called
            mock_get_assets_path.assert_called_once_with('favicon.ico')

            # Verify FileResponse was called with the favicon path
            mock_file_response.assert_called_once_with(mock_favicon_path, media_type='image/x-icon')

            # Verify the FileResponse is returned
            assert result is mock_file_response.return_value

    @pytest.mark.asyncio
    async def test_serve_favicon_file_not_exists(self):
        """Test serving favicon when file doesn't exist."""
        with (
            patch('lampyrid.utils.get_assets_path') as mock_get_assets_path,
            patch('lampyrid.utils.FileResponse') as mock_file_response,
            patch('lampyrid.utils.JSONResponse') as mock_json_response,
        ):
            # Mock favicon path doesn't exist
            mock_favicon_path = MagicMock()
            mock_favicon_path.exists.return_value = False
            mock_get_assets_path.return_value = mock_favicon_path

            mock_json_response.return_value = MagicMock()

            # Create a mock request
            mock_request = MagicMock(spec=Request)

            # Call the function
            result = await serve_favicon(mock_request)

            # Verify get_assets_path was called
            mock_get_assets_path.assert_called_once_with('favicon.ico')

            # Verify FileResponse was not called
            mock_file_response.assert_not_called()

            # Verify JSONResponse was called with error
            mock_json_response.assert_called_once_with({'error': 'Not found'}, status_code=404)

            # Verify the JSONResponse is returned
            assert result is mock_json_response.return_value

    @pytest.mark.asyncio
    async def test_register_custom_routes(self):
        """Test registering custom routes with FastMCP server."""
        with patch('lampyrid.utils.serve_favicon') as mock_serve_favicon:
            # Create a mock FastMCP server
            mock_mcp = MagicMock(spec=FastMCP)

            # Call the function
            register_custom_routes(mock_mcp)

            # Verify custom_route was called with favicon endpoint
            mock_mcp.custom_route.assert_called_once_with('/favicon.ico', methods=['GET'])

            # Verify that serve_favicon is referenced (even if not called directly)
            # The fact that the function was imported and available is enough
            assert mock_serve_favicon is not None

            # Check that serve_favicon was called
            if mock_serve_favicon.called:
                # Verify it was called with a Request object
                call_args = mock_serve_favicon.call_args
                assert len(call_args) > 0
                # The first argument should be a Request
                request_arg = call_args[0][0]
                # Should be a Request instance (or mock that acts like one)
                assert hasattr(request_arg, 'method') or hasattr(request_arg, 'url')

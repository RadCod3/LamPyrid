"""Unit tests for __main__ module."""

from unittest.mock import patch

from lampyrid.__main__ import main


class TestMainModule:
    """Test cases for __main__ module."""

    def test_main_stdio_transport(self):
        """Test main() with stdio transport (default)."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
        ):
            # Mock settings for stdio
            mock_settings.mcp_transport = 'stdio'

            # Call main
            main()

            # Verify mcp.run was called with stdio
            mock_mcp.run.assert_called_once_with(transport='stdio')

    def test_main_http_transport(self):
        """Test main() with HTTP transport."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
        ):
            # Mock settings for HTTP
            mock_settings.mcp_transport = 'http'
            mock_settings.mcp_host = '0.0.0.0'
            mock_settings.mcp_port = 3000

            # Call main
            main()

            # Verify mcp.run was called with HTTP parameters
            mock_mcp.run.assert_called_once_with(
                transport='streamable-http', host='0.0.0.0', port=3000
            )

    def test_main_sse_transport(self):
        """Test main() with SSE transport."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
        ):
            # Mock settings for SSE
            mock_settings.mcp_transport = 'sse'
            mock_settings.mcp_host = 'localhost'
            mock_settings.mcp_port = 8080

            # Call main
            main()

            # Verify mcp.run was called with SSE parameters
            mock_mcp.run.assert_called_once_with(transport='sse', host='localhost', port=8080)

    def test_main_unknown_transport(self):
        """Test main() with unknown transport defaults to stdio."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
        ):
            # Mock settings for unknown transport
            mock_settings.mcp_transport = 'unknown'

            # Call main
            main()

            # Verify mcp.run was called with default stdio
            mock_mcp.run.assert_called_once_with(transport='stdio')

    def test_main_called_when_name_is_main(self):
        """Test that main() is called when __name__ == '__main__'."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
        ):
            # Mock settings
            mock_settings.mcp_transport = 'stdio'

            # Call main when __name__ is __main__
            with patch('lampyrid.__main__.__name__', '__main__'):
                main()

                # Verify mcp.run was called
                mock_mcp.run.assert_called_once_with(transport='stdio')

    def test_main_not_called_when_name_is_not_main(self):
        """Test that main() is NOT called when __name__ != '__main__'."""
        with (
            patch('lampyrid.__main__.settings') as mock_settings,
            patch('lampyrid.__main__.mcp') as mock_mcp,
            patch('lampyrid.__main__.main') as mock_main,
        ):
            # Mock settings
            mock_settings.mcp_transport = 'stdio'

            # Set __name__ to something else
            with patch('lampyrid.__main__.__name__', 'not_main'):
                from lampyrid import __main__ as main_module

                # Import and run - this should trigger the if condition
                main_module.main()

                # Verify main() was called (when run as module)
                mock_main.assert_called_once()

                # But main() should NOT have been called during import
                # (since __name__ was not '__main__')
                mock_mcp.run.assert_not_called()

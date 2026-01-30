"""Unit tests for format script."""

from unittest.mock import patch

from lampyrid.scripts import format


class TestFormatScript:
    """Test cases for the format script."""

    @patch('subprocess.run')
    def test_main_return_code(self, mock_run):
        """Test that format.main returns correct code."""
        mock_run.return_value.returncode = 0

        ret_code = format.main()

        assert ret_code == 0
        assert mock_run.call_count == 2

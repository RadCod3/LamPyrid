"""Unit tests for maintenance scripts."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lampyrid.scripts import format, update_schema


class TestFormatScript:
    """Test cases for the format script."""

    @patch('subprocess.run')
    def test_main_success(self, mock_run):
        """Test that format.main runs ruff commands successfully."""
        mock_run.return_value.returncode = 0

        # Capture stdout to verify messages
        with patch('sys.stdout'):
            ret_code = format.main()

        assert ret_code == 0
        assert mock_run.call_count == 2

        # Verify calls use absolute path for cwd
        args, kwargs = mock_run.call_args_list[0]
        assert args[0] == ['ruff', 'format', '.']
        assert kwargs.get('check') is True
        assert isinstance(kwargs.get('cwd'), Path)
        assert kwargs.get('cwd').name == 'LamPyrid'

        args, kwargs = mock_run.call_args_list[1]
        assert args[0] == ['ruff', 'check', '--fix', '.']
        assert kwargs.get('check') is True
        assert isinstance(kwargs.get('cwd'), Path)

    @patch('subprocess.run')
    def test_main_formatting_error(self, mock_run):
        """Test that format.main handles subprocess errors."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, ['ruff'])

        with patch('sys.stdout'):
            ret_code = format.main()

        assert ret_code == 1

    @patch('subprocess.run')
    def test_main_formatting_error_at_second_step(self, mock_run):
        """Test that format.main handles subprocess errors at second step."""
        import subprocess

        mock_run.side_effect = [
            None,  # First step succeeds
            subprocess.CalledProcessError(1, ['ruff']),  # Second step fails
        ]

        with patch('sys.stdout'):
            ret_code = format.main()

        assert ret_code == 1
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_main_file_not_found(self, mock_run):
        """Test that format.main handles missing executable."""
        mock_run.side_effect = FileNotFoundError

        with patch('sys.stdout'):
            ret_code = format.main()

        assert ret_code == 1


class TestUpdateSchemaScript:
    """Test cases for the update_schema script."""

    def test_parse_versions_from_html(self):
        """Test version parsing logic."""
        html = """
        <a href="firefly-iii-6.4.16-v1.yaml">...</a>
        <a href="firefly-iii-6.4.14-v1.yaml">...</a>
        <a href="firefly-iii-develop-v1.yaml">...</a>
        """
        versions = update_schema.parse_versions_from_html(html)
        assert '6.4.16' in versions
        assert '6.4.14' in versions
        assert 'develop' not in versions
        assert len(versions) == 2

    def test_get_latest_stable_version(self):
        """Test version sorting logic."""
        versions = ['6.4.14', '6.4.16', '6.5.0']
        latest = update_schema.get_latest_stable_version(versions)
        assert latest == '6.5.0'

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_update_pyproject_toml_no_change(self, mock_write, mock_read):
        """Test that file is not written if content hasn't changed."""
        mock_read.return_value = 'input = "firefly-iii-6.4.16-v1.yaml"'

        result = update_schema.update_pyproject_toml('6.4.16', '6.4.16')

        assert result is False
        mock_write.assert_not_called()

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_update_pyproject_toml_with_change(self, mock_write, mock_read):
        """Test that file is updated when version changes."""
        mock_read.return_value = 'input = "firefly-iii-6.4.14-v1.yaml"'

        result = update_schema.update_pyproject_toml('6.4.14', '6.4.16')

        assert result is True
        mock_write.assert_called_once()
        content = mock_write.call_args[0][0]
        assert 'firefly-iii-6.4.16-v1.yaml' in content

    @patch('httpx.get')
    def test_download_schema(self, mock_get):
        """Test schema downloading."""
        mock_response = MagicMock()
        mock_response.content = b'schema content'
        mock_get.return_value = mock_response

        content = update_schema.download_schema('6.4.16')

        assert content == b'schema content'
        mock_get.assert_called_with(
            'https://api-docs.firefly-iii.org/firefly-iii-6.4.16-v1.yaml',
            timeout=30.0,
            follow_redirects=True,
        )

    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists')
    def test_cleanup_old_schema(self, mock_exists, mock_unlink):
        """Test cleanup of old schema files."""
        mock_exists.return_value = True

        result = update_schema.cleanup_old_schema('6.4.14', '6.4.16')

        assert result is True
        mock_unlink.assert_called_once()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_cleanup_old_schema_no_cleanup_needed(self, mock_unlink, mock_exists):
        """Test cleanup when old and new versions are the same."""
        result = update_schema.cleanup_old_schema('6.4.16', '6.4.16')

        assert result is False
        mock_exists.assert_not_called()
        mock_unlink.assert_not_called()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_cleanup_old_schema_no_old_version(self, mock_unlink, mock_exists):
        """Test cleanup when there's no old version."""
        result = update_schema.cleanup_old_schema(None, '6.4.16')

        assert result is False
        mock_exists.assert_not_called()
        mock_unlink.assert_not_called()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_cleanup_old_schema_file_not_exists(self, mock_unlink, mock_exists):
        """Test cleanup when old schema file doesn't exist."""
        mock_exists.return_value = False

        result = update_schema.cleanup_old_schema('6.4.14', '6.4.16')

        assert result is False
        mock_exists.assert_called_once()
        mock_unlink.assert_not_called()

    def test_parse_semver(self):
        """Test version parsing for semver comparison."""
        assert update_schema.parse_semver('6.4.16') == (6, 4, 16)
        assert update_schema.parse_semver('6.5.0') == (6, 5, 0)
        assert update_schema.parse_semver('10.0.1') == (10, 0, 1)

    @patch('pathlib.Path.exists')
    def test_get_current_schema_version_not_found(self, mock_exists):
        """Test get_current_schema_version when file doesn't exist."""
        mock_exists.return_value = False

        version = update_schema.get_current_schema_version()

        assert version is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_get_current_schema_version_no_match(self, mock_read, mock_exists):
        """Test get_current_schema_version when no schema reference found."""
        mock_exists.return_value = True
        mock_read.return_value = 'some other content without schema'

        version = update_schema.get_current_schema_version()

        assert version is None

    def test_get_latest_stable_version_empty_list(self):
        """Test get_latest_stable_version with empty list."""
        with pytest.raises(ValueError, match='No stable versions found'):
            update_schema.get_latest_stable_version([])

    def test_parse_versions_from_html_no_matches(self):
        """Test parse_versions_from_html with no matching versions."""
        html = '<a href="some-other-file.yaml">...</a>'

        versions = update_schema.parse_versions_from_html(html)

        assert len(versions) == 0

    def test_parse_versions_from_html_ignores_duplicates(self):
        """Test parse_versions_from_html ignores duplicate versions."""
        html = """
        <a href="firefly-iii-6.4.16-v1.yaml">...</a>
        <a href="firefly-iii-6.4.16-v1.yaml">...</a>
        <a href="firefly-iii-6.4.14-v1.yaml">...</a>
        """

        versions = update_schema.parse_versions_from_html(html)

        assert versions == ['6.4.16', '6.4.14']
        assert len(versions) == 2

    @patch('pathlib.Path.read_text')
    def test_get_current_schema_version_with_pyproject_toml(self, mock_read):
        """Test get_current_schema_version when pyproject.toml exists."""
        mock_read.return_value = 'some content input = "firefly-iii-6.4.16-v1.yaml" more content'

        version = update_schema.get_current_schema_version()

        assert version == '6.4.16'

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_update_pyproject_toml_regex_fallback(self, mock_write, mock_read):
        """Test update_pyproject_toml when direct string replacement fails."""
        mock_read.return_value = 'input = "firefly-iii-6.4.14-v1.yaml"'

        result = update_schema.get_current_schema_version()

        assert result == '6.4.14'

    @patch('subprocess.run')
    def test_regenerate_models_failure(self, mock_run):
        """Test regenerate_models when subprocess fails."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, 'datamodel-codegen', stderr='error')

        result = update_schema.regenerate_models()

        assert result is False

    # --- apply_manual_fixes -------------------------------------------------

    # Minimal stand-in for freshly generated firefly_models.py containing the
    # exact anchors apply_manual_fixes() patches.
    _GENERATED_STUB = (
        'from __future__ import annotations\n\n'
        'from typing import Any\n\n'
        'from pydantic import AnyUrl, AwareDatetime, BaseModel, EmailStr, Field, RootModel\n\n\n'
        'class ArrayEntryWithCurrencyAndSum(BaseModel):\n'
        "    currency_id: str | None = Field(None, examples=['5'])\n"
    )

    def _stub_models_file(self, tmp_path, monkeypatch, content):
        """Point update_schema at a temp models file containing ``content``."""
        models_path = tmp_path / 'firefly_models.py'
        models_path.write_text(content)
        monkeypatch.setattr(update_schema, 'PROJECT_ROOT', tmp_path)
        monkeypatch.setattr(update_schema, 'MODELS_OUTPUT', 'firefly_models.py')
        return models_path

    def test_apply_manual_fixes_patches_generated_file(self, tmp_path, monkeypatch):
        """Fresh generated content is patched with the int->str coercion."""
        models_path = self._stub_models_file(tmp_path, monkeypatch, self._GENERATED_STUB)

        assert update_schema.apply_manual_fixes() is True

        patched = models_path.read_text()
        assert '_coerce_to_str' in patched
        assert 'BeforeValidator' in patched
        assert 'Annotated[str | None, BeforeValidator(_coerce_to_str)]' in patched

    def test_apply_manual_fixes_is_idempotent(self, tmp_path, monkeypatch):
        """Already-patched content is left untouched and reported as no-op."""
        models_path = self._stub_models_file(tmp_path, monkeypatch, self._GENERATED_STUB)
        update_schema.apply_manual_fixes()
        patched = models_path.read_text()

        assert update_schema.apply_manual_fixes() is False
        assert models_path.read_text() == patched

    def test_apply_manual_fixes_missing_anchor_raises(self, tmp_path, monkeypatch):
        """A drifted generated file (anchor missing) fails loudly."""
        drifted = self._GENERATED_STUB.replace(
            'from typing import Any\n', 'from typing import List\n'
        )
        self._stub_models_file(tmp_path, monkeypatch, drifted)

        with pytest.raises(RuntimeError, match='anchor not found'):
            update_schema.apply_manual_fixes()

    def test_apply_manual_fixes_missing_file_raises(self, tmp_path, monkeypatch):
        """Missing models file fails loudly rather than silently skipping."""
        monkeypatch.setattr(update_schema, 'PROJECT_ROOT', tmp_path)
        monkeypatch.setattr(update_schema, 'MODELS_OUTPUT', 'does_not_exist.py')

        with pytest.raises(FileNotFoundError):
            update_schema.apply_manual_fixes()

    @patch('subprocess.run')
    def test_regenerate_models_applies_fixes(self, mock_run, tmp_path, monkeypatch):
        """regenerate_models patches the file after a successful codegen run."""
        mock_run.return_value = MagicMock(returncode=0)
        models_path = self._stub_models_file(tmp_path, monkeypatch, self._GENERATED_STUB)

        assert update_schema.regenerate_models() is True
        assert '_coerce_to_str' in models_path.read_text()

    @patch('subprocess.run')
    def test_regenerate_models_fails_loud_on_drift(self, mock_run, tmp_path, monkeypatch):
        """regenerate_models returns False if manual fixes cannot be applied."""
        mock_run.return_value = MagicMock(returncode=0)
        drifted = self._GENERATED_STUB.replace(
            'from typing import Any\n', 'from typing import List\n'
        )
        self._stub_models_file(tmp_path, monkeypatch, drifted)

        assert update_schema.regenerate_models() is False

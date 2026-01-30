#!/usr/bin/env python3
"""Download the latest Firefly III API schema and regenerate Pydantic models.

This script:
1. Fetches available versions from api-docs.firefly-iii.org
2. Identifies the latest stable version (excludes develop/beta)
3. Downloads the OpenAPI YAML schema
4. Updates pyproject.toml with the new schema path
5. Regenerates Pydantic models using datamodel-codegen
6. Cleans up the old schema file

Usage:
    uv run python scripts/update_schema.py
"""

import re
import subprocess
import sys
from pathlib import Path

import httpx

# Constants
API_DOCS_URL = 'https://api-docs.firefly-iii.org/'
SCHEMA_BASE_URL = 'https://api-docs.firefly-iii.org/'
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / 'pyproject.toml'
MODELS_OUTPUT = 'src/lampyrid/models/firefly_models.py'


def parse_versions_from_html(html: str) -> list[str]:
    """Extract available schema versions from the swagger UI HTML.

    Args:
        html: HTML content from the API docs page

    Returns:
        List of version strings (e.g., ['6.4.16', '6.4.14', ...])

    """
    # Match patterns like: firefly-iii-6.4.16-v1.yaml
    # The HTML may have escaped slashes (\/) or regular format
    pattern = r'firefly-iii-([0-9][^"\'>\s]*)-v1\.yaml'
    matches = re.findall(pattern, html)

    # Filter out develop and beta versions for stable release
    stable_versions = []
    seen = set()
    for version in matches:
        if 'develop' in version or 'beta' in version:
            continue
        if version not in seen:
            seen.add(version)
            stable_versions.append(version)

    return stable_versions


def parse_semver(version: str) -> tuple[int, ...]:
    """Parse a version string into a tuple for comparison.

    Args:
        version: Version string like '6.4.16' or '6.4.14'

    Returns:
        Tuple of integers for comparison (e.g., (6, 4, 16))

    """
    # Extract numeric parts
    parts = re.findall(r'\d+', version)
    return tuple(int(p) for p in parts)


def get_latest_stable_version(versions: list[str]) -> str:
    """Find the latest stable version from a list of versions.

    Args:
        versions: List of version strings

    Returns:
        The latest stable version string

    """
    if not versions:
        raise ValueError('No stable versions found')

    # Sort by semver, descending
    sorted_versions = sorted(versions, key=parse_semver, reverse=True)
    return sorted_versions[0]


def get_current_schema_version() -> str | None:
    """Get the current schema version from pyproject.toml.

    Returns:
        Current version string or None if not found

    """
    if not PYPROJECT_PATH.exists():
        return None

    content = PYPROJECT_PATH.read_text()

    # Match: input = "firefly-iii-6.4.14-v1.yaml"
    match = re.search(r'input\s*=\s*"firefly-iii-([^"]+)-v1\.yaml"', content)
    if match:
        return match.group(1)

    return None


def download_schema(version: str) -> bytes:
    """Download the OpenAPI schema for a specific version.

    Args:
        version: Version string (e.g., '6.4.16')

    Returns:
        Schema content as bytes

    """
    url = f'{SCHEMA_BASE_URL}firefly-iii-{version}-v1.yaml'
    response = httpx.get(url, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    return response.content


def update_pyproject_toml(old_version: str | None, new_version: str) -> bool:
    """Update the schema path in pyproject.toml.

    Args:
        old_version: Previous version string (or None)
        new_version: New version string

    Returns:
        True if the file was updated, False otherwise

    """
    content = PYPROJECT_PATH.read_text()
    original_content = content

    old_filename = f'firefly-iii-{old_version}-v1.yaml' if old_version else None
    new_filename = f'firefly-iii-{new_version}-v1.yaml'

    if old_filename and old_filename in content:
        content = content.replace(old_filename, new_filename)
    else:
        # If no existing entry, try to update any firefly schema reference
        content = re.sub(
            r'input\s*=\s*"firefly-iii-[^"]*\.yaml"',
            f'input = "{new_filename}"',
            content,
        )

    if content != original_content:
        PYPROJECT_PATH.write_text(content)
        return True

    return False


def regenerate_models() -> bool:
    """Run datamodel-codegen to regenerate Pydantic models.

    Returns:
        True if successful, False otherwise

    """
    try:
        subprocess.run(
            ['uv', 'run', 'datamodel-codegen'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f'   Error running datamodel-codegen: {e.stderr}')
        return False


def cleanup_old_schema(old_version: str | None, new_version: str) -> bool:
    """Remove the old schema file if it exists and differs from new.

    Args:
        old_version: Previous version string (or None)
        new_version: New version string

    Returns:
        True if a file was removed, False otherwise

    """
    if not old_version or old_version == new_version:
        return False

    old_path = PROJECT_ROOT / f'firefly-iii-{old_version}-v1.yaml'
    if old_path.exists():
        old_path.unlink()
        return True

    return False


def main() -> int:
    """Run the schema update process.

    Returns:
        Exit code (0 for success, 1 for error)

    """
    print('=== Firefly III Schema Updater ===\n')

    # Step 1: Fetch available versions
    print('Fetching available versions from api-docs.firefly-iii.org...')
    try:
        response = httpx.get(API_DOCS_URL, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f'Error fetching API docs page: {e}')
        return 1

    versions = parse_versions_from_html(response.text)
    if not versions:
        print('Error: Could not find any schema versions')
        return 1

    latest_version = get_latest_stable_version(versions)
    print(f'Found {len(versions)} stable versions, latest: {latest_version}\n')

    # Step 2: Check current version
    current_version = get_current_schema_version()
    current_display = current_version or '(none)'

    print(f'Current schema: firefly-iii-{current_display}-v1.yaml')
    print(f'Latest schema:  firefly-iii-{latest_version}-v1.yaml\n')

    # Step 3: Check if update is needed
    if current_version == latest_version:
        print('Already up to date!')
        return 0

    # Step 4: Download new schema
    print(f'Downloading firefly-iii-{latest_version}-v1.yaml...')
    try:
        schema_content = download_schema(latest_version)
    except httpx.HTTPError as e:
        print(f'Error downloading schema: {e}')
        return 1

    schema_path = PROJECT_ROOT / f'firefly-iii-{latest_version}-v1.yaml'
    schema_path.write_bytes(schema_content)
    size_kb = len(schema_content) / 1024
    print(f'Schema downloaded ({size_kb:.0f}KB)')

    # Step 5: Update pyproject.toml
    print('\nUpdating pyproject.toml...')
    if update_pyproject_toml(current_version, latest_version):
        print('Updated [tool.datamodel-codegen] input')
    else:
        print('No changes needed in pyproject.toml')

    # Step 6: Regenerate models
    print('\nRegenerating Pydantic models...')
    if regenerate_models():
        print(f'Models regenerated at {MODELS_OUTPUT}')

        # Format the generated code
        print('Formatting generated code...')
        try:
            subprocess.run(
                ['uv', 'run', 'ruff', 'format', MODELS_OUTPUT],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
            )
            print('Code formatted successfully')
        except subprocess.CalledProcessError as e:
            print(f'Warning: Formatting failed: {e}')
    else:
        print('Warning: Model regeneration failed')
        print('You may need to run manually: uv run datamodel-codegen')

    # Step 7: Cleanup old schema
    if current_version:
        print('\nCleaning up old schema...')
        if cleanup_old_schema(current_version, latest_version):
            print(f'Removed firefly-iii-{current_version}-v1.yaml')
        else:
            print('No cleanup needed')

    # Summary
    print('\n=== Update Complete ===')
    if current_version:
        print(f'Schema updated from {current_version} to {latest_version}')
    else:
        print(f'Schema set to {latest_version}')

    return 0


if __name__ == '__main__':
    sys.exit(main())

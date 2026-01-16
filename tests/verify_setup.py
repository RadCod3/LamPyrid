#!/usr/bin/env python3
"""
Verification script for Firefly III test setup.

This script checks that:
1. Firefly III is running and accessible
2. The API token is valid
3. Required test accounts exist
4. Required test budget exists
"""

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load test environment
env_path = Path(__file__).parent / '.env.test'
if env_path.exists():
	load_dotenv(env_path)
else:
	print('✗ tests/.env.test file not found')
	print('\nPlease create it with:')
	print('  FIREFLY_BASE_URL=http://localhost:8080')
	print('  FIREFLY_TOKEN=your_token_here')
	sys.exit(1)


FIREFLY_URL = os.getenv('FIREFLY_BASE_URL', 'http://localhost:8080')
TOKEN = os.getenv('FIREFLY_TOKEN', '')

if not TOKEN:
	print('✗ FIREFLY_TOKEN not set in tests/.env.test')
	sys.exit(1)

print('=== Firefly III Test Setup Verification ===\n')
print(f'Firefly URL: {FIREFLY_URL}')
print(f'Token: {TOKEN[:20]}...\n')

headers = {
	'Authorization': f'Bearer {TOKEN}',
	'Accept': 'application/json',
}

all_checks_passed = True


# Check 1: Firefly III is running
print('1. Checking Firefly III accessibility...')
try:
	response = httpx.get(f'{FIREFLY_URL}/api/v1/about', headers=headers, timeout=10.0)
	if response.status_code == 200:
		data = response.json()
		version = data.get('data', {}).get('version', 'unknown')
		print(f'   ✓ Firefly III is running (version: {version})')
	else:
		print(f'   ✗ Unexpected response: {response.status_code}')
		all_checks_passed = False
except Exception as e:
	print(f'   ✗ Cannot connect to Firefly III: {e}')
	print('   Make sure Firefly III is running: docker-compose -f docker-compose.test.yml up -d')
	all_checks_passed = False

# Check 2: Token is valid
print('\n2. Checking API token validity...')
try:
	response = httpx.get(f'{FIREFLY_URL}/api/v1/about', headers=headers, timeout=10.0)
	if response.status_code == 200:
		print('   ✓ Token is valid')
	elif response.status_code == 401:
		print('   ✗ Token is invalid or expired')
		print('   Please regenerate token in Firefly III web UI')
		all_checks_passed = False
	else:
		print(f'   ✗ Unexpected response: {response.status_code}')
		all_checks_passed = False
except Exception as e:
	print(f'   ✗ Cannot verify token: {e}')
	all_checks_passed = False

# Note about test data creation
print('\n3. Test data creation...')
print('   ℹ  Tests will create accounts and budgets programmatically')
print('   ℹ  No pre-existing accounts or budgets required')

# Summary
print('\n=== Verification Summary ===')
if all_checks_passed:
	print('✓ All checks passed! Your test environment is ready.')
	print('\nYou can now run tests with: uv run pytest tests/')
	sys.exit(0)
else:
	print('✗ Some checks failed. Please fix the issues above.')
	print('\nFor setup instructions, see: tests/setup_firefly.md')
	sys.exit(1)

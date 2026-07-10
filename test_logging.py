#!/usr/bin/env python
"""
Test script to verify logging is working across all modules.
Run this from the Django shell or as a standalone test.
"""

import logging
import os
import sys

import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_p.settings')
django.setup()

# Import all modules to trigger logging initialization
from django.conf import settings


# Get all configured loggers
def test_logging():
    """Test logging functionality across all modules"""
    print("\n" + "=" * 60)
    print("LOGGING CONFIGURATION TEST")
    print("=" * 60 + "\n")

    # Get logging configuration
    logging_config = settings.LOGGING

    print(f"Logging version: {logging_config.get('version')}")
    print(f"Disable existing loggers: {logging_config.get('disable_existing_loggers')}")

    print("\n📋 CONFIGURED HANDLERS:")
    print("-" * 60)
    for handler_name, handler_config in logging_config.get('handlers', {}).items():
        print(f"  ✓ {handler_name}: {handler_config.get('class', 'N/A')}")
        if 'filename' in handler_config:
            print(f"    File: {handler_config['filename']}")

    print("\n📋 CONFIGURED LOGGERS:")
    print("-" * 60)
    for logger_name, logger_config in logging_config.get('loggers', {}).items():
        handlers = logger_config.get('handlers', [])
        level = logger_config.get('level', 'N/A')
        print(f"  ✓ {logger_name}")
        print(f"    Level: {level}")
        print(f"    Handlers: {', '.join(handlers)}")

    # Test logging from all modules
    print("\n📝 TESTING LOGGING FROM MODULES:")
    print("-" * 60)

    test_loggers = {
        'accounts': 'accounts.models',
        'accounts.auth': 'accounts.auth.services',
        'accounts.core': 'accounts.core.jwt_utils',
        'finances': 'finances.models',
        'groupes': 'groupes.models',
        'membres': 'membres.models',
        'evenements': 'evenements.models',
        'librairie': 'librairie.models',
    }

    results = []

    for logger_name, module_path in test_loggers.items():
        try:
            logger = logging.getLogger(logger_name)

            # Test different log levels
            logger.debug(f"DEBUG test from {logger_name}")
            logger.info(f"INFO test from {logger_name}")
            logger.warning(f"WARNING test from {logger_name}")
            logger.error(f"ERROR test from {logger_name}")

            results.append((logger_name, "✓ PASS"))
            print(f"  ✓ {logger_name:<30} - Logging works")
        except Exception as e:
            results.append((logger_name, f"✗ FAIL: {str(e)}"))
            print(f"  ✗ {logger_name:<30} - {str(e)}")

    # Check log files exist
    print("\n📂 LOG FILES:")
    print("-" * 60)
    log_dir = os.path.join(settings.BASE_DIR, 'logs')

    if os.path.exists(log_dir):
        print(f"  ✓ Log directory exists: {log_dir}")
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            size = os.path.getsize(filepath)
            print(f"    - {filename}: {size} bytes")
    else:
        print(f"  ✗ Log directory does not exist: {log_dir}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if "✓" in result)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All logging tests passed!")
        return True
    else:
        print(f"\n⚠️  Some tests failed")
        return False


if __name__ == '__main__':
    success = test_logging()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webassist.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

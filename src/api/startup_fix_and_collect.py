"""Helper script to run ADT utils Data Fixer in an isolated subprocess.

This avoids import path collisions with the main app's `src` package by
inserting the ADT utils root into sys.path before importing.

Usage:
    python src/api/startup_fix_and_collect.py <target_output_dir> <adt_utils_dir>

Prints a JSON object to stdout with keys: success (bool) and metadata (dict).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    """Entry point for the fixer runner.

    Returns a JSON payload on stdout so the parent process can parse results.
    """
    if len(sys.argv) < 3:
        sys.stdout.write(json.dumps({"success": False, "error": "missing arguments"}))
        return 2

    target_dir = Path(sys.argv[1])
    adt_utils_dir = Path(sys.argv[2])

    # Ensure ADT utils package is importable first to avoid name collisions
    sys.path.insert(0, str(adt_utils_dir))

    try:
        from src.core import PageProcessConfig  # type: ignore
        from src.validation.classes import ADTDataFixer  # type: ignore
    except Exception as e:  # pragma: no cover - depends on runtime env
        sys.stdout.write(json.dumps({"success": False, "error": f"import_error: {e}"}))
        return 1

    try:
        fix_config = PageProcessConfig(
            start_page=-1,
            end_page=-1,
            target_dir=target_dir,
        )
        fixer = ADTDataFixer()
        result = fixer.process_page_range(fix_config, dry_run=False, auto_format=False)
        sys.stdout.write(json.dumps({"success": result.success, "metadata": result.metadata}))
        return 0
    except Exception as e:  # pragma: no cover - external deps
        sys.stdout.write(json.dumps({"success": False, "error": f"fix_error: {e}"}))
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

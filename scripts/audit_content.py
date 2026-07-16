"""Audit core pages — delegates to validate_content.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    script = ROOT / "scripts" / "validate_content.py"
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

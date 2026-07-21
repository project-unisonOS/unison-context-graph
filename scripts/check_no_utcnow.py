#!/usr/bin/env python3
"""Reject deprecated naive UTC construction in production Python sources."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    offenders = [
        path.relative_to(ROOT)
        for path in (ROOT / "src").rglob("*.py")
        if "datetime.utcnow" in path.read_text(encoding="utf-8")
    ]
    if offenders:
        names = ", ".join(str(path) for path in offenders)
        raise SystemExit(f"naive datetime.utcnow remains in: {names}")
    print("[PASS] Production sources use timezone-aware UTC construction.")


if __name__ == "__main__":
    main()

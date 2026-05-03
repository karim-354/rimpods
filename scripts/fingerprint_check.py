"""CLI wrapper untuk fingerprint_check. Jalankan: python scripts/fingerprint_check.py <file.txt>"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from fingerprint_check import verify_before_publish  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fingerprint_check.py <input.txt> [--no-fix]")
        sys.exit(1)
    auto_fix = "--no-fix" not in sys.argv
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()
    result = verify_before_publish(text, auto_fix=auto_fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("publish_allowed") else 2)

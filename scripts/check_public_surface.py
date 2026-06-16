from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "build", "dist", "out"}
REQUIRED = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    ".gitignore",
    ".dockerignore",
    ".env.example",
    "project-docs/public-boundary.md",
]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".txt", ".yml", ".yaml", ".json", ".jsonl", ".example"}
BANNED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        "warden" + r"-ops",
        "real" + r" client data",
        "internal" + r" private runbook",
        "AKIA[0-9A-Z]{16}",
        "OPENAI_API_KEY" + r"\s*=",
        "ANTHROPIC_API_KEY" + r"\s*=",
    ]
]


def main() -> int:
    failures: list[str] = []
    for required in REQUIRED:
        if not (ROOT / required).exists():
            failures.append(f"missing required file: {required}")
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            failures.append(f"committed environment file is not allowed: {rel}")
        if path.suffix not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in BANNED_PATTERNS:
            if pattern.search(text):
                failures.append(f"{rel}: banned public-surface pattern {pattern.pattern!r}")
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

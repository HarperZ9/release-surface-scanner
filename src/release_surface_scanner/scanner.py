"""Repository release scanner."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import FileRecord, Finding, FindingLevel, ReleaseReport


REQUIRED_FILES = ("README.md", "LICENSE", "pyproject.toml", ".gitignore")
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "build", "dist", "out", "node_modules"}
TEXT_SUFFIXES = {".md", ".py", ".toml", ".txt", ".yml", ".yaml", ".json", ".jsonl", ".cfg", ".ini"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{32,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api|secret|token|password)_?key\s*=\s*['\"]?[^'\"\s]{16,}"),
    # GitHub fine-grained PAT (check before the gh*_ shape; "github" != "gh[opsru]")
    re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),
    # GitHub classic / oauth / server / refresh / user-to-server tokens
    re.compile(r"gh[opsru]_[A-Za-z0-9]{36}"),
    # JSON Web Token (header.payload.signature, both first segments base64 of `{"...`)
    re.compile(r"eyJ[A-Za-z0-9_=-]+\.eyJ[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+"),
    # PEM private-key block header (RSA/EC/DSA/OPENSSH/PGP/generic)
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    # Slack token (bot/user/app/refresh/legacy)
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    # Google API key
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
)


def _is_env_file(path: Path) -> bool:
    return path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example")


def _should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    return _is_env_file(path) or any(part in SKIP_DIRS for part in rel.parts)


def _kind(path: Path) -> str:
    if path.name in REQUIRED_FILES:
        return "required-file"
    if path.parts and "tests" in path.parts:
        return "test"
    if path.suffix in {".md", ".txt"}:
        return "doc"
    if path.suffix == ".py":
        return "source"
    return "artifact"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _detect_secret_shapes(path: Path, text: str) -> list[Finding]:
    findings = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    level=FindingLevel.FAIL,
                    code="secret-shaped-text",
                    path=path.as_posix(),
                    summary=f"secret-shaped value detected at line {line}",
                )
            )
    return findings


def scan_repo(root: str | Path) -> ReleaseReport:
    root_path = Path(root).resolve()
    findings: list[Finding] = []
    records: list[FileRecord] = []
    excluded: list[str] = []

    for required in REQUIRED_FILES:
        if not (root_path / required).exists():
            findings.append(
                Finding(
                    level=FindingLevel.FAIL,
                    code="missing-required-file",
                    path=required,
                    summary=f"missing required file: {required}",
                )
            )

    for path in sorted(p for p in root_path.rglob("*") if p.is_file()):
        rel = path.relative_to(root_path).as_posix()
        if _should_skip(path, root_path):
            excluded.append(rel)
            continue
        data = path.read_bytes()
        records.append(FileRecord(path=rel, sha256=_sha(data), bytes=len(data), kind=_kind(path)))
        if path.suffix in TEXT_SUFFIXES or path.name in REQUIRED_FILES or path.name == ".gitignore":
            text = data.decode("utf-8", errors="ignore")
            findings.extend(_detect_secret_shapes(Path(rel), text))

    repo_hash = _sha("".join(f"{r.path}:{r.sha256};" for r in records).encode("utf-8"))
    fail_count = sum(1 for finding in findings if finding.level == FindingLevel.FAIL)
    status = "fail" if fail_count else "pass"
    secret_count = sum(1 for finding in findings if finding.code == "secret-shaped-text")
    return ReleaseReport(
        root=str(root_path),
        status=status,
        repo_hash=repo_hash,
        file_count=len(records),
        secret_shape_count=secret_count,
        files=tuple(records),
        excluded_paths=tuple(sorted(excluded)),
        findings=tuple(findings),
    )

"""Release assurance models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FindingLevel(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class Finding:
    level: FindingLevel
    code: str
    path: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "code": self.code,
            "path": self.path,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class FileRecord:
    path: str
    sha256: str
    bytes: int
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class ReleaseReport:
    root: str
    status: str
    repo_hash: str
    file_count: int
    secret_shape_count: int
    files: tuple[FileRecord, ...] = ()
    excluded_paths: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    schema: str = "release-surface-scanner.report.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "root": self.root,
            "status": self.status,
            "repo_hash": self.repo_hash,
            "file_count": self.file_count,
            "secret_shape_count": self.secret_shape_count,
            "excluded_paths": list(self.excluded_paths),
            "files": [record.to_dict() for record in self.files],
            "findings": [finding.to_dict() for finding in self.findings],
        }

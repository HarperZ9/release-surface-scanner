"""Proof-index generation."""
from __future__ import annotations

from .models import ReleaseReport


def build_proof_index(report: ReleaseReport) -> dict[str, object]:
    evidence = [
        {
            "kind": record.kind,
            "path": record.path,
            "sha256": record.sha256,
            "bytes": record.bytes,
        }
        for record in report.files
        if record.kind in {"required-file", "test", "doc"}
    ]
    return {
        "schema": "warden-release-assurance.proof-index.v1",
        "status": report.status,
        "repo_hash": report.repo_hash,
        "evidence": evidence,
        "finding_count": len(report.findings),
    }

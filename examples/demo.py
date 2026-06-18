"""Best-effort demo - not runtime-verified by author.

End-to-end walkthrough of the Release Surface Scanner public API using only
documented functions: scan_repo, build_proof_index, and the reporting helpers.

It scans the repository's bundled synthetic fixture (fixtures/sample_repo),
prints the report summary, writes a JSON + Markdown release report and a proof
index to an output directory, and exits non-zero if the surface does not pass
(mirroring the CLI's --fail-on-fail behavior).

Run from the repository root:

    python examples/demo.py

If the package is not installed, add the source tree to PYTHONPATH first:

    # PowerShell
    $env:PYTHONPATH = "src"; python examples/demo.py
"""
from __future__ import annotations

from pathlib import Path

from release_surface_scanner import (
    __version__,
    build_proof_index,
    scan_repo,
)
from release_surface_scanner.reporting import write_json, write_markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "fixtures" / "sample_repo"
OUT_DIR = REPO_ROOT / "out"


def main() -> int:
    print(f"release-surface-scanner {__version__}")
    print(f"scanning: {TARGET}")

    report = scan_repo(TARGET)

    print(
        f"status={report.status} "
        f"files={report.file_count} "
        f"findings={len(report.findings)} "
        f"secret_shapes={report.secret_shape_count}"
    )
    print(f"repo_hash={report.repo_hash}")

    for finding in report.findings:
        # Summaries never contain the matched secret value, only a location.
        print(f"  - [{finding.level.value}] {finding.code} {finding.path}: {finding.summary}")

    # Persist the same artifacts the CLI produces.
    json_out = OUT_DIR / "release-report.json"
    md_out = OUT_DIR / "release-report.md"
    proof_out = OUT_DIR / "proof-index.json"

    write_json(report.to_dict(), json_out)
    write_markdown(report, md_out)
    write_json(build_proof_index(report), proof_out)

    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    print(f"wrote {proof_out}")

    # Mirror `release-scan scan ... --fail-on-fail`.
    return 1 if report.status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""JSON and Markdown report output."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ReleaseReport


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: ReleaseReport) -> str:
    lines = [
        "# Release Surface Scanner",
        "",
        f"- Status: `{report.status}`",
        f"- Files included: {report.file_count}",
        f"- Excluded paths: {len(report.excluded_paths)}",
        f"- Secret-shaped findings: {report.secret_shape_count}",
        f"- Repository hash: `{report.repo_hash}`",
        "",
    ]
    if report.findings:
        lines.append("## Findings")
        lines.append("")
        for finding in report.findings:
            lines.append(f"- `{finding.level.value}` `{finding.code}` `{finding.path}`: {finding.summary}")
    else:
        lines.append("No release-blocking findings.")
    return "\n".join(lines) + "\n"


def write_markdown(report: ReleaseReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")

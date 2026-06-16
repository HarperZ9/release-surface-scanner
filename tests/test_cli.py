from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    return repo


def test_cli_scan_writes_json_and_markdown(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    json_out = tmp_path / "release-report.json"
    md_out = tmp_path / "release-report.md"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "warden_release_assurance",
            "scan",
            str(repo),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
            "--fail-on-fail",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(json_out.read_text(encoding="utf-8"))["status"] == "pass"
    assert "WARDEN Release Assurance" in md_out.read_text(encoding="utf-8")


def test_cli_proof_index_writes_json(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    out = tmp_path / "proof-index.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "warden_release_assurance",
            "proof-index",
            str(repo),
            "--json-out",
            str(out),
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["schema"].endswith(".v1")

from __future__ import annotations

import json
from pathlib import Path

from warden_release_assurance import FindingLevel, scan_repo


def _sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n\nA public release candidate.\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".env\n.env.*\ndist/\n", encoding="utf-8")
    env_key = "OPENAI" + "_API_KEY"
    (repo / ".env").write_text(f"{env_key}=should_not_be_read\n", encoding="utf-8")
    src = repo / "src"
    src.mkdir()
    (src / "demo.py").write_text("print('ok')\n", encoding="utf-8")
    return repo


def test_scan_repo_passes_clean_surface_and_excludes_env(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)

    report = scan_repo(repo)

    assert report.root == str(repo)
    assert report.status == "pass"
    assert report.file_count >= 4
    assert report.secret_shape_count == 0
    assert ".env" in report.excluded_paths
    assert all("should_not_be_read" not in finding.summary for finding in report.findings)


def test_scan_repo_flags_missing_required_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")

    report = scan_repo(repo)

    assert report.status == "fail"
    assert any(f.level == FindingLevel.FAIL for f in report.findings)
    assert any("missing required file" in f.summary for f in report.findings)


def test_scan_repo_flags_secret_shaped_text_without_leaking_value(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    (repo / "README.md").write_text(
        "token = sk-" + "x" * 48 + "\n",
        encoding="utf-8",
    )

    report = scan_repo(repo)
    payload = json.dumps(report.to_dict(), sort_keys=True)

    assert report.status == "fail"
    assert report.secret_shape_count == 1
    assert "sk-" + "x" * 48 not in payload
    assert "secret-shaped value" in payload


def test_report_hashes_are_stable(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)

    first = scan_repo(repo).to_dict()
    second = scan_repo(repo).to_dict()

    assert first["repo_hash"] == second["repo_hash"]
    assert first["files"][0]["sha256"] == second["files"][0]["sha256"]

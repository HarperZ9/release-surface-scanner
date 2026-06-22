from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_surface_scanner import FindingLevel, scan_repo


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


# Each value is a *shape* of a published secret the gate must catch. The values
# are syntactically valid but non-functional (no real credential). The gate is a
# pre-publish safety net; missing any of these lets a real secret ship.
_SECRET_SHAPES = {
    "github_pat_classic": "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "github_pat_oauth": "gho_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "github_pat_fine_grained": "github_pat_" + "11ABCDEFG0" + "a" * 22 + "_" + "b" * 20,
    "jwt": (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkRlbW8ifQ"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    ),
    # Split like the others so this source file never contains a matchable shape.
    "pem_rsa_private_key": "-----BEGIN RSA " + "PRIVATE KEY-----",
    "pem_openssh_private_key": "-----BEGIN OPENSSH " + "PRIVATE KEY-----",
    "slack_token": "xoxb-" + "1234567890" + "-" + "0987654321" + "-" + "a" * 24,
    "google_api_key": "AIza" + "Sy" + "A" * 33,
}


@pytest.mark.parametrize("name, secret", sorted(_SECRET_SHAPES.items()))
def test_scan_flags_published_secret_shapes_without_leaking_value(
    tmp_path: Path, name: str, secret: str
) -> None:
    repo = _sample_repo(tmp_path)
    # Bare value on its own line, so the generic `*_key=` pattern can't be the
    # one that catches it - this isolates the new shape-specific detection.
    (repo / "README.md").write_text(f"deploy with:\n{secret}\n", encoding="utf-8")

    report = scan_repo(repo)
    payload = json.dumps(report.to_dict(), sort_keys=True)

    assert report.status == "fail", f"{name} not flagged"
    assert report.secret_shape_count >= 1, f"{name} produced no secret finding"
    assert secret not in payload, f"{name} leaked its value into the report"
    assert "secret-shaped value" in payload


def test_report_hashes_are_stable(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)

    first = scan_repo(repo).to_dict()
    second = scan_repo(repo).to_dict()

    assert first["repo_hash"] == second["repo_hash"]
    assert first["files"][0]["sha256"] == second["files"][0]["sha256"]

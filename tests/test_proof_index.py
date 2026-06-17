from __future__ import annotations

from pathlib import Path

from release_surface_scanner import build_proof_index, scan_repo


def test_build_proof_index_groups_release_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_demo.py").write_text("def test_demo():\n    assert True\n", encoding="utf-8")

    report = scan_repo(repo)
    index = build_proof_index(report)

    assert index["schema"] == "release-surface-scanner.proof-index.v1"
    assert index["status"] == "pass"
    assert any(item["kind"] == "required-file" for item in index["evidence"])
    assert any(item["kind"] == "test" for item in index["evidence"])

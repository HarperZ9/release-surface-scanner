"""CLI for Release Surface Scanner."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .proof import build_proof_index
from .reporting import write_json, write_markdown
from .scanner import scan_repo


def _cmd_scan(args: argparse.Namespace) -> int:
    report = scan_repo(args.repo)
    write_json(report.to_dict(), args.json_out)
    if args.md_out is not None:
        write_markdown(report, args.md_out)
    print(f"status={report.status} files={report.file_count} findings={len(report.findings)}")
    if args.fail_on_fail and report.status == "fail":
        return 1
    return 0


def _cmd_proof_index(args: argparse.Namespace) -> int:
    report = scan_repo(args.repo)
    write_json(build_proof_index(report), args.json_out)
    print(f"proof-index={args.json_out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="release-scan",
        description="Scan a public release surface and emit reviewable proof artifacts.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a repository release surface")
    scan.add_argument("repo", type=Path)
    scan.add_argument("--json-out", required=True, type=Path)
    scan.add_argument("--md-out", type=Path)
    scan.add_argument("--fail-on-fail", action="store_true")
    scan.set_defaults(func=_cmd_scan)

    proof = sub.add_parser("proof-index", help="build a compact proof index")
    proof.add_argument("repo", type=Path)
    proof.add_argument("--json-out", required=True, type=Path)
    proof.set_defaults(func=_cmd_proof_index)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

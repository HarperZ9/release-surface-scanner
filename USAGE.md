# Usage

Release Surface Scanner turns a repository into a reviewable release packet:
required-file checks, `.env` exclusion, secret-shape detection (without echoing
the matched value), per-file SHA-256 hashes, a machine-readable release report,
and a compact proof index.

It has **no runtime dependencies** and targets **Python 3.10+**.

## Install

From a checkout of this repository:

```powershell
pip install .
```

Or for local development (editable, with test tooling):

```powershell
pip install -e ".[dev]"
```

Installing exposes the `release-scan` console script. If you prefer not to
install, you can run the package directly with
`python -m release_surface_scanner ...` (set `PYTHONPATH=src` when running from
a source checkout).

## CLI

```
release-scan --version
release-scan scan <repo> --json-out <path> [--md-out <path>] [--fail-on-fail]
release-scan proof-index <repo> --json-out <path>
```

| Command       | Required args                | Optional flags                          |
| ------------- | ---------------------------- | --------------------------------------- |
| `scan`        | `<repo>`, `--json-out PATH`  | `--md-out PATH`, `--fail-on-fail`       |
| `proof-index` | `<repo>`, `--json-out PATH`  | —                                       |

Notes on behavior (from the source):

- **Required files** checked at the repo root: `README.md`, `LICENSE`,
  `pyproject.toml`, `.gitignore`. A missing one produces a `fail` finding.
- **Excluded** from hashing/reporting: `.env`, any `.env.*` except
  `.env.example`, and the directories `.git`, `.pytest_cache`, `__pycache__`,
  `build`, `dist`, `out`, `node_modules`.
- **Secret-shaped** values (e.g. `sk-...`, `AKIA...`, `…_key = "…"`) are flagged
  by line number only; the matched text is never written to the report.
- `status` is `"fail"` if any finding has level `fail`, otherwise `"pass"`.
- `--fail-on-fail` makes `scan` exit non-zero (exit code `1`) when `status` is
  `"fail"`; without it the command exits `0` regardless. An `OSError` (e.g. an
  unreadable path) exits `2`.

## Worked examples

### 1. Scan a repository to JSON + Markdown

```powershell
release-scan scan . --json-out out/release-report.json --md-out out/release-report.md
```

Expected stdout:

```
status=pass files=4 findings=0
```

`out/release-report.json` (captured against the bundled
`fixtures/sample_repo`; hashes are content-derived and stable for that input):

```json
{
  "excluded_paths": [],
  "file_count": 4,
  "files": [
    {
      "bytes": 18,
      "kind": "required-file",
      "path": ".gitignore",
      "sha256": "173d1764d73725f627f9cab942a0b6b78c47c01a9e915466150967975c844845"
    },
    {
      "bytes": 4,
      "kind": "required-file",
      "path": "LICENSE",
      "sha256": "adc37366f403835c1470ab2df93d3837d4719372fc1ef8593d922e06f033f8b2"
    },
    {
      "bytes": 44,
      "kind": "required-file",
      "path": "pyproject.toml",
      "sha256": "93d578fe36417f9381470df03d5fe48629b2b55686e7d0ccbdfa3605493bd994"
    },
    {
      "bytes": 86,
      "kind": "required-file",
      "path": "README.md",
      "sha256": "449f5d95121ed311b907f00fb846e4313a459a8c9c6f740f7c169ca3b1169ad3"
    }
  ],
  "findings": [],
  "repo_hash": "f009e453905806acc4a045720a9f967ee95224555e3fafa86f02570e3d929fe6",
  "root": "<absolute path to the scanned repo>",
  "schema": "release-surface-scanner.report.v1",
  "secret_shape_count": 0,
  "status": "pass"
}
```

`out/release-report.md`:

```markdown
# Release Surface Scanner

- Status: `pass`
- Files included: 4
- Excluded paths: 0
- Secret-shaped findings: 0
- Repository hash: `f009e453905806acc4a045720a9f967ee95224555e3fafa86f02570e3d929fe6`

No release-blocking findings.
```

### 2. Gate a release in CI

Use `--fail-on-fail` so the process exits non-zero when the surface is not
clean (missing required file, or a secret-shaped value):

```powershell
release-scan scan . --json-out out/release-report.json --fail-on-fail
```

On a repo missing `LICENSE`, `pyproject.toml`, and `.gitignore`, expected
stdout (illustrative):

```
status=fail files=1 findings=3
```

and the process exits `1`, failing the CI step.

### 3. Build a proof index

The proof index is a compact subset of the report containing only
`required-file`, `test`, and `doc` evidence, plus the repo hash and status:

```powershell
release-scan proof-index . --json-out out/proof-index.json
```

Expected stdout (the printed path reflects your `--json-out` value):

```
proof-index=out/proof-index.json
```

`out/proof-index.json` (captured against `fixtures/sample_repo`):

```json
{
  "evidence": [
    { "bytes": 18, "kind": "required-file", "path": ".gitignore", "sha256": "173d1764d73725f627f9cab942a0b6b78c47c01a9e915466150967975c844845" },
    { "bytes": 4, "kind": "required-file", "path": "LICENSE", "sha256": "adc37366f403835c1470ab2df93d3837d4719372fc1ef8593d922e06f033f8b2" },
    { "bytes": 44, "kind": "required-file", "path": "pyproject.toml", "sha256": "93d578fe36417f9381470df03d5fe48629b2b55686e7d0ccbdfa3605493bd994" },
    { "bytes": 86, "kind": "required-file", "path": "README.md", "sha256": "449f5d95121ed311b907f00fb846e4313a459a8c9c6f740f7c169ca3b1169ad3" }
  ],
  "finding_count": 0,
  "repo_hash": "f009e453905806acc4a045720a9f967ee95224555e3fafa86f02570e3d929fe6",
  "schema": "release-surface-scanner.proof-index.v1",
  "status": "pass"
}
```

### 4. Use the Python API

The package exports `scan_repo`, `build_proof_index`, the data models, and
`__version__`:

```python
from release_surface_scanner import scan_repo, build_proof_index, __version__

report = scan_repo("fixtures/sample_repo")
print(__version__)                 # "0.1.0"
print(report.status)               # "pass"
print(report.file_count)           # 4
print(report.secret_shape_count)   # 0
print(report.repo_hash[:16])       # "f009e453905806ac"

# report.to_dict() is the same structure written by the CLI's --json-out.
index = build_proof_index(report)
print(index["schema"])             # "release-surface-scanner.proof-index.v1"
print(len(index["evidence"]))      # 4
```

`scan_repo` accepts a `str` or `pathlib.Path` and returns a frozen
`ReleaseReport` dataclass (see `release_surface_scanner.models`).
`build_proof_index` takes that report and returns a plain `dict`. Use
`release_surface_scanner.reporting.write_json` / `write_markdown` to persist
results yourself.

> Output blocks above were captured by running the tool against the bundled
> `fixtures/sample_repo`. Per-file `sha256` and `repo_hash` values are derived
> from file content and will differ for any other repository.

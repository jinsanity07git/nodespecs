# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`nodespecs` (imported as `specs`) is a Python package that summarizes a computer's system and hardware (OS, CPU, GPU, memory, disk, network), runs a small CPU benchmark, organizes a downloads folder, indexes a filesystem into SQLite, generates a Mermaid gitGraph from a local git repo, and provides a streaming HTTP upload server plus a custom TCP file-transfer client/server. Published to PyPI as `nodespecs`; installed module name is `specs`.

**Design philosophy: a Swiss Army Knife library.** The package is built to be lightweight, portable, and forgiving about its environment. It targets `python>=3.6`, depends on a single runtime package (`tabulate`), and uses lazy, on-demand dependency installation (see `ensure_lib` / `ensure_libs` in `src/specs/hardware/deps.py`) so that an old Python interpreter or a host without `psutil` / `GPUtil` / `uploadserver` does not block import — heavy deps are pulled in only when the function that needs them is first called. Prefer the stdlib; reach for `os`, `socket`, `subprocess`, `platform`, `pathlib`, `sqlite3`, `http`, `argparse` before adding a third-party dep. Lazy-decorate any new function that needs a non-stdlib module.

## Commands

All commands run from the repo root.

```bash
# Install (uv, preferred per README)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.12
uv init
uv add nodespecs
uv pip install psutil
uv run -m specs                  # default: full system info
uv run -m specs bcpu             # CPU benchmark only
uv run -m specs -v               # print version
uv run -m specs -l=1             # lite: native python platform info only
uv run -m specs fclean           # organize ~/Downloads by extension
uv run -m specs upload           # streaming upload server on :8000
uv run -m specs server           # custom TCP file server on :12345
uv run -m specs cld -i='<ip>'    # upload top-level files from cwd to TCP server
uv run -m specs.disk.drive --dir "F:\\" --db "F:\\file_index.db"

# Install (pip)
pip install nodespecs
python -m specs
python -c "import specs; specs.bench_cpu()"
python -c "import specs; specs.info_gpu()"
python -c "import specs; specs.hardware.get_system_info()"
python -c "from specs.disk import resolve_user_path; print(resolve_user_path())"

# Programmatic API (top-level shortcuts on specs.*)
specs.bench_cpu() | specs.info_plat() | specs.server()
specs.client(host, port, path, progress=False)
specs.clientd(host, port, parentdir="./", progress=True)
specs.whoish() | specs.derive_uid() | specs.environment_check()
specs.info_gpu() | specs.hardware.get_system_info()
```

There is **no test suite, no linter, no formatter configured**. CI is a single `python-publish.yml` workflow that builds and publishes to PyPI on GitHub release (also manually dispatchable). No `Makefile`, `tox`, or `pytest`.

## Architecture

### Entry points

- `src/specs/__init__.py` — package facade. Re-exports the top-level API (`bench_cpu`, `info_plat`, `server`, `client`, `clientd`, `whoish`, `derive_uid`, `environment_check`, `info_gpu`, `ensure_libs`, `__version__`).
- `src/specs/__main__.py` — wires `python -m specs` to `cli.main`.
- `src/specs/cli.py` — argparse CLI. Subcommands: `bcpu`, `fclean` (with `--folder`), `upload`, `server`, `cld -i=<ip>`. Top-level flags: `-v` (version), `-l` (lite), `-u` (utility shortcut), `-i` (iphost for `cld`). Default (no subcommand) prints system + CPU + memory + disk + network info.

### Module layout under `src/specs/`

- `hardware/` — system info printers.
  - `main.py` — `get_system_info`, `boot_time`, `info_sys`, `info_cpu`, `info_mem`, `info_disk`, `info_net`, `check_gpu`, `info_gpu`. All hardware functions that need `psutil` are wrapped with `@ensure_lib("psutil")` from `deps.py`.
  - `deps.py` — `ensure_lib` / `ensure_libs` decorators. At call time, if a required module is missing, it tries `uv add` (if a `.venv` workspace root is found above this file), then `uv pip install`, then `pip install`. Lazy import pattern: missing module is loaded into the function's `__globals__` on first call.
  - `__init__.py` — re-exports the printers + `ensure_lib(s)`.
  - **Note**: `src/specs/hardware.py` is a legacy single-file copy of the same functions. `cli.py` imports from `.hardware` (the package), so the legacy file is only used if something imports `from specs import hardware` directly. Prefer the package.
- `benchmark.py` — `bench_cpu()` (Alex Dedyura's `3.141592 * 2**x` / float-division loop, 10 repeats) and `info_plat()`.
- `cpuinfo.py` — vendored `py-cpuinfo` (CPUINFO_VERSION 8.0.0). Provides `get_cpu_info()`. Treat as third-party; do not hand-edit.
- `pyinfo.py` — `environment_check()` (Python env diagnostics).
- `cmd.py` — cross-platform command map (`keymap` dict) for `df`, `uname`, `systeminfo`, etc. (currently unused by CLI but available for tooling).
- `disk/` — filesystem utilities.
  - `organizer.py` — `organize_folder()` sorts files into Images/Audio/Videos/Documents/Develops/Installer/Archives by extension; `resolve_user_path()` defaults to `~/Downloads`; `resolve_target_url()`, `load_module_from_path()`, `list_files_and_dirs()`.
  - `indexer.py` — `FileIndexer` class: in-memory walk + `search()` (regex, extensions, size filters) + `export_to_sqlite()` (creates `files` and `statistics` tables).
  - `drive.py` — `main()` for `python -m specs.disk.drive`; default root is the Windows raw literal `F:\\`. CLI flags: `--dir`, `--db` (defaults to `<dir>/file_index.db`).
  - `__init__.py` / `automate.py` — re-exports + automation helpers.
- `git/` — Mermaid gitGraph generator.
  - `collector.py` — `GitCollector` shells out to `git` (validated `rev-parse --git-dir` and tag existence first). Collects branches, commits since `base_tag`, and merge commits. Encodes with `errors="replace"` for non-UTF-8 messages.
  - `renderer.py` — `GitMermaidRenderer` builds a Mermaid `gitGraph` block + a markdown summary. `key_branches` and `workflows`/`merge_sequence` are hardcoded against this project's own branch history — generalize if reusing on a different repo.
  - `git_mermaid_generator.py` — CLI entry point; flags: `--tag` (default `v1.1.1`), `--repo-dir`, `--exclude-branches`, `--output`.
- `communicate/` — networking.
  - `tcpip/protocol.py` — wire format: 4-byte big-endian UTF-8 filename length, filename bytes, 8-byte big-endian file size, then raw bytes. Helpers: `send_file_header`, `recv_all`, `receive_file_header`.
  - `tcpip/server.py` — `server(save_path='./')` binds to the host's outbound IP (UDP-trick to `8.8.8.8:80`) on port `12345`, handles SIGINT/SIGTERM, `settimeout(1)` loop. Single concurrent client.
  - `tcpip/client.py` — `client(host, port, path, prg)` and `clientd(host, port, parentdir, prg)` (walks top-level files). Uses `tqdm` for progress when `prg=True` and the module is installed; falls back to no progress bar.
  - `aboutme.py` — `whoish()` (hostname + current user), `derive_uid()` (5-digit ASCII-sum of `user@host`).
  - `upload/__init__.py` — `stream_files()` patches `uploadserver.receive_upload` with `receive_streaming_upload` (streaming multipart parser, `DISK_LIMIT = 2**40` bytes) and calls `uploadserver.main(['8000', '--cgi', '--allow-replace', '--bind', '0.0.0.0', '--directory', './', '--theme', 'dark'])`. Wrapped in `@ensure_libs(["uploadserver","multipart"])`.
  - `tcpsocket.py` — placeholder.
- `format/html2pdf.py` — `render_html_to_pdf()` using `selenium` + headless Chrome + `pdfkit` + `wkhtmltopdf` at `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe` (Windows path; hardcoded). Optional utility, not wired to CLI.

### Versioning

Version lives in two places and they must stay in sync: `src/specs/__init__.py` (`__version__ = "0.3.1"`) and `pyproject.toml` (`[project] version`). `setup.py` reads `__init__.py`, parses the version, and writes it back into `pyproject.toml` via `sync_version()` on every invocation — so editing `__init__.py` is enough; running `python setup.py ...` (or any build) will rewrite `pyproject.toml`.

### Packaging

- Source layout: `src/` with `specs` package; `pyproject.toml` uses setuptools.
- Console script: `realpython = specs.__main__:main` (note the script name is `realpython`, not `specs`).
- Runtime deps: `tabulate >= 0.8.0`. Optional `[dev]`: `GPUtil`, `pip-tools`, `psutil >= 5.9.5`, `toml`. `psutil` is imported at call time by the hardware printers (lazy via `ensure_lib`), so the package is importable without it but `info_cpu`/`info_mem`/etc. trigger an install on first use.
- `requirements.txt` is the pip-compile output, only pinning `tabulate==0.8.0`.

### Things to know before editing

- **Lazy deps via `ensure_lib`/`ensure_libs`.** Hardware and upload code do not import `psutil` / `GPUtil` / `uploadserver` / `multipart` at module top. The decorators install on first call, preferring `uv add` when a `.venv` workspace root is found. If you add a new hardware helper that needs a non-stdlib module, decorate it; do not add a top-level import.
- **TCP file protocol is fixed.** Length-prefixed filename (4 bytes BE) + filename (UTF-8) + filesize (8 bytes BE) + raw bytes. Any change to `communicate/tcpip/protocol.py` must be made in lockstep with both client and server.
- **Server is single-client, blocking.** `communicate/tcpip/server.py` uses `listen(1)` and `settimeout(1)` in a `while True` loop. Multiple `clientd()` uploads from one client work because `clientd()` reuses one connection sequentially with a 1s sleep between files, not concurrently.
- **Default file-indexer root is `F:\\`.** `specs.disk.drive` defaults to a Windows raw-path literal. Pass `--dir` on any non-Windows host or it will fail-fast with exit 2.
- **`git_mermaid_generator.py` is project-specific.** `key_branches`, `workflows`, and `merge_sequence` in `git/renderer.py` are hardcoded to this repo's PR numbers and branch names. Reusing on another repo requires editing those lists.
- **PyPI publish workflow** (`/.github/workflows/python-publish.yml`) runs on GitHub `release: published` and on manual dispatch. It builds with `python -m build`, publishes with `twine` using the `PYPI_API_TOKEN` secret, and uploads `dist/` as a build artifact. There is no test step in CI.

## Package health principles (for PyPI contributors)

These are the aspects a `pip install` user will judge this package on, in rough order of impact. Each one is small enough to land as its own commit.

1. **Versioning is honest.** `__version__` in `src/specs/__init__.py` is the source of truth; `pyproject.toml` is synced by `setup.py::sync_version` on every build. Never hand-edit both. Use [SemVer](https://semver.org/): a bug fix or docs-only change is a patch bump, a new public symbol is a minor bump, a breaking change to a documented import or signature is a major bump. If the changelog says "fixed" and the version doesn't move, the release is not real.
2. **CHANGELOG.md is required for every release.** A user scanning PyPI should be able to read "what changed since 0.3.2" without opening GitHub. One short section per version, grouped by *Added / Changed / Fixed / Removed*. Date in ISO format (`YYYY-MM-DD`). Skip the changelog → skip the release.
3. **Tests are the contract.** A package without a test suite is a demo. The Swiss Army Knife philosophy does not justify "no tests" — it justifies "stdlib `unittest`, no new third-party deps." Every public function should have at least one happy-path and one degrade-gracefully test. Tests run with `python -m unittest discover -s tests` and must pass on Python 3.6+ (the stated `python>=3.6` target).
4. **CI must run the tests.** `.github/workflows/python-publish.yml` currently only builds and publishes on release; it does not run tests. A `test` job on push/PR against `main` is the difference between "broken releases are caught at publish time" and "broken releases are caught at PR time." The two CI files are separate on purpose — tests are gates, publish is delivery.
5. **`.gitignore` is part of the source.** Build artifacts (`dist/`, `*.egg-info/`, `build/`, `.pytest_cache/`, `.tox/`, `.coverage`, `htmlcov/`, `__pycache__/`, `*.pyc`) must never be committed. They pollute diffs, confuse `git log`, and make the repo bigger. A stale `src/*.egg-info/` in git is a smell that says "we forgot to gitignore it."
6. **`pyproject.toml` metadata is user-facing.** PyPI renders `[project]` fields directly: `description` (one line, the headline), `readme` (the long version), `requires-python` (the floor), `license`, `classifiers` (the discoverability tags), `keywords` (search hits), `urls` (Homepage, Issues, Changelog, Source). Missing classifiers = lower search ranking. Missing `[project.urls]` = no "Source" / "Issues" button on the PyPI page.
7. **README is the landing page.** It must show (a) one-line install, (b) one copy-pasteable usage example, (c) a feature list, and (d) what Python versions are supported — within the first 30 lines. Anything below the fold is for the curious, not the user evaluating `pip install`. Add a badge row near the top: PyPI version, supported Python versions, license. They cost nothing and signal "this is maintained."
8. **Lazy-decorate new third-party deps.** `ensure_lib` / `ensure_libs` are not just a hack for `psutil`; they are the architectural contract for *every* non-stdlib dep this package uses. A new helper that does `import requests` at the top of a module is a regression: the package no longer imports cleanly on a fresh Python 3.6 venv.
9. **Public API stability.** The names in `src/specs/__init__.py`'s `__all__` plus the names re-exported by `src/specs/hardware/__init__.py` and `src/specs/disk/__init__.py` are the contract. Renaming or removing one of them is a breaking change. The `internal`/`_` prefix is reserved for private modules — do not import those from outside the package.
10. **Errors are messages, not stack traces.** A `pip install` user on a host with no NVIDIA driver, no `nvidia-smi`, no `psutil`, no `pip`, and Python 3.12 should still see a clean friendly message from `info_gpu()` and a clean exit code. We learned this in PR #6: any code path that calls `subprocess.check_call` on a user-controlled string is a future issue waiting to happen. Guard every external call.

When in doubt, the order is: tests first, then a changelog entry, then a version bump, then the code change. Tests are the only artifact that proves a fix is real.

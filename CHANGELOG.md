# Changelog

All notable changes to `nodespecs` (imported as `specs`) are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2026-06-18

### Added
- `FileIndexer` now captures `st_blocks`, `st_nlink`, `st_ino`, and
  `st_dev` per file, and reports a deduped `on_disk_size` (sum of
  `st_blocks * 512` over distinct inodes) alongside the existing
  `total_size`. This is the field that most closely matches what the
  OS reports as "used space" for a file walk; it accounts for cluster
  rounding on NTFS / exFAT and for sparse files, and is not inflated
  by hardlinks.
- `get_statistics()` returns five new keys: `unique_files`,
  `logical_size` (deduped), `on_disk_size` (deduped),
  `hardlink_extra_paths` (paths beyond the first for each shared
  inode), and `skipped_paths` (directory / entry access errors).
- The SQLite export adds matching `on_disk`, `blocks`, `nlinks`,
  `inode`, and `device` columns to the `files` table (plus indexes on
  `(device, inode)` and `extension`) and the same five new rows to
  the `statistics` table.
- `tests/test_indexer.py`: stdlib `unittest` smoke tests covering the
  new counts, hardlink dedup, the per-directory error path, and the
  SQLite round-trip.

### Changed
- `FileIndexer.index_directory()` is now implemented with an explicit
  `os.scandir` stack walker instead of `os.walk`. A `PermissionError`
  on a single subdirectory no longer aborts the whole walk; the
  affected entry is recorded in `skipped_paths` and the walk continues
  with the rest of the tree. Symlink-following behavior is unchanged
  (`follow_symlinks=False`).
- `specs.disk.drive` (`python -m specs.disk.drive`): the `--dir`
  default is now the current working directory on non-Windows hosts
  (still `F:\\` on Windows, matching the legacy behavior). After a
  successful index, the CLI prints a side-by-side comparison between
  `on_disk_size` and `shutil.disk_usage(root_dir)` so the gap from
  filesystem metadata, snapshots, and unread subtrees is visible
  instead of hidden.

## [0.4.0] - 2026-06-16

### Added
- `tests/test_deps.py`: stdlib `unittest` smoke tests covering the lazy-install
  blocklist in `src/specs/hardware/deps.py` (issue #5) and the graceful-degrade
  path of `info_gpu()`.
- `CHANGELOG.md`: this file.
- CI test job in `.github/workflows/ci.yml` running
  `python -m unittest discover -s tests` on Python 3.10 / 3.11 / 3.12 for
  every push and pull request against `main`.

### Changed
- `pyproject.toml` metadata: filled in `classifiers`, `keywords`,
  `[project.urls]` (Homepage, Repository, Issues, Changelog, Source), and a
  one-line `description` so PyPI renders the package page correctly.
- `README.md`: added a badge row at the top (PyPI version, supported Python
  versions, license, CI status) and tightened the "30-line landing page".
- `.gitignore`: added `*.egg-info/`, `build/`, `dist/`-adjacent artifacts,
  and other common Python tool caches.
- `__version__` bumped to `0.4.0`; `setup.py` syncs `pyproject.toml`.
- `.github/workflows/python-publish.yml` overhauled:
  - Renamed in spirit to `publish-and-deploy`; runs on `release: published`
    and `workflow_dispatch`.
  - Split into three jobs: `build` (sdist + wheel, uploads `dist/` as a
    workflow artifact), `publish` (downloads the artifact, `twine upload` with
    `PYPI_API_TOKEN`), and `deploy-update` (emits a GitHub Deployment object +
    success status so any subscriber to deployment events — auto-update feeds,
    dashboards, deploy bots — can react to a new PyPI release landing).
  - Bumped action versions: `actions/checkout@v7`, `actions/setup-python@v6`,
    `actions/upload-artifact@v7`, `actions/download-artifact@v7`,
    `actions/github-script@v8`.
  - Added `id-token: write` permission in the publish job in preparation for
    a future switch to OIDC trusted publishing (no behavior change yet).
  - Added `concurrency: publish-and-deploy` so a re-published release does not
    trigger a second, racing publish job.
  - The `pypi` environment can now carry required reviewers / wait-timer in
    repo settings for a manual gate before the upload runs.

## [0.3.2] - 2025-12-18

### Fixed
- `info_gpu()` no longer crashes on Python 3.12 venvs. GPUtil 1.4.0's
  transitive `from distutils import spawn` (removed in 3.12) used to trigger
  a doomed `pip install distutils` that surfaced a `CalledProcessError` to
  the user. `info_gpu()` now probes `nvidia-smi` first, guards the install
  path with a `_NON_PACKAGE_NAMES` blocklist in `src/specs/hardware/deps.py`,
  and degrades gracefully with a friendly message. (issue #5)
- Removed dead legacy `src/specs/hardware.py` (single-file copy of the
  package; no live code path imported it). The `check_gpu` helper was
  folded into `info_gpu()`.

## [0.3.1] - 2025-12-10

### Changed
- `pyproject.toml`: bumped to `setuptools>=61.0.0` and added `toml` to the
  build-system requires.
- README: updated CLI usage examples.

## [0.3.0] - 2025-11-20

### Changed
- Restructured the package into modular subpackages: `specs/hardware/`,
  `specs/disk/`, `specs/git/`, `specs/communicate/`. The legacy
  `specs.hardware` module path is preserved as a thin re-export for
  backward compatibility.
- Hardware info printers now lazy-install their `psutil` dependency via the
  `ensure_lib` decorator, preferring `uv add` over `pip install` when a
  `.venv` is found.

### Added
- `specs.disk.drive` CLI: recursively index a directory and export to
  SQLite.
- `specs.git.git_mermaid_generator` CLI: generate a Mermaid `gitGraph`
  visualization of commits since a tag.

## [0.2.0] - 2024-06-08

### Added
- `specs.server()` / `specs.client()`: custom TCP file-transfer
  client/server (length-prefixed protocol in
  `specs.communicate.tcpip.protocol`).
- `specs.upload`: streaming HTTP upload server based on `uploadserver`,
  with a custom `receive_streaming_upload` handler that raises the
  multipart disk limit to 1 TiB.

### Fixed
- `specs.server()` now binds to the host's outbound IP (UDP trick to
  `8.8.8.8:80`) instead of `0.0.0.0`, which on some systems raised
  `PermissionError: [Errno 1] Operation not permitted`. (issue #4)

## [0.1.9] - 2024-05-30

### Fixed
- `pip-tools>=7.4.0` pinned in dev requirements; older versions could not
  resolve `setuptools` in the new resolver.

## [0.1.8] - 2024-05-15

### Fixed
- `specs.disk.automate`: `ImportError: cannot import name 'resolve_path'`
  when called from a clean install; renamed the function to
  `resolve_target_url` to match the public API.

## [0.1.7] - 2024-05-10

### Added
- `specs.whoish()` and `specs.derive_uid()`: hostname / current-user lookup
  with a 5-digit ASCII-sum identifier.

## [0.1.6] - 2024-04-30

### Added
- `specs.disk.organizer.resolve_target_url`: working-directory-relative
  path resolver used by the TCP upload server.

## [0.1.1] - 2024-04-15

### Added
- Initial release. Hardware info (CPU, memory, disk, network), CPU
  benchmark, and downloads-folder organizer.

[Unreleased]: https://github.com/jinsanity07git/nodespecs/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/jinsanity07git/nodespecs/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/jinsanity07git/nodespecs/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/jinsanity07git/nodespecs/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/jinsanity07git/nodespecs/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/jinsanity07git/nodespecs/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jinsanity07git/nodespecs/compare/v0.1.9...v0.2.0
[0.1.9]: https://github.com/jinsanity07git/nodespecs/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/jinsanity07git/nodespecs/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/jinsanity07git/nodespecs/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/jinsanity07git/nodespecs/compare/v0.1.1...v0.1.6
[0.1.1]: https://github.com/jinsanity07git/nodespecs/releases/tag/v0.1.1

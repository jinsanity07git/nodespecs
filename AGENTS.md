# Agent Instructions for nodespecs

## Project Shape
- `nodespecs` (imported as `specs`) is a Python package that summarizes a computer's system and hardware, runs a small CPU benchmark, organizes a downloads folder, indexes a filesystem into SQLite, generates a Mermaid `gitGraph` from a local git repo, and ships a streaming HTTP upload server plus a custom TCP file-transfer client/server.
- Main entry points are [src/specs/__init__.py](src/specs/__init__.py) (facade), [src/specs/cli.py](src/specs/cli.py) (argparse CLI), [src/specs/__main__.py](src/specs/__main__.py) (`python -m specs`), and the subpackages `hardware/`, `disk/`, `git/`, `communicate/`.
- Keep changes consistent with the existing package shape; do not invent new top-level entry points or new subpackage layers without a strong reason.
- Read [CLAUDE.md](CLAUDE.md) for the project-specific design philosophy (Swiss Army Knife — stdlib first, lazy deps, `python>=3.6`), the file map, and the package-health principles.

## Environment
- Python 3.6+ is the stated target; the CI matrix runs 3.10 / 3.11 / 3.12. Use stdlib whenever possible; reach for `os`, `socket`, `subprocess`, `platform`, `pathlib`, `sqlite3`, `http`, `argparse` before adding a third-party dep.
- `uv` is the preferred package manager for local dev (per the README); `pip` works too. `setup.py` calls `sync_version()` so editing `__version__` in [src/specs/__init__.py](src/specs/__init__.py) is enough — `pyproject.toml` is rewritten on every build.
- Do not raise the minimum Python version. A new helper that needs a non-stdlib module must be wrapped in `ensure_lib` / `ensure_libs` from [src/specs/hardware/deps.py](src/specs/hardware/deps.py); never `import` such modules at module top.

## Common Commands
- Editable install: `uv pip install -e .` (or `pip install --break-system-packages -e .` on a system Python).
- Tests (stdlib `unittest`, no pytest): `python -m unittest discover -s tests -v`.
- Smoke check: `python -m py_compile src/specs/**/*.py`.
- CLI sanity: `python -m specs -v`, `python -m specs bcpu`, `python -m specs fclean`.
- Build sdist + wheel: `python -m build` (writes to `dist/`; the publish workflow uploads this artifact).

## Working Rules
- Prefer small, local changes over broad refactors. The package is small on purpose.
- Follow the existing module layout (subpackages with `__init__.py` re-exports, lazy-decorated third-party deps, friendly-degrade error messages).
- Keep the public API stable. The names in `src/specs/__init__.py`'s `__all__` plus the re-exports in `hardware/__init__.py` and `disk/__init__.py` are the contract.
- Every third-party import must be lazy (decorated with `ensure_lib` / `ensure_libs`). A bare `import requests` at the top of a new module is a regression.
- Errors are messages, not stack traces. A `pip install` user with no NVIDIA driver, no `nvidia-smi`, no `psutil`, and Python 3.12 should still see a clean friendly message and a clean exit code.
- Update the README when setup or usage behavior changes; the README is the PyPI landing page.
- Update `CHANGELOG.md` for every release-impacting change. Keep-a-Changelog format, dated sections, grouped by *Added / Changed / Fixed / Removed*.
- Keep `pyproject.toml` metadata honest: `version`, `classifiers`, `keywords`, `[project.urls]`, and `requires-python` are user-facing.

## Feature Delivery Workflow

Use this workflow for substantial features, bug fixes, refactors, and other release-impacting code changes unless the user explicitly requests a different Git strategy:

**Pipeline:** feature prompt → implementation contract → latest-base feature branch → milestone implementation and commits → version/changelog/docs → validation → push → draft PR with a descriptive title and detailed body → handoff.

1. **Translate the feature prompt into an implementation contract.**
   - Restate the intended behavior, assumptions, scope boundaries, acceptance criteria, and validation plan.
   - Inspect the relevant code and repository state before editing; preserve unrelated work. The Swiss Army Knife philosophy and the package-health principles in [CLAUDE.md](CLAUDE.md) are non-negotiable context.
2. **Create a feature branch from the latest target branch.**
   - Identify the requested PR base; otherwise use the repository's active development branch (`main`).
   - Fetch the remote base and branch from its latest commit using a descriptive name such as `fix/<issue-n-slug>` or `chore/<topic>` (e.g. `fix/issue-5-auto-install-uv`, `chore/package-health`, `chore/publish-workflow`).
   - Do not implement substantial feature work directly on `main`.
3. **Implement in reviewable milestones.**
   - Keep changes small and aligned with the existing Swiss Army Knife architecture: stdlib first, lazy deps, friendly errors.
   - Define milestone boundaries before or during implementation, such as core logic fix, test coverage, and documentation/version sync.
   - Commit each completed, coherent milestone separately with a concise imperative message (e.g. `fix(gpu): never pip-install distutils; degrade gracefully when no nvidia-smi`). Stage only files belonging to that milestone.
4. **Update release metadata and documentation.**
   - Bump `__version__` in [src/specs/__init__.py](src/specs/__init__.py) using SemVer. `setup.py::sync_version` will rewrite `pyproject.toml` on the next build — never hand-edit both. Patch bump for a bug fix, minor for a new public symbol, major for a breaking change.
   - Add a `CHANGELOG.md` entry under the new version section (Keep-a-Changelog format, dated, grouped by *Added / Changed / Fixed / Removed*). Skip the changelog → skip the release.
   - Update README setup, usage, configuration, or limitations whenever user-visible behavior changes.
5. **Validate before publishing.**
   - Run `python -m unittest discover -s tests -v` and `python -m py_compile src/specs/**/*.py`. CI already runs the tests on Python 3.10 / 3.11 / 3.12 — they must pass locally first.
   - For a release-impacting change, also run the relevant CLI smoke: `python -m specs -v`, `python -m specs bcpu`, `python -m specs fclean` on a clean tree, plus any feature-specific call.
   - Confirm the final worktree and diff contain only intended files (no stray `dist/`, `*.egg-info/`, `__pycache__/`, or unrelated edits).
6. **Push the feature branch and create a draft pull request.**
   - Push with upstream tracking (`git push -u origin <branch>`); never force-push unless the user explicitly authorizes it.
   - Use a descriptive PR title, normally `type(scope): summary` (e.g. `fix(gpu): never pip-install distutils; degrade gracefully when no nvidia-smi`, `chore: package health (CHANGELOG, CI tests, .gitignore, metadata, README badges, 0.4.0)`).
   - Write a detailed Markdown body covering: summary and motivation, implementation/model, user and developer impact, important behavior and tradeoffs, validation results, known limitations, and any follow-up work.
   - Target the selected base branch (`main` unless the user says otherwise) and verify the PR is open with the correct head/base refs.
7. **Hand off the result.**
   - Report the branch, milestone commits, version change, validation results, and PR URL. Update the related GitHub issue (comment, link the PR) if one exists.

Skip the branch/version/PR workflow for pure conversation, inspection-only work, plans, and small documentation-only edits unless the user asks to publish them. Direct commits or pushes to `main` require explicit user instruction — a hotfix on `main` is acceptable only when the user says so (e.g. a broken release pipeline).

## Hotfix Practice
- For a live incident (CI red on `main`, broken release), commit and push directly to `main` only when the user explicitly authorizes it. The `a9edd94 fix(ci): install twine in publish job` commit is a worked example of a direct-to-`main` hotfix.
- Write the fix as a single, well-scoped commit with an imperative message that names the symptom, not just the fix.
- After the hotfix lands, re-run the failed workflow via `workflow_dispatch` (if available) to confirm green, then write up what changed and why it bypassed the normal feature-delivery pipeline.

## PyPI Publish Pipeline
- `.github/workflows/python-publish.yml` runs on `release: published` and `workflow_dispatch`. The `build` job produces sdist + wheel and uploads `dist/` as a workflow artifact. The `publish` job downloads that artifact, installs `twine` (it does NOT inherit from the build runner), and runs `python -m twine upload dist/*` using `PYPI_API_TOKEN`. The `deploy-update` job emits a GitHub Deployment object + success status.
- Any change to the publish pipeline must be validated by walking through both the release-published path and the manual-dispatch path on a test release.
- The `pypi` environment in repo settings is the right place to add a required-reviewer gate or wait-timer if the maintainer wants a manual approval step before each upload.

## Good Places To Check
- Project philosophy and package-health principles: [CLAUDE.md](CLAUDE.md)
- Public API surface: [src/specs/__init__.py](src/specs/__init__.py)
- Lazy-dep decorators and the `_NON_PACKAGE_NAMES` blocklist: [src/specs/hardware/deps.py](src/specs/hardware/deps.py)
- Test surface (stdlib `unittest`): [tests/](tests/)
- Release notes: [CHANGELOG.md](CHANGELOG.md)
- Setup, install, and usage: [README.md](README.md)
- Build / publish: [pyproject.toml](pyproject.toml), [setup.py](setup.py), [.github/workflows/](.github/workflows/)

import importlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, MutableMapping


# Stdlib-removed / stdlib-internal names that must never be pip-installed.
# - `distutils` was removed from the standard library in Python 3.12; it is
#   not on PyPI and any `pip install distutils` attempt will fail with a
#   misleading dependency-resolution error (see issue #5).
# - Names starting with an underscore are CPython-internal and not packages.
# Forward-looking: the blocklist is consulted both at decoration time (so a
# stray `@ensure_lib("distutils")` fails loudly) and at install time inside
# `check_imp` (so a transitive `ModuleNotFoundError` for these names cannot
# trigger a doomed `pip install`).
_NON_PACKAGE_NAMES = frozenset({"distutils"})

# PEP 668 marker pip prints to stderr when the target interpreter is an
# externally-managed environment (Debian/Ubuntu system Python 3.11+). On such
# hosts a bare `pip install <pkg>` exits non-zero, which used to surface as a
# raw `subprocess.CalledProcessError` (issue #14). We sniff stderr for this
# marker and offer an interactive `--break-system-packages` retry.
_PEP668_MARKER = "externally-managed-environment"


def _is_blocked_module(name: str) -> bool:
    """Return True if `name` is a stdlib-removed or CPython-internal name
    that should never be pip-installed."""
    return name in _NON_PACKAGE_NAMES or name.startswith("_")


def _raise_blocked(module: str) -> None:
    raise ImportError(
        f"Module {module!r} is not an installable package; "
        "it has been removed from the Python standard library or is "
        "CPython-internal. Install a third-party replacement instead."
    )


def parse_dep(module_name):
    sep = "=="
    if sep in module_name:
        module, version = [i.strip() for i in module_name.split(sep)]
    else:
        module, version = module_name, None

    debug = 0
    if debug:
        print(f"module_name {module}, {version}")
    return module, version


def _find_workspace_root_with_venv(start_path: Path) -> Optional[Path]:
    for parent in [start_path] + list(start_path.parents):
        if (parent / ".venv").is_dir():
            return parent
    return None


def _load_module(module: str):
    importlib.invalidate_caches()
    loaded_module = sys.modules.get(module)
    if loaded_module is not None:
        return loaded_module
    spec = importlib.util.find_spec(module)
    if spec is None:
        return None
    return importlib.import_module(module)


def _is_pep668_error(stderr_text):
    """Return True if pip's stderr indicates an externally-managed
    environment (PEP 668)."""
    return bool(stderr_text) and _PEP668_MARKER in stderr_text


def _friendly_pep668_message(install_target):
    """User-facing explanation shown when we cannot install into an
    externally-managed environment (PEP 668) — either because the host is
    non-interactive or because the user declined the --break-system-packages
    retry."""
    return (
        f"Cannot install {install_target!r}: this Python is an "
        "externally-managed environment (PEP 668). Options:\n"
        "  - use a virtualenv (python -m venv) and install there,\n"
        "  - use `pipx`, or\n"
        f"  - retry manually: {sys.executable} -m pip install "
        f"{install_target} --break-system-packages"
    )


def _prompt_break_system_packages(install_target):
    """Interactively ask whether to retry the install with
    --break-system-packages. Returns True only on an explicit yes; False on
    decline or EOF (e.g. piped stdin). Caller is responsible for checking
    `sys.stdin.isatty()` first so we never block in a non-interactive
    context."""
    try:
        answer = input(
            f"\nRetry installing {install_target!r} with "
            "--break-system-packages? [y/N]: "
        )
    except EOFError:
        return False
    return answer.strip().lower() in ("y", "yes")


def _pip_available():
    """Return True if the current interpreter provides the pip module.

    Virtual environments created by `uv venv` / `uv init` do not include
    pip by default, so `python -m pip install ...` fails there with
    "No module named pip" (issue #21).
    """
    try:
        return importlib.util.find_spec("pip") is not None
    except (ImportError, ValueError):
        return False


def _in_virtualenv():
    """Return True when the running interpreter is a virtual environment
    (as opposed to a base / system installation)."""
    return sys.prefix != sys.base_prefix


def _uv_pip_install(install_target):
    """Install `install_target` into the *current* environment with
    `uv pip install --python <sys.executable>`.

    Preferred fallback when pip itself is missing, since uv-created
    virtualenvs are exactly the environments that ship without pip
    (issue #21). Restricted to virtual environments so we never write
    into an externally-managed system Python without the user's consent
    (PEP 668). Returns True on success, False otherwise.
    """
    uv_path = shutil.which("uv")
    if uv_path is None or not _in_virtualenv():
        return False
    print(f"Attempting to install missing module via uv: {install_target}")
    proc = subprocess.run(
        [uv_path, "pip", "install", "--python", sys.executable, install_target],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode == 0:
        return True
    print("uv pip install failed, attempting to bootstrap pip")
    return False


def _ensurepip_bootstrap():
    """Bootstrap pip into the current environment via
    `python -m ensurepip --upgrade`.

    Returns True when pip is importable afterwards.
    """
    print("Attempting to bootstrap pip via: python -m ensurepip --upgrade")
    proc = subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode != 0:
        print("pip bootstrap failed (ensurepip unavailable or disabled)")
        return False
    importlib.invalidate_caches()
    return _pip_available()


def _friendly_no_pip_message(install_target):
    """User-facing explanation shown when the current environment has no
    pip and neither the uv fallback nor the ensurepip bootstrap could
    provide an installer (issue #21)."""
    return (
        f"Cannot install {install_target!r}: this Python environment has "
        "no pip module (uv-created virtualenvs do not include one). "
        "Options:\n"
        f"  - run `uv pip install {install_target}`, or\n"
        "  - bootstrap pip with `python -m ensurepip --upgrade`, or\n"
        "  - use an environment that includes pip"
    )


def _pip_install_or_raise(install_target):
    """Run `python -m pip install <install_target>`.

    Virtual environments created by uv ship without pip, so the bare
    `python -m pip` invocation fails there with "No module named pip"
    (issue #21). When pip is missing we first try `uv pip install` into
    the current environment, then an `ensurepip` bootstrap, and only then
    give up with a friendly `ImportError`.

    Unlike a bare `subprocess.check_call`, a non-zero exit never surfaces as a
    raw `subprocess.CalledProcessError` (issue #14): on a PEP 668
    externally-managed failure we offer an interactive
    `--break-system-packages` retry, and every other failure becomes a clear
    `ImportError`. Returns None on success.
    """
    if not _pip_available():
        if _uv_pip_install(install_target):
            return
        if _ensurepip_bootstrap():
            # pip is now importable; fall through to `python -m pip` so
            # the PEP 668 handling below still applies.
            pass
        else:
            raise ImportError(_friendly_no_pip_message(install_target))

    # Use stdout/stderr=PIPE + universal_newlines (not capture_output / text,
    # which are 3.7+) so the stated python>=3.6 target keeps working.
    base_cmd = [sys.executable, "-m", "pip", "install", install_target]
    print(f"Attempting to install missing module: {install_target}")
    proc = subprocess.run(
        base_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode == 0:
        return

    if _is_pep668_error(proc.stderr):
        if sys.stdin.isatty() and _prompt_break_system_packages(install_target):
            retry_cmd = base_cmd[:-1] + ["--break-system-packages", install_target]
            print("Retrying with --break-system-packages ...")
            retry = subprocess.run(
                retry_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            if retry.returncode == 0:
                return
            raise ImportError(
                f"pip install --break-system-packages for {install_target!r} "
                f"failed:\n{(retry.stderr or '').strip()}"
            )
        # Non-interactive host, or user declined.
        raise ImportError(_friendly_pep668_message(install_target))

    # Some other pip failure — surface a clean message, not CalledProcessError.
    raise ImportError(
        f"pip install for {install_target!r} failed:\n{(proc.stderr or '').strip()}"
    )


def check_imp(module_name, target_globals: Optional[MutableMapping[str, object]] = None):
    module, version = parse_dep(module_name)
    if _is_blocked_module(module):
        _raise_blocked(module)
    missing_module = module

    try:
        loaded_module = _load_module(module)
    except ModuleNotFoundError as e:
        loaded_module = None
        missing_module = e.name or module

    # If the transitive import blew up on a stdlib-removed name, do not try
    # to pip-install that name either (see issue #5: GPUtil 1.4.0 →
    # `from distutils import spawn` on Python 3.12).
    if loaded_module is None and _is_blocked_module(missing_module):
        _raise_blocked(missing_module)

    if loaded_module is not None:
        if target_globals is not None:
            target_globals[module] = loaded_module
        else:
            globals()[module] = loaded_module
        return True

    install_target = module_name if missing_module == module and version else missing_module
    workspace_root = _find_workspace_root_with_venv(Path(__file__).resolve())
    uv_path = shutil.which("uv")
    installed = False

    if uv_path and workspace_root:
        print(f"Attempting to add missing module via uv: {install_target}")
        try:
            subprocess.check_call([uv_path, "add", install_target], cwd=str(workspace_root))
            installed = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("uv add failed, attempting uv pip install")

        if not installed:
            try:
                subprocess.check_call(
                    [uv_path, "pip", "install", install_target], cwd=str(workspace_root)
                )
                installed = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("uv pip install failed, falling back to pip")

    if not installed:
        _pip_install_or_raise(install_target)
        installed = True

    # Re-load the module after successful install so it is available in
    # the caller's globals. Without this, a function decorated with
    # @ensure_lib("psutil") would crash with NameError on the first call
    # because the module was pip-installed but never imported into the
    # decorated function's scope (issue #16).
    loaded_module = _load_module(module)
    if loaded_module is not None:
        if target_globals is not None:
            target_globals[module] = loaded_module
        else:
            globals()[module] = loaded_module
        return True
    return False


def ensure_lib(module_name):
    """Decorator that lazily imports `module_name` on first call.

    If the module is not installed, the wrapper delegates to
    `check_imp` (same path as `ensure_libs`) which tries `uv add` /
    `uv pip install` (when a `.venv` workspace root is found) and falls
    back to `pip install`. The `_NON_PACKAGE_NAMES` blocklist is enforced
    so a stray transitive `ModuleNotFoundError` for a stdlib-removed name
    (e.g. `distutils` on Python 3.12) cannot trigger a doomed
    `pip install` (see issue #5).

    The decorator also accepts an optional `version_spec` (e.g.
    `"psutil>=5.9.5"`) so callers can pin a minimum version on the
    auto-install. When omitted, the bare module name is used.
    """
    module, _ = parse_dep(module_name)
    if _is_blocked_module(module):
        _raise_blocked(module)

    def decorator(func):
        def wrapper(*args, **kwargs):
            target_globals = func.__globals__
            # Skip the install path when the module is already visible
            # to the wrapped function. Two caches matter:
            #   * `module in target_globals` — the wrapped body sees it
            #     as a global name (set by a previous check_imp success
            #     or by the caller's own `import`).
            #   * `module in sys.modules` — the module is loaded, but
            #     the wrapped body resolves it via `import` rather than
            #     as a global. (We do not pre-bind it into
            #     target_globals on a hit, to avoid surprising mutations
            #     of the caller's namespace.)
            if (
                module not in target_globals
                and module not in sys.modules
            ):
                # Delegate to check_imp so the install path (uv add /
                # uv pip install / pip install) and the blocklist guard
                # are shared with ensure_libs. check_imp loads the
                # module into target_globals on success, so subsequent
                # calls hit the `module in target_globals` shortcut.
                check_imp(module_name, target_globals=target_globals)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def ensure_libs(modules):
    # Validate every requested module name at decoration time so a typo
    # (`@ensure_libs(["distutils"])`) fails loudly rather than silently.
    for module_name in modules:
        module, _ = parse_dep(module_name)
        if _is_blocked_module(module):
            _raise_blocked(module)

    def decorator(func):
        def wrapper(*args, **kwargs):
            target_globals = func.__globals__
            for module_name in modules:
                check_imp(module_name, target_globals=target_globals)
            return func(*args, **kwargs)

        return wrapper

    return decorator

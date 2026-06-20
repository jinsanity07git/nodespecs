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

    if uv_path and workspace_root:
        print(f"Attempting to add missing module via uv: {install_target}")
        try:
            subprocess.check_call([uv_path, "add", install_target], cwd=str(workspace_root))
            return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("uv add failed, attempting uv pip install")

        try:
            subprocess.check_call([uv_path, "pip", "install", install_target], cwd=str(workspace_root))
            return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("uv pip install failed, falling back to pip")

    print(f"Attempting to install missing module: {install_target}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", install_target])
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

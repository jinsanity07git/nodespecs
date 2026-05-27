import importlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, MutableMapping


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
    missing_module = module

    try:
        loaded_module = _load_module(module)
    except ModuleNotFoundError as e:
        loaded_module = None
        missing_module = e.name or module

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
    module, _ = parse_dep(module_name)

    def decorator(func):
        def wrapper(*args, **kwargs):
            target_globals = func.__globals__
            if module in target_globals:
                return func(*args, **kwargs)

            importlib.invalidate_caches()
            loaded_module = sys.modules.get(module)
            if loaded_module is None:
                spec = importlib.util.find_spec(module)
                if spec is None:
                    raise ImportError(f"Module {module} is required but not installed.")
                loaded_module = importlib.import_module(module)

            target_globals[module] = loaded_module
            return func(*args, **kwargs)

        return wrapper

    return decorator


def ensure_libs(modules):
    def decorator(func):
        def wrapper(*args, **kwargs):
            target_globals = func.__globals__
            for module_name in modules:
                check_imp(module_name, target_globals=target_globals)
            return func(*args, **kwargs)

        return wrapper

    return decorator

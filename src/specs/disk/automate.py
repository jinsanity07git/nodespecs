import os
from pathlib import Path
import shutil

def resolve_user_path(folder='Downloads'):
    """
    resolve path to the Downloads folder 
    """
    home_dir = os.path.expanduser('~')
    path = os.path.join(home_dir,folder )

    if not os.path.exists(path):
        raise FileNotFoundError(f"The path {path} does not exist")
        
    return path

def resolve_target_url(sepdir, relurl):
    """
    Generates the target URL based on a working directory --sepdir 
    and the provided relative URL --relurl.
    """
    target_path = Path(Path(os.getcwd().split(sepdir)[0]), 
                                      Path(f"{sepdir}/{relurl}"))
    if target_path.parent.exists():  
        return target_path.as_posix()
    else:
        raise FileNotFoundError(f"Directory does not exist: {target_path.parent}")

import importlib.util
from pathlib import Path
from typing import Any, Dict

def load_module_from_path(module_name: str, file_path: Path) -> Any:
    """
    Dynamically load a Python module from a file path.
    Aviod going deep through the __init__ process
    
    Args:
        module_name: Name to assign to the loaded module
        file_path: Path to the Python file to load
        
    Returns:
        The loaded module object
        
    Raises:
        FileNotFoundError: If the module file doesn't exist
        ImportError: If the module cannot be loaded or executed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Module file not found: {file_path}")
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        raise ImportError(f"Failed to load module {module_name} from {file_path}: {e}")




def list_files_and_dirs(root_dir="./",separator=' '):
    """
    List all files and directories in the given directory tree.
    """

    for root, dirs, files in os.walk(root_dir):
        level = root.replace(root_dir, '').count(os.sep)
        indent = separator * 4 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = separator * 4 * (level + 1)
        for f in files:
            print(f'{sub_indent}{f}')

def organize_folder(folder):
    print (folder)
    file_types = {
        'Images': ['.jpeg', '.jpg', '.png', '.gif','.ico','.svg','.webp'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac'],
        'Videos': ['.mp4', '.avi', '.mov'],
        'Documents': ['.pdf', '.docx', '.txt','.html','.xlsx',
                      ".mobi",".epub"],
        'Develops': ['.csv', '.py', '.json','.log',".vr",'.bin','.ipynb'],
        'Installer': ['.exe','.msi','.application','.ps1'],
        'Archives': ['.zip', '.rar','.tar.gz' ,'.7z'],
    }

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            for folder_name, extensions in file_types.items():
                if ext in extensions:
                    target_folder = os.path.join(folder, folder_name)
                    os.makedirs(target_folder, exist_ok=True)
                    shutil.move(file_path, os.path.join(target_folder, filename))
                    print(f'- Moved {filename:<40} to {folder_name:<40}')
if __name__ == "__main__":
    # furl=resolve_path()
    # organize_folder(furl)
    list_files_and_dirs()
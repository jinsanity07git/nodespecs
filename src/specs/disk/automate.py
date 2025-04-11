import os
import shutil

def resolve_path():
    username = os.getlogin() 
    if os.name == 'nt':  # Windows
        path = f"C:/Users/{username}/Downloads"
    elif os.name == 'posix':  # MacOS/Linux
        home_dir = os.path.expanduser('~')
        path = f"{home_dir}/Downloads"
    else:
        raise OSError("Unsupported operating system")

    if not os.path.exists(path):
        raise FileNotFoundError(f"The path {path} does not exist")
        
    return path

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
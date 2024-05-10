import sys
import platform
import os
import subprocess
from pprint import pprint


def detect_environment():
    if 'JPY_PARENT_PID' in os.environ:
        return "JupyterNotebook"
    if 'VSCODE_PID' in os.environ :
        return "VSCode"
    if 'PYCHARM_HOSTED' in os.environ:
        return "PyCharm"
    return "Unknown or standard Python"

def environment_check():
    try:
        from pprint import pprint
        from IPython import get_ipython
        shell = get_ipython()
        if shell is None:
            return "standard Python script"
        shell_name = shell.__class__.__name__
        if shell_name == 'ZMQInteractiveShell':
            return f"ZMQ_{detect_environment()}"  
        elif shell_name == 'TerminalInteractiveShell':
            return "IPython shell"
        elif shell_name == 'Shell':
            if "colab" in  str(shell.__class__):
                return "GoogleColabShell"
            else:
                return "Python IDLE"
        else:
            return f"Other: {shell_name}"
    except ImportError:
        return "Not IPython environment"

def find_python_interpreters():
    try:
        # Running the 'where' command to find all occurrences of python.exe
        result = subprocess.check_output("where python", shell=True)
        interpreters = result.decode().strip().split('\n')
        return interpreters
    except subprocess.CalledProcessError:
        return []


if __name__ == "__main__":
    print (sys.executable)
    platform.python_branch()
    platform.python_compiler()
    platform.python_implementation()
    platform.architecture()

    # List the found Python interpreters
    pprint(find_python_interpreters())

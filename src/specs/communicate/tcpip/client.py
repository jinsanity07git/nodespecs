import socket
import os
import time

from .protocol import send_file_header


def get_progress():
    try:
        from tqdm import tqdm
        return tqdm
    except ModuleNotFoundError:
        return None

def send_file(client_socket, file_path, prg=False):
    # Send the file name
    file_name = os.path.basename(file_path)
    file_size = send_file_header(client_socket, file_path)

    # Send the file content
    tqdm = get_progress()
    tqdm_progress = None
    if prg and tqdm is not None:
        tqdm_progress = tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Sending {file_name}")

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)
            if tqdm_progress is not None:
                tqdm_progress.update(len(data))

    if tqdm_progress is not None:
        tqdm_progress.close()
    print(f"File {file_name:<35} has been sent.")

def client(server_ip, server_port=12345, file_path="./README.md", prg=False):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    try:
        send_file(client_socket, file_path, prg)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
    return None

def clientd(server_ip, server_port=12345, parentdir="./", prg=True):
    """
    client upload top level files in the cwd
    """
    # Create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    try:
        for chiddir, foldernames, files in os.walk(parentdir):
            if chiddir == parentdir:
                for file in files:
                    file_path = os.path.join(chiddir, file)
                    # print(f"***Preparing*** {file_path}")
                    send_file(client_socket, file_path, prg)
                    # print(f"***Done*** {file_path}")
                    time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Uncomment to run the server
# server()

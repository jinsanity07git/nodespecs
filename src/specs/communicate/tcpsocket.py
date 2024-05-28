import socket
import os
import signal
import sys

# Global variable to track the server socket
server_socket = None

def handle_signal(sig, frame):
    print("\nReceived interrupt signal, shutting down server...")
    if server_socket:
        server_socket.close()
    sys.exit(0)

def server(save_path='./'):
    global server_socket
    
    # Ensure the directory for saving files exists
    os.makedirs(save_path, exist_ok=True)

    # Creating a dummy socket to find the local IP address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # Google's DNS server
        local_ip = s.getsockname()[0]

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((local_ip, 12345))  # Bind to the local IP address found
    server_socket.listen(1)
    server_socket.settimeout(1)  # Set a timeout to make the socket non-blocking
    print("Listening on", server_socket.getsockname())

    # Set up signal handling
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print('Connection from', addr)

            try:
                while True:
                    # Receive the file name size
                    file_name_size = client_socket.recv(4)
                    if not file_name_size:
                        break
                    file_name_size = int.from_bytes(file_name_size, 'big')

                    # Receive the file name
                    file_name = client_socket.recv(file_name_size).decode()
                    full_path = os.path.join(save_path, file_name)

                    # Receive the file size
                    file_size = client_socket.recv(8)
                    file_size = int.from_bytes(file_size, 'big')

                    # Receive the file content
                    with open(full_path, 'wb') as f:
                        received = 0
                        while received < file_size:
                            data = client_socket.recv(1024)
                            if not data:
                                break
                            f.write(data)
                            received += len(data)

                    print(f"File {file_name} has been received and saved.")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                client_socket.close()
        except socket.timeout:
            # Continue the loop to check for interrupt signal
            continue

# Uncomment to run the server
# server()

def check_prg():
    import sys
    import subprocess
    try:
        from tqdm import tqdm
        return True
    except ModuleNotFoundError as e:
        # Extract the name of the missing module
        missing_module = str(e).split("'")[1]
        print(f"Attempting to install missing module: {missing_module}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", missing_module])
        return False

def send_file(client_socket, file_path, prg=False):
    # Send the file name
    file_name = os.path.basename(file_path)
    file_name_size = len(file_name).to_bytes(4, 'big')
    client_socket.sendall(file_name_size)
    client_socket.sendall(file_name.encode())

    # Send the file size
    file_size = os.path.getsize(file_path)
    client_socket.sendall(file_size.to_bytes(8, 'big'))

    # Send the file content
    prgenv = not prg
    while not prgenv:
        prgenv = check_prg()
    if prgenv & prg:
        from tqdm import tqdm
        tqdm_progress = tqdm(total=file_size, unit='B', unit_scale=True, desc=f'Sending {file_name}')

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)
            if prg: tqdm_progress.update(len(data))
    
    if prg: tqdm_progress.close()
    print(f"File {file_name:<35} has been sent.")

def client(server_ip, server_port, file_path="./README.md", prg=False):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    try:
        send_file(client_socket, file_path, prg)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
    return None

def clientd(server_ip, server_port, parentdir="./", prg=True):
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
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Uncomment to run the server
# server()

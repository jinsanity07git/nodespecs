import socket
import os

def server(save_path = './'):
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
    print("Listening on", server_socket.getsockname())

    while True:
        client_socket, addr = server_socket.accept()
        print('Connection from', addr)

        # Receiving the file name
        file_name = client_socket.recv(1024).decode()
        full_path = os.path.join(save_path, file_name)

        # Receiving the file content
        with open(full_path, 'wb') as f:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)

        print(f"File {file_name} has been received and saved.")
        client_socket.close()


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


def client(server_ip, server_port, file_path,prg = False):
    # Create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    # Send the file name
    file_name = os.path.basename(file_path)
    client_socket.sendall(file_name.encode())

    # Send the file content
    file_size = os.path.getsize(file_path)

    prgenv = not prg
    while not prgenv:
        prgenv = check_prg()
    if prgenv & prg:
        from tqdm import tqdm
        tqdm_progress = tqdm(total=file_size, unit='B', unit_scale=True, desc='Sending')

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)
            if prg: tqdm_progress.update(len(data))
    
    if prg: tqdm_progress.close()
    print("File has been sent.")
    client_socket.close()

# Example usage:
# client('192.168.1.2', 12345, 'path_to_your_file.txt')

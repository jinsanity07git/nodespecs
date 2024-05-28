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
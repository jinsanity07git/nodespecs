import os


def send_file_header(sock, file_path: str) -> int:
    file_name = os.path.basename(file_path)
    file_name_size = len(file_name.encode("utf-8")).to_bytes(4, "big")
    sock.sendall(file_name_size)
    sock.sendall(file_name.encode("utf-8"))

    file_size = os.path.getsize(file_path)
    sock.sendall(file_size.to_bytes(8, "big"))
    return file_size


def recv_all(sock, length: int) -> bytes:
    data = b""
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before receiving all data")
        data += more
    return data


def receive_file_header(sock):
    file_name_size_data = recv_all(sock, 4)
    file_name_size = int.from_bytes(file_name_size_data, "big")

    file_name_data = recv_all(sock, file_name_size)
    file_name = file_name_data.decode("utf-8")

    file_size_data = recv_all(sock, 8)
    file_size = int.from_bytes(file_size_data, "big")
    return file_name, file_size

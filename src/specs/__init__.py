from .hardware import ensure_libs, info_gpu
# Version of the node-specs package
__version__ = "0.2.2"

__all__ = [
    "ensure_libs",
    "info_gpu",
    "__version__",
    "bench_cpu",
    "info_plat",
    "server",
    "client",
    "clientd",
    "whoish",
    "derive_uid",
    "environment_check",
]


def bench_cpu():
    from .benchmark import bench_cpu as _bench_cpu

    return _bench_cpu()


def info_plat():
    from .benchmark import info_plat as _info_plat

    return _info_plat()


def server():
    from .communicate.tcpip.server import server as _server

    return _server()


def client(server_ip, server_port=12345, file_path="./README.md", prg=False):
    from .communicate.tcpip.client import client as _client

    return _client(server_ip, server_port, file_path, prg)


def clientd(server_ip, server_port=12345, parentdir="./", prg=True):
    from .communicate.tcpip.client import clientd as _clientd

    return _clientd(server_ip, server_port, parentdir, prg)


def whoish():
    from .communicate.aboutme import whoish as _whoish

    return _whoish()


def derive_uid():
    from .communicate.aboutme import derive_uid as _derive_uid

    return _derive_uid()


def environment_check():
    from .pyinfo import environment_check as _environment_check

    return _environment_check()


#Be ready to enjoy your python code--UTB
# https://www.thepythoncode.com/article/get-hardware-system-information-python
#

import platform
import shutil
from datetime import datetime

from .deps import ensure_lib, ensure_libs


def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def info_sys():
    print("=" * 40, "System Information", "=" * 40)
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Node Name: {uname.node}")
    print(f"Release: {uname.release}")
    print(f"Version: {uname.version}")
    print(f"Machine: {uname.machine}")
    print(f"Processor: {uname.processor}")


@ensure_lib("psutil")
def get_system_info():
    cpu_count = psutil.cpu_count(logical=True)
    memory_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)

    # Get storage information
    storage_info = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            storage_info.append(
                f"{partition.device} ({partition.fstype}): {round(usage.total / (1024 ** 3), 2)}GB"
            )
        except Exception:
            pass
    cpu_count = psutil.cpu_count(logical=True)

    print(f"vCPUs : {cpu_count}")
    print(f"Memory: {memory_gb} GB")
    print("Storage:")
    unique_devices = {}
    total_storage = 0
    for info in storage_info:
        device = info.split()[0]  # Get device name
        if device not in unique_devices:
            unique_devices[device] = info
            # Extract the storage number (GB) from the info string
            storage_gb = float(info.split()[-1].replace("GB", ""))
            total_storage += storage_gb
    for info in unique_devices.values():
        print(f"***  {info}")
    print(f"Total Storage: {total_storage:.2f} GB")

    return cpu_count, memory_gb, storage_info


@ensure_lib("psutil")
def boot_time():
    # Boot Time
    print("=" * 40, "Boot Time", "=" * 40)
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    print(f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}")


@ensure_lib("psutil")
def info_cpu():
    # let's print CPU information
    print("=" * 40, "CPU Info", "=" * 40)
    from .. import cpuinfo

    print("CPU: " + cpuinfo.get_cpu_info().get("brand_raw", "Unknown"))
    # number of cores
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))
    try:
        # CPU frequencies
        cpufreq = psutil.cpu_freq()
        print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
        print(f"Min Frequency: {cpufreq.min:.2f}Mhz")
        print(f"Current Frequency: {cpufreq.current:.2f}Mhz")
        # CPU usage
        print("CPU Usage Per Core:")
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            print(f"{f'Core':>8} {i:>2}: {percentage :>6}%")
        print(f"Total CPU Usage: {psutil.cpu_percent()}%")
    except FileNotFoundError:
        pass


@ensure_lib("psutil")
def info_mem():
    # Memory Information
    print("=" * 40, "Memory Information", "=" * 40)
    # get the memory details
    svmem = psutil.virtual_memory()
    print(f"Total: {get_size(svmem.total)}")
    print(f"Available: {get_size(svmem.available)}")
    print(f"Used: {get_size(svmem.used)}")
    print(f"Percentage: {svmem.percent}%")
    print("=" * 20, "SWAP", "=" * 20)
    # get the swap memory details (if exists)
    swap = psutil.swap_memory()
    print(f"Total: {get_size(swap.total)}")
    print(f"Free: {get_size(swap.free)}")
    print(f"Used: {get_size(swap.used)}")
    print(f"Percentage: {swap.percent}%")


def info_disk():
    # Disk Information
    print("=" * 40, "Disk Information", "=" * 40)
    print("Partitions and Usage:")
    # get all disk partitions
    partitions = psutil.disk_partitions()
    for partition in partitions:
        print(f"=== Device: {partition.device} ===")
        print(f"  Mountpoint: {partition.mountpoint}")
        print(f"  File system type: {partition.fstype}")
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue
        print(f"  Total Size: {get_size(partition_usage.total)}")
        print(f"  Used: {get_size(partition_usage.used)}")
        print(f"  Free: {get_size(partition_usage.free)}")
        print(f"  Percentage: {partition_usage.percent}%")
    # get IO statistics since boot
    disk_io = psutil.disk_io_counters()
    print(f"Total read: {get_size(disk_io.read_bytes)}")
    print(f"Total write: {get_size(disk_io.write_bytes)}")


@ensure_lib("psutil")
def info_net():
    # Network information
    print("=" * 40, "Network Information", "=" * 40)
    # get all network interfaces (virtual and physical)
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            print(f"=== Interface: {interface_name} ===")
            if str(address.family) == "AddressFamily.AF_INET":
                print(f"  IP Address: {address.address}")
                print(f"  Netmask: {address.netmask}")
                print(f"  Broadcast IP: {address.broadcast}")
            elif str(address.family) == "AddressFamily.AF_PACKET":
                print(f"  MAC Address: {address.address}")
                print(f"  Netmask: {address.netmask}")
                print(f"  Broadcast MAC: {address.broadcast}")
    # get IO statistics since boot
    net_io = psutil.net_io_counters()
    print(f"Total Bytes Sent: {get_size(net_io.bytes_sent)}")
    print(f"Total Bytes Received: {get_size(net_io.bytes_recv)}")


def info_gpu():
    """Print a table of NVIDIA GPUs detected on the host.

    Degrades gracefully — never raises — if:
      * nvidia-smi is not on PATH (no NVIDIA driver, or non-NVIDIA host)
      * GPUtil or tabulate cannot be loaded (deps missing or transitive
        stdlib-removed import, e.g. `from distutils import spawn` on 3.12 —
        see issue #5)
      * nvidia-smi runs but reports zero GPUs

    The nvidia-smi probe runs *before* the GPUtil/tabulate install attempt
    so that on a host with no NVIDIA GPU we never trigger a `pip install
    GPUtil` (which would fail on a no-pip venv and surface a stack trace).
    """
    from .deps import check_imp

    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        print(
            "No NVIDIA GPU detected (nvidia-smi not found in PATH). "
            "Skipping GPU info."
        )
        return

    for module in ("GPUtil", "tabulate"):
        try:
            check_imp(module, target_globals=globals())
        except ImportError as e:
            print(
                f"GPU utilities unavailable: {e}. "
                "Run 'uv pip install GPUtil tabulate' to enable."
            )
            return

    try:
        gpus = GPUtil.getGPUs()
    except Exception as e:
        print(f"GPU utilities unavailable: failed to query nvidia-smi ({e}).")
        return

    if not gpus:
        print("No NVIDIA GPUs reported by nvidia-smi.")
        return

    list_gpus = [
        (
            gpu.id,
            gpu.name,
            f"{gpu.load * 100}%",
            f"{gpu.memoryFree}MB",
            f"{gpu.memoryUsed}MB",
            f"{gpu.memoryTotal}MB",
            f"{gpu.temperature} °C",
            gpu.uuid,
        )
        for gpu in gpus
    ]

    print("=" * 40, "GPU Details", "=" * 40)
    print(
        tabulate(
            list_gpus,
            headers=(
                "id",
                "name",
                "load",
                "free memory",
                "used memory",
                "total memory",
                "temperature",
                "uuid",
            ),
        )
    )


if __name__ == "__main__":
    boot_time()
    info_sys()
    info_cpu()
    info_mem()
    # info_gpu()

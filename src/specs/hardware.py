#Be ready to enjoy your python code--UTB
# https://www.thepythoncode.com/article/get-hardware-system-information-python
#

import platform
from datetime import datetime
import importlib

def parse_dep(module_name):
    sep = "=="
    if sep in module_name:
        module, version = [ i.strip() for i in module_name.split(sep)]
    else:
        module, version = module_name,None
        
    debug = 0
    if debug:
        print (f"module_name {module}, {version}")
    return module, version

def check_imp(module_name):
    import sys
    import subprocess
    try:
        module, version = parse_dep(module_name)
        globals()[module] = importlib.import_module(module)
        return True
    except ModuleNotFoundError as e:
        # Extract the name of the missing module
        missing_module = str(e).split("'")[1]
        print(f"Attempting to install missing module: {missing_module}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", missing_module])
        return False


def ensure_lib(module_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if module_name not in globals():
                check_imp(module_name)
                try:
                    globals()[module_name] = importlib.import_module(module_name)
                except ImportError:
                    raise ImportError(f"Module {module_name} is required but not installed.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def ensure_libs(modules):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for module_name in modules:
                check_imp(module_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator


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
    print("="*40, "System Information", "="*40)
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Node Name: {uname.node}")
    print(f"Release: {uname.release}")
    print(f"Version: {uname.version}")
    print(f"Machine: {uname.machine}")
    print(f"Processor: {uname.processor}")

@ensure_lib('psutil')
def get_system_info():
  cpu_count = psutil.cpu_count(logical=True)
  memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
  
  # Get storage information
  storage_info = []
  for partition in psutil.disk_partitions():
    try:
      usage = psutil.disk_usage(partition.mountpoint)
      storage_info.append(f"{partition.device} ({partition.fstype}): {round(usage.total / (1024**3), 2)}GB")
    except:
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
          storage_gb = float(info.split()[-1].replace('GB', ''))
          total_storage += storage_gb
  for info in unique_devices.values():
      print(f"***  {info}")
  print(f"Total Storage: {total_storage:.2f} GB")

  return cpu_count, memory_gb, storage_info

@ensure_lib('psutil')
def boot_time():
    # Boot Time
    print("="*40, "Boot Time", "="*40)
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    print(f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}")

@ensure_lib('psutil')
def info_cpu():
    # let's print CPU information
    print("="*40, "CPU Info", "="*40)
    from . import cpuinfo
    print('CPU: ' + cpuinfo.get_cpu_info().get('brand_raw', "Unknown"))
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

@ensure_lib('psutil')
def info_mem():
    # Memory Information
    print("="*40, "Memory Information", "="*40)
    # get the memory details
    svmem = psutil.virtual_memory()
    print(f"Total: {get_size(svmem.total)}")
    print(f"Available: {get_size(svmem.available)}")
    print(f"Used: {get_size(svmem.used)}")
    print(f"Percentage: {svmem.percent}%")
    print("="*20, "SWAP", "="*20)
    # get the swap memory details (if exists)
    swap = psutil.swap_memory()
    print(f"Total: {get_size(swap.total)}")
    print(f"Free: {get_size(swap.free)}")
    print(f"Used: {get_size(swap.used)}")
    print(f"Percentage: {swap.percent}%")

def info_disk():
    # Disk Information
    print("="*40, "Disk Information", "="*40)
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

@ensure_lib('psutil')
def info_net():
    # Network information
    print("="*40, "Network Information", "="*40)
    # get all network interfaces (virtual and physical)
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            print(f"=== Interface: {interface_name} ===")
            if str(address.family) == 'AddressFamily.AF_INET':
                print(f"  IP Address: {address.address}")
                print(f"  Netmask: {address.netmask}")
                print(f"  Broadcast IP: {address.broadcast}")
            elif str(address.family) == 'AddressFamily.AF_PACKET':
                print(f"  MAC Address: {address.address}")
                print(f"  Netmask: {address.netmask}")
                print(f"  Broadcast MAC: {address.broadcast}")
    # get IO statistics since boot
    net_io = psutil.net_io_counters()
    print(f"Total Bytes Sent: {get_size(net_io.bytes_sent)}")
    print(f"Total Bytes Received: {get_size(net_io.bytes_recv)}")

def check_gpu():
    import sys
    import subprocess
    try:
        import GPUtil
        from tabulate import tabulate
        return True
    except ModuleNotFoundError as e:
        # Extract the name of the missing module
        missing_module = str(e).split("'")[1]
        print(f"Attempting to install missing module: {missing_module}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", missing_module])
        return False

def info_gpu():
    gpuenv = False
    while not gpuenv:
        gpuenv = check_gpu()

    if gpuenv:
        import GPUtil
        from tabulate import tabulate
        print("="*40, "GPU Details", "="*40)
        gpus = GPUtil.getGPUs()
        list_gpus = []
        for gpu in gpus:
            # get the GPU id
            gpu_id = gpu.id
            # name of GPU
            gpu_name = gpu.name
            # get % percentage of GPU usage of that GPU
            gpu_load = f"{gpu.load*100}%"
            # get free memory in MB format
            gpu_free_memory = f"{gpu.memoryFree}MB"
            # get used memory
            gpu_used_memory = f"{gpu.memoryUsed}MB"
            # get total memory
            gpu_total_memory = f"{gpu.memoryTotal}MB"
            # get GPU temperature in Celsius
            gpu_temperature = f"{gpu.temperature} °C"
            gpu_uuid = gpu.uuid
            list_gpus.append((
                gpu_id, gpu_name, gpu_load, gpu_free_memory, gpu_used_memory,
                gpu_total_memory, gpu_temperature, gpu_uuid
            ))

        print(tabulate(list_gpus, headers=("id", "name", "load", "free memory", "used memory", "total memory",
                                        "temperature", "uuid")))
        

if __name__ == "__main__":
    boot_time()
    info_sys()
    info_cpu()
    info_mem()
    # info_gpu()
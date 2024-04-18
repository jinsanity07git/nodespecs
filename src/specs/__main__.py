import sys

from .hardware import (info_cpu,
                       info_mem,
                       info_disk,
                       info_net)

def main():
    info_cpu()
    info_mem()
    info_disk()
    info_net()

if __name__ == "__main__":
    main()
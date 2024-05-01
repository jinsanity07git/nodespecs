import sys
import argparse

from .hardware import (info_cpu,
                       info_mem,
                       info_disk,
                       info_net)

from .hardware import (info_sys,
                       info_mem,
                       info_disk,
                       info_net)
from . import info_plat
def main():
    parser = argparse.ArgumentParser(description="Display hardware information")
    parser.add_argument('-l','--lite',default=0, help='Display native python platform')

    args = parser.parse_args()
    if (args.lite == "1") or (args.lite == "True") :
        info_sys()
        info_plat()
    else:
        info_cpu()
        info_mem()
        info_disk()
        info_net()

if __name__ == "__main__":
    main()
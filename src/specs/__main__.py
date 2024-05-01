import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Display hardware information")
    parser.add_argument('-l','--lite',default=0, help='Display native python platform')
    parser.add_argument('-u','--utility',default=None, help='run benchmark for single core CPU')

    args = parser.parse_args()
    if args.utility is None:
        if (args.lite == "1") or (args.lite == "True") :
            from . import info_plat
            info_plat()
        else:
            from .hardware import (info_cpu,
                                   info_mem,
                                   info_disk,
                                   info_net)
            info_cpu()
            info_mem()
            info_disk()
            info_net()
    else:
        if args.utility == "bcpu":
            from . import bench_cpu
            bench_cpu()



if __name__ == "__main__":
    main()
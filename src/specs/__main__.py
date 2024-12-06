import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Display hardware information")
    parser.add_argument('-v','--version',action='store_true', help='Display the version info')
    parser.add_argument('-l','--lite',default=0, help='Display native python platform')
    parser.add_argument('-u','--utility',default=None, help='run benchmark for single core CPU')
    parser.add_argument('-i','--iphost',default=None, help='hosthame of the server machine')

    args = parser.parse_args()
    if args.utility is None:
        if (args.lite == "1") or (args.lite == "True") :
            from . import info_plat
            info_plat()
        elif args.version:
            from . import __version__
            print(__version__)
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
        elif args.utility == "fclean":
            from .disk import organize_folder,resolve_path
            furl=resolve_path()
            organize_folder(furl)
        elif args.utility == "upload":
            from .communicate import stream_files
            from . import whoish
            whoish()
            stream_files()
        elif args.utility == "server":
            from . import server
            server()
        elif args.utility == "cld":
            from . import clientd
            if args.iphost is not None:
                clientd(args.iphost)



if __name__ == "__main__":
    main()
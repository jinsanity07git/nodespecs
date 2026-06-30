import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Display hardware information")
    parser.add_argument("-v", "--version", action="store_true", help="Display the version info")
    parser.add_argument("-l", "--lite", default=0, help="Display native python platform")
    parser.add_argument("-u", "--utility", default=None, help="run benchmark for single core CPU")
    parser.add_argument("-i", "--iphost", default=None, help="hosthame of the server machine")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("bcpu", help="run CPU benchmark")

    fclean = subparsers.add_parser("fclean", help="clean and organize downloads folder")
    fclean.add_argument(
        "--folder",
        default="Downloads",
        help="Folder name under the user home directory",
    )

    subparsers.add_parser("upload", help="start streaming upload server")
    subparsers.add_parser("server", help="start TCP file server")

    subparsers.add_parser("cld", help="upload top-level files to server")

    return parser


def _run_default(args) -> int:
    if (args.lite == "1") or (args.lite == "True"):
        from .benchmark import info_plat

        info_plat()
        return 0

    if args.version:
        from . import __version__

        print(__version__)
        return 0

    from .hardware import get_system_info

    get_system_info()
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command or args.utility
    if command is None:
        return _run_default(args)

    if command == "bcpu":
        from .benchmark import bench_cpu

        bench_cpu()
        return 0

    if command == "fclean":
        from .disk import organize_folder, resolve_user_path

        folder = getattr(args, "folder", "Downloads")
        target_dir = resolve_user_path(folder)
        organize_folder(target_dir)
        return 0

    if command == "upload":
        from .communicate import stream_files
        from .communicate.aboutme import whoish

        whoish()
        stream_files()
        return 0

    if command == "server":
        from .communicate.tcpip.server import server

        server()
        return 0

    if command == "cld":
        iphost = args.iphost
        if not iphost:
            parser.error("iphost is required for cld")

        from .communicate.tcpip.client import clientd

        clientd(iphost)
        return 0

    parser.error(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI entry point: index a directory and export results to SQLite.

Default ``--dir`` is the current working directory on non-Windows hosts
and ``F:\\`` on Windows (matching the package's primary use case on the
maintainer's Windows desktop). On a non-Windows host, ``F:\\`` does
not exist and the default would fail with exit code 2, so we fall back
to ``Path.cwd()``.

After indexing, prints a side-by-side comparison of the indexer's
``on_disk_size`` and the OS-reported ``shutil.disk_usage()`` so the
gap (filesystem metadata, snapshots, unread subtrees) is visible
instead of hidden.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

from .indexer import FileIndexer

# Default to F:\\ on Windows (legacy behavior, used by the maintainer)
# and the current working directory everywhere else so the CLI is
# runnable on Linux/macOS without a hardcoded path crash.
if os.name == "nt":
    DEFAULT_ROOT_DIR = Path(r"F:\\")
else:
    DEFAULT_ROOT_DIR = Path.cwd()


def _format_bytes(n: int) -> str:
    """Right-aligned byte count with thousands separators."""
    return f"{n:>14,}"


def _is_volume_root(p: Path) -> bool:
    """Return True if ``p`` is the mount root of its containing volume.

    On POSIX, the only mount root is ``/``. On Windows, any drive
    letter at its root (e.g. ``C:\\``) counts. Used to disambiguate
    the comparison line in ``_print_comparison`` so the gap between
    the indexer's on-disk size and ``shutil.disk_usage`` is attributed
    correctly: when the indexed directory is a subtree, the gap is
    mostly "files outside the indexed directory"; when it is the
    volume root, the gap is filesystem metadata + unread subtrees.
    """
    if p == p.anchor:
        return True
    # Path.anchor on Windows is 'C:\\'; ``Path('C:\\').parent == Path('C:\\')``.
    return p.parent == p


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Index a directory and export results to a SQLite database. "
            "Prints a side-by-side comparison with shutil.disk_usage() "
            "so on-disk accounting gaps are visible."
        )
    )
    parser.add_argument(
        "--dir",
        dest="root_dir",
        default=str(DEFAULT_ROOT_DIR),
        help=(
            "Root directory to index. "
            f"Default: {DEFAULT_ROOT_DIR}"
        ),
    )
    parser.add_argument(
        "--db",
        dest="db_path",
        default=None,
        help="Optional SQLite database file path. Defaults to <dir>/file_index.db",
    )
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"Directory does not exist: {root_dir}", file=sys.stderr)
        return 2

    indexer = FileIndexer()
    indexer.index_directory(str(root_dir))

    db_path = Path(args.db_path) if args.db_path else root_dir / "file_index.db"
    success, error = indexer.export_to_sqlite(str(db_path))
    if not success:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1

    print(f"Successfully exported to SQLite database: {db_path}")
    _print_comparison(indexer, root_dir)
    return 0


def _print_comparison(indexer: FileIndexer, root_dir: Path) -> None:
    """Print indexer stats and the OS-reported disk usage side by side."""
    stats = indexer.get_statistics()
    print(
        f"Indexed {stats['total_files']} files "
        f"({stats['unique_files']} unique inodes)"
    )
    print(f"  logical size:    {_format_bytes(stats['logical_size'])} bytes")
    print(
        f"  on-disk size:    {_format_bytes(stats['on_disk_size'])} bytes  "
        "(deduped by inode; accounts for cluster rounding + sparse files)"
    )
    print(
        f"  hardlink paths:  {_format_bytes(stats['hardlink_extra_paths'])} "
        "(extra paths sharing an inode)"
    )
    print(
        f"  skipped:         {_format_bytes(stats['skipped_paths'])} "
        "(permission / access errors during walk)"
    )
    try:
        du = shutil.disk_usage(str(root_dir))
    except (OSError, AttributeError) as e:
        print(f"\n(could not read OS disk usage: {e})")
        return
    is_vol_root = _is_volume_root(root_dir)
    if is_vol_root:
        scope = f"OS-reported usage of {root_dir} (volume root):"
    else:
        scope = (
            f"OS-reported usage of the volume containing {root_dir} "
            "(indexer covers this subtree only):"
        )
    print(f"\n{scope}")
    print(f"  total:           {_format_bytes(du.total)} bytes")
    print(f"  used:            {_format_bytes(du.used)} bytes")
    print(f"  free:            {_format_bytes(du.free)} bytes")
    gap = du.used - stats["on_disk_size"]
    if is_vol_root:
        gap_label = (
            "metadata, system files, unread subtrees, snapshots"
        )
    else:
        gap_label = (
            "includes every file outside the indexed subtree, plus "
            "metadata, snapshots, etc."
        )
    print(
        f"  OS - indexer:    {_format_bytes(gap)} bytes  "
        f"({gap_label})"
    )


if __name__ == "__main__":
    raise SystemExit(main())

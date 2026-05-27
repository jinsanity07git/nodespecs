import argparse
import sys
from pathlib import Path

from .indexer import FileIndexer
DEFAULT_ROOT_DIR = r"F:\\"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index a directory and export results to a SQLite database."
    )
    parser.add_argument(
        "--dir",
        dest="root_dir",
        default=DEFAULT_ROOT_DIR,
        help=(
            "Root directory to index. Default is a raw Windows path literal: "
            f"{DEFAULT_ROOT_DIR}"
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
    indexed_count = indexer.index_directory(str(root_dir))
    print(f"Indexed {indexed_count} files")

    db_path = Path(args.db_path) if args.db_path else root_dir / "file_index.db"
    success, error = indexer.export_to_sqlite(str(db_path))
    if success:
        print(f"Successfully exported to SQLite database: {db_path}")
        return 0

    print(f"Export failed: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
    
    # from pprint import pprint
    # pprint(indexer.files)
    # # Search for files
    # results = indexer.search(
    #     pattern="document",
    #     exact_match=False,
    #     extensions=[".png",".md"],
    #     min_size=1  # 1KB
    # )
    
    # # Print results
    # for filepath, filename, size in results:
    #     print(f"Found: {filename} ({size:,} bytes) at {filepath}")
    
    # # Get statistics
    # stats = indexer.get_statistics()
    # print(f"\nIndexing Statistics:")
    # print(f"Total Files: {stats['total_files']:,}")
    # print(f"Total Size: {stats['total_size']:,} bytes")
    # print(f"Unique Extensions: {stats['unique_extensions']}")
    # print("\nTop Extensions:")
    # for ext, count in stats['top_extensions']:
    #     print(f"{ext or '(no extension)'}: {count:,} files")

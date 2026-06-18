"""Recursive filesystem indexer with on-disk size accounting.

The ``FileIndexer`` walks a directory tree and produces:

* an in-memory mapping of filepath -> file metadata (logical size,
  on-disk usage in 512-byte blocks, hardlink count, inode, device),
* aggregate statistics including an inode-deduped on-disk usage that
  approximates the OS-reported "used space" for a file walk.

Why a dedicated ``on_disk_size`` and not just ``sum(st_size)``:
  * NTFS / exFAT / many Linux filesystems round every file up to the
    cluster size. The same file can take 4 KB on one volume and 64 KB
    on another, regardless of its logical content. ``st_size`` does
    not capture this. ``st_blocks * 512`` does.
  * Hardlinks share an inode; summing ``st_size`` over every path
    multiplies the same bytes by ``st_nlink``. We dedup by
    ``(st_dev, st_ino)`` and report one copy.
  * Sparse files (VHDs, pagefile, DB files) report huge ``st_size`` but
    little real allocation; ``st_blocks * 512`` captures actual usage.

None of this matches the OS's "used" number exactly: filesystem
metadata (NTFS MFT, journals, $Secure, $Bitmap), system restore
points, shadow copies, the Recycle Bin, the pagefile, hiberfil, and
any subtree the walker could not read (locked directories) all
contribute to "used" but never to a file walk. The CLI in
``specs.disk.drive`` prints both numbers so the gap is visible.
"""
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FileIndexer:
    """Walk a directory tree, capture per-file metadata, expose stats."""

    def __init__(self):
        """Initialize the FileIndexer with in-memory storage and stats."""
        self.files: Dict[str, dict] = {}
        self._reset_stats()

    def _reset_stats(self) -> None:
        """Reset the per-run stats dict (called by index_directory)."""
        self.stats = {
            "total_files": 0,
            "unique_files": 0,
            "total_size": 0,
            "logical_size": 0,
            "on_disk_size": 0,
            "hardlink_extra_paths": 0,
            "skipped_paths": 0,
            "extensions": defaultdict(int),
        }

    def index_directory(self, root_path: str) -> int:
        """
        Recursively index all files from the given root directory.

        Uses an explicit ``os.scandir`` walker so a per-directory
        ``PermissionError`` does not abort the whole walk the way the
        legacy ``os.walk`` did. Symlinks are not followed
        (``follow_symlinks=False``), matching the previous behavior.

        Returns the number of file entries indexed (including
        hardlinked paths, so two hardlinks of one inode count as 2).
        """
        self._reset_stats()

        stack: List[str] = [root_path]
        while stack:
            dirpath = stack.pop()
            try:
                with os.scandir(dirpath) as it:
                    entries = list(it)
            except (OSError, PermissionError) as e:
                print(f"Error scanning {dirpath}: {e}")
                self.stats["skipped_paths"] += 1
                continue

            for entry in entries:
                child = os.path.join(dirpath, entry.name)
                try:
                    if entry.is_file(follow_symlinks=False):
                        self._record_file(child, entry)
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(child)
                    # Symlinks and other entry types are silently skipped
                    # (matches the previous os.walk default).
                except (OSError, PermissionError) as e:
                    print(f"Error accessing {child}: {e}")
                    self.stats["skipped_paths"] += 1

        self._finalize_stats()
        return self.stats["total_files"]

    def _record_file(self, filepath: str, entry: "os.DirEntry") -> None:
        """Stat a single file entry and append to ``self.files`` + ``self.stats``."""
        st = entry.stat(follow_symlinks=False)
        _, ext = os.path.splitext(entry.name)
        ext = ext.lower()
        posix_path = Path(filepath).as_posix()
        self.files[posix_path] = {
            "filepath": posix_path,
            "filename": entry.name,
            "extension": ext,
            "size": st.st_size,
            "on_disk": st.st_blocks * 512,
            "blocks": st.st_blocks,
            "nlinks": st.st_nlink,
            "inode": st.st_ino,
            "device": st.st_dev,
            "last_modified": datetime.fromtimestamp(st.st_mtime),
            "indexed_at": datetime.now(),
        }
        self.stats["total_files"] += 1
        self.stats["total_size"] += st.st_size
        self.stats["extensions"][ext] += 1

    def _finalize_stats(self) -> None:
        """Compute the inode-deduped sums and hardlink counts.

        After ``_record_file`` has populated ``self.files`` and the
        per-path counters, walk the records once and dedup by
        ``(st_dev, st_ino)``. Filesystems that report ``st_ino == 0``
        (some Windows / FAT configurations) cannot be deduped, so each
        path is counted individually in that case; this is documented
        in the module docstring.
        """
        seen: Dict[Tuple[int, int], Tuple[int, int]] = {}
        for info in self.files.values():
            ino = info["inode"]
            dev = info["device"]
            if ino == 0:
                # Indistinguishable inodes — count this path on its own
                # so the total is still an upper bound.
                seen[(dev, id(info))] = (info["on_disk"], info["size"])
            else:
                key = (dev, ino)
                if key not in seen:
                    seen[key] = (info["on_disk"], info["size"])
        self.stats["unique_files"] = len(seen)
        self.stats["on_disk_size"] = sum(o for o, _ in seen.values())
        self.stats["logical_size"] = sum(s for _, s in seen.values())
        self.stats["hardlink_extra_paths"] = (
            self.stats["total_files"] - self.stats["unique_files"]
        )

    def search(
        self,
        pattern: str,
        exact_match: bool = False,
        extensions: List[str] = None,
        min_size: int = None,
        max_size: int = None,
    ) -> List[Tuple[str, str, int]]:
        """
        Search for files matching the given criteria.
        Returns list of tuples containing (filepath, filename, size).
        """
        results = []

        # Compile regex pattern if not exact match
        if not exact_match:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # If pattern is not a valid regex, treat it as literal
                regex = re.compile(re.escape(pattern), re.IGNORECASE)

        # Normalize extensions list
        if extensions:
            extensions = [
                ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
            ]

        for file_info in self.files.values():
            # Check filename match
            if exact_match:
                if pattern.lower() != file_info["filename"].lower():
                    continue
            else:
                if not regex.search(file_info["filename"]):
                    continue

            # Check extension
            if extensions and file_info["extension"] not in extensions:
                continue

            # Check size constraints
            if min_size is not None and file_info["size"] < min_size:
                continue
            if max_size is not None and file_info["size"] > max_size:
                continue

            results.append(
                (
                    file_info["filepath"],
                    file_info["filename"],
                    file_info["size"],
                )
            )

        return sorted(results, key=lambda x: x[1])  # Sort by filename

    def get_statistics(self) -> dict:
        """Return statistics about the indexed files.

        Field guide:
            total_files         -- every regular file seen (incl. hardlinked
                                   paths). Sum of ``st_size`` over these is
                                   ``total_size``, which over-counts hardlinks.
            unique_files        -- distinct inodes counted.
            total_size          -- sum of ``st_size`` across ALL files (kept
                                   for back-compat; inflated by hardlinks).
            logical_size        -- sum of ``st_size`` across distinct inodes.
            on_disk_size        -- sum of ``st_blocks * 512`` across distinct
                                   inodes. Closest file-walking analog of the
                                   OS-reported used space; does not include
                                   filesystem metadata, snapshots, or unread
                                   subtrees.
            hardlink_extra_paths -- ``total_files - unique_files``.
            skipped_paths       -- directory or entry access errors during
                                   the walk.
            unique_extensions   -- distinct file extensions seen.
            top_extensions      -- top 5 extensions by file count.
        """
        top_extensions = sorted(
            self.stats["extensions"].items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_files": self.stats["total_files"],
            "unique_files": self.stats["unique_files"],
            "total_size": self.stats["total_size"],
            "logical_size": self.stats["logical_size"],
            "on_disk_size": self.stats["on_disk_size"],
            "hardlink_extra_paths": self.stats["hardlink_extra_paths"],
            "skipped_paths": self.stats["skipped_paths"],
            "unique_extensions": len(self.stats["extensions"]),
            "top_extensions": top_extensions,
        }

    def export_to_sqlite(self, db_path: str) -> Tuple[bool, Optional[str]]:
        """
        Export the indexed files to a SQLite database.
        Returns a tuple of (success: bool, error_message: Optional[str])
        """
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            return False, f"SQLite error: {str(e)}"

        try:
            cursor = conn.cursor()

            # Create the files table with the new stat columns
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    extension TEXT,
                    size INTEGER,
                    on_disk INTEGER,
                    blocks INTEGER,
                    nlinks INTEGER,
                    inode INTEGER,
                    device INTEGER,
                    last_modified TIMESTAMP,
                    indexed_at TIMESTAMP
                )
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_inode "
                "ON files(device, inode)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_files_ext "
                "ON files(extension)"
            )

            # Create the statistics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS statistics (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """
            )

            # Insert or update file records
            cursor.executemany(
                """
                INSERT OR REPLACE INTO files
                (filepath, filename, extension, size, on_disk, blocks,
                 nlinks, inode, device, last_modified, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        info["filepath"],
                        info["filename"],
                        info["extension"],
                        info["size"],
                        info["on_disk"],
                        info["blocks"],
                        info["nlinks"],
                        info["inode"],
                        info["device"],
                        info["last_modified"].isoformat(),
                        info["indexed_at"].isoformat(),
                    )
                    for info in self.files.values()
                ],
            )

            # Insert statistics
            stats = self.get_statistics()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO statistics (key, value)
                VALUES (?, ?)
            """,
                [
                    ("total_files", str(stats["total_files"])),
                    ("unique_files", str(stats["unique_files"])),
                    ("total_size", str(stats["total_size"])),
                    ("logical_size", str(stats["logical_size"])),
                    ("on_disk_size", str(stats["on_disk_size"])),
                    ("hardlink_extra_paths", str(stats["hardlink_extra_paths"])),
                    ("skipped_paths", str(stats["skipped_paths"])),
                    ("unique_extensions", str(stats["unique_extensions"])),
                    ("top_extensions", repr(stats["top_extensions"])),
                ],
            )

            conn.commit()
            return True, None

        except sqlite3.Error as e:
            return False, f"SQLite error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        finally:
            conn.close()

"""Smoke tests for specs.disk.FileIndexer.

Covers the on-disk / hardlink dedup behavior added in 0.4.1, the
scandir-based walker (per-directory error handling), and the new
columns in the SQLite export. All stdlib; no new deps.
"""
import os
import platform
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from specs.disk import FileIndexer  # noqa: E402


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class FileIndexerBasicTests(unittest.TestCase):
    """Index a small synthetic tree, sanity-check the new stats fields."""

    def test_counts_and_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.txt", b"hello")
            _write(root / "b.txt", b"world!")
            _write(root / "sub" / "c.md", b"abcdef")

            indexer = FileIndexer()
            n = indexer.index_directory(str(root))

            self.assertEqual(n, 3)
            self.assertEqual(indexer.stats["total_files"], 3)
            self.assertEqual(indexer.stats["unique_files"], 3)
            self.assertEqual(indexer.stats["hardlink_extra_paths"], 0)
            self.assertEqual(indexer.stats["skipped_paths"], 0)

            stats = indexer.get_statistics()
            for key in (
                "total_files",
                "unique_files",
                "total_size",
                "logical_size",
                "on_disk_size",
                "hardlink_extra_paths",
                "skipped_paths",
                "unique_extensions",
                "top_extensions",
            ):
                self.assertIn(key, stats)

            # logical == total when no hardlinks
            self.assertEqual(stats["logical_size"], stats["total_size"])

    def test_logical_size_matches_sum_of_st_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sizes = [b"x" * 11, b"y" * 23, b"z" * 5]
            for i, payload in enumerate(sizes):
                _write(root / f"f{i}.bin", payload)
            indexer = FileIndexer()
            indexer.index_directory(str(root))
            self.assertEqual(
                indexer.get_statistics()["logical_size"], sum(len(s) for s in sizes)
            )


class FileIndexerHardlinkTests(unittest.TestCase):
    """Hardlinks must be deduped in on_disk_size and logical_size."""

    def test_hardlink_dedups_on_disk_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src.bin"
            _write(src, b"A" * 4096)
            try:
                os.link(str(src), str(root / "link.bin"))
            except (OSError, NotImplementedError) as e:
                self.skipTest(f"hardlinks unsupported on this FS: {e}")
            indexer = FileIndexer()
            n = indexer.index_directory(str(root))
            self.assertEqual(n, 2)
            stats = indexer.get_statistics()
            self.assertEqual(stats["total_files"], 2)
            self.assertEqual(stats["unique_files"], 1)
            self.assertEqual(stats["hardlink_extra_paths"], 1)
            src_blocks = os.stat(src).st_blocks
            self.assertEqual(stats["on_disk_size"], src_blocks * 512)
            # Both logical_size and on_disk_size are deduped by inode.
            self.assertEqual(stats["logical_size"], os.stat(src).st_size)
            # total_size (back-compat) is still inflated.
            self.assertEqual(stats["total_size"], 2 * os.stat(src).st_size)


class FileIndexerErrorHandlingTests(unittest.TestCase):
    """A locked subdirectory must not abort the whole walk."""

    def test_perm_error_on_subdir_does_not_abort_walk(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("running as root, chmod 0o000 is bypassable")
        if platform.system() == "Windows":
            self.skipTest("POSIX-only chmod test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.txt", b"x")
            locked = root / "locked"
            locked.mkdir()
            _write(locked / "secret.txt", b"y")
            os.chmod(locked, 0o000)
            try:
                indexer = FileIndexer()
                indexer.index_directory(str(root))
                stats = indexer.get_statistics()
                self.assertEqual(stats["total_files"], 1)
                self.assertGreaterEqual(stats["skipped_paths"], 1)
            finally:
                os.chmod(locked, 0o700)


class FileIndexerSqliteTests(unittest.TestCase):
    """The new columns and statistic rows must round-trip through SQLite."""

    def test_export_persists_new_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.txt", b"hello world")
            indexer = FileIndexer()
            indexer.index_directory(str(root))
            db = Path(tmp) / "index.db"
            ok, err = indexer.export_to_sqlite(str(db))
            self.assertTrue(ok, msg=err)

            with sqlite3.connect(str(db)) as conn:
                row = conn.execute(
                    "SELECT filepath, size, on_disk, blocks, nlinks, "
                    "inode, device FROM files"
                ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], 11)  # logical size
            self.assertGreater(row[2], 0)  # on_disk
            self.assertEqual(row[2], row[3] * 512)
            self.assertGreaterEqual(row[4], 1)  # nlinks

            with sqlite3.connect(str(db)) as conn:
                stat_keys = {
                    r[0]
                    for r in conn.execute("SELECT key FROM statistics").fetchall()
                }
            for key in (
                "total_files",
                "unique_files",
                "logical_size",
                "on_disk_size",
                "hardlink_extra_paths",
                "skipped_paths",
            ):
                self.assertIn(key, stat_keys)


class FileIndexerWindowsStatTests(unittest.TestCase):
    """On Windows ``st_blocks`` is ``None``; the indexer must not crash."""

    def test_on_disk_bytes_falls_back_when_st_blocks_is_none(self):
        from specs.disk.indexer import _on_disk_bytes

        class _WindowsStat:
            st_size = 1234
            st_blocks = None  # what Windows returns

        self.assertEqual(_on_disk_bytes(_WindowsStat()), 1234)

    def test_on_disk_bytes_uses_blocks_when_available(self):
        from specs.disk.indexer import _on_disk_bytes

        class _PosixStat:
            st_size = 100
            st_blocks = 8  # 8 * 512 = 4096

        self.assertEqual(_on_disk_bytes(_PosixStat()), 4096)


class FileIndexerSecondCallTests(unittest.TestCase):
    """A second ``index_directory`` must not retain the first call's records."""

    def test_second_call_clears_previous_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.txt", b"x" * 100)
            (root / "sub1").mkdir()
            _write(root / "sub1" / "b.txt", b"y" * 200)
            (root / "sub2").mkdir()
            _write(root / "sub2" / "c.txt", b"z" * 300)
            _write(root / "sub2" / "d.txt", b"w" * 400)

            indexer = FileIndexer()
            indexer.index_directory(str(root / "sub1"))
            first = indexer.get_statistics()
            self.assertEqual(first["total_files"], 1)

            # Second call: only sub2's files should be present.
            indexer.index_directory(str(root / "sub2"))
            second = indexer.get_statistics()
            self.assertEqual(second["total_files"], 2)
            self.assertEqual(second["unique_files"], 2)
            # The relationship must hold (would be negative on a leaky impl).
            self.assertEqual(
                second["hardlink_extra_paths"],
                second["total_files"] - second["unique_files"],
            )
            self.assertGreaterEqual(second["hardlink_extra_paths"], 0)
            # And self.files must only contain sub2 entries.
            self.assertEqual(len(indexer.files), 2)
            for path in indexer.files:
                self.assertIn("sub2", path)


class FileIndexerSymlinkTests(unittest.TestCase):
    """Symlink-to-file must be recorded under the symlink's path."""

    def test_symlink_to_file_recorded(self):
        if not hasattr(os, "symlink"):
            self.skipTest("os.symlink unavailable on this platform")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.bin"
            _write(target, b"x" * 64)
            link = root / "link.bin"
            try:
                os.symlink(str(target), str(link))
            except (OSError, NotImplementedError) as e:
                self.skipTest(f"symlinks unsupported on this FS: {e}")

            indexer = FileIndexer()
            indexer.index_directory(str(root))
            self.assertIn(
                link.as_posix(),
                indexer.files,
                "symlink-to-file should be recorded under the link's path",
            )
            self.assertEqual(indexer.files[link.as_posix()]["size"], 64)


class FileIndexerMigrationTests(unittest.TestCase):
    """A pre-0.4.1 DB must be migrated in place by ``export_to_sqlite``."""

    def test_legacy_schema_is_migrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Put the test files in a subdir so the walker doesn't also
            # pick up the legacy.db SQLite file (which is a regular
            # file on disk and would otherwise show up in the index).
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            _write(data_dir / "a.txt", b"hello")
            legacy_db = Path(tmp) / "legacy.db"
            with sqlite3.connect(str(legacy_db)) as c:
                c.execute(
                    "CREATE TABLE files ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "filepath TEXT NOT NULL UNIQUE, "
                    "filename TEXT NOT NULL, "
                    "extension TEXT, "
                    "size INTEGER, "
                    "last_modified TIMESTAMP, "
                    "indexed_at TIMESTAMP)"
                )
                c.execute(
                    "CREATE TABLE statistics ("
                    "key TEXT PRIMARY KEY, value TEXT)"
                )
                c.commit()

            indexer = FileIndexer()
            indexer.index_directory(str(data_dir))
            ok, err = indexer.export_to_sqlite(str(legacy_db))
            self.assertTrue(ok, msg=err)

            with sqlite3.connect(str(legacy_db)) as c:
                cols = {
                    r[1]
                    for r in c.execute("PRAGMA table_info(files)").fetchall()
                }
            for col in ("on_disk", "blocks", "nlinks", "inode", "device"):
                self.assertIn(col, cols, f"missing migrated column {col}")

            # Re-running must be a no-op (idempotent migration).
            ok2, err2 = indexer.export_to_sqlite(str(legacy_db))
            self.assertTrue(ok2, msg=err2)
            with sqlite3.connect(str(legacy_db)) as c:
                row = c.execute(
                    "SELECT size, on_disk, nlinks, filepath "
                    "FROM files WHERE filename = 'a.txt'"
                ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 5)        # size
            self.assertGreaterEqual(row[1], 5) # on_disk (>= size; == size if blocks None)
            self.assertGreaterEqual(row[2], 1) # nlinks


if __name__ == "__main__":
    unittest.main()

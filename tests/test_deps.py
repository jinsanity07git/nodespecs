"""Smoke tests for the lazy-install path in specs.hardware.deps and for
the bare-import surface of the public package.

These tests do not install or require GPUtil / tabulate / psutil. They
cover the blocklist that prevents `pip install distutils`-style failures
(see issue #5) and the graceful-degrade path of `info_gpu` when
nvidia-smi is not on PATH.
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

# Make `src/` importable when the test is run from the repo root.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import specs  # noqa: E402  (path-tweak above must come first)
from specs.hardware import deps  # noqa: E402
from specs.hardware import main as hardware_main  # noqa: E402


class BlocklistTests(unittest.TestCase):
    """`pip install distutils` must never happen (issue #5)."""

    def test_check_imp_rejects_distutils(self):
        with self.assertRaises(ImportError) as ctx:
            deps.check_imp("distutils")
        self.assertIn("distutils", str(ctx.exception))

    def test_check_imp_rejects_underscore_prefixed(self):
        with self.assertRaises(ImportError) as ctx:
            deps.check_imp("_io")
        self.assertIn("_io", str(ctx.exception))

    def test_ensure_lib_rejects_distutils_at_decoration_time(self):
        with self.assertRaises(ImportError):
            deps.ensure_lib("distutils")

    def test_ensure_libs_rejects_distutils_at_decoration_time(self):
        with self.assertRaises(ImportError):
            deps.ensure_libs(["GPUtil", "distutils"])


class InfoGpuDegradeTests(unittest.TestCase):
    """`info_gpu()` must never raise on a host with no NVIDIA driver."""

    def test_info_gpu_prints_friendly_message_when_no_nvidia_smi(self):
        buf = io.StringIO()
        with mock.patch.object(hardware_main.shutil, "which", return_value=None):
            with redirect_stdout(buf):
                result = hardware_main.info_gpu()
        self.assertIsNone(result)
        self.assertIn("No NVIDIA GPU detected", buf.getvalue())


class PublicApiTests(unittest.TestCase):
    """The package must import cleanly without any third-party deps."""

    def test_version_is_a_string(self):
        self.assertIsInstance(specs.__version__, str)
        # Sanity-check the shape: at least one dot, digits on each side.
        parts = specs.__version__.split(".")
        self.assertGreaterEqual(len(parts), 2)
        for p in parts:
            self.assertTrue(p.isdigit(), f"version part {p!r} is not numeric")

    def test_public_all_lists_include_version(self):
        self.assertIn("__version__", specs.__all__)

    def test_top_level_shortcuts_callable(self):
        # Each entry in __all__ should resolve to *something* callable or
        # to a string (for __version__).
        for name in specs.__all__:
            attr = getattr(specs, name)
            self.assertTrue(callable(attr) or isinstance(attr, str),
                            f"specs.{name} is not callable and not str")


if __name__ == "__main__":
    unittest.main()

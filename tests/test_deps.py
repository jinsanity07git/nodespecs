"""Smoke tests for the lazy-install path in specs.hardware.deps.

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

from specs.hardware import deps
from specs.hardware import main as hardware_main


class BlocklistTests(unittest.TestCase):
    def test_check_imp_rejects_distutils(self):
        """`check_imp('distutils')` must raise ImportError, not attempt
        a doomed `pip install distutils` (issue #5)."""
        with self.assertRaises(ImportError) as ctx:
            deps.check_imp("distutils")
        self.assertIn("distutils", str(ctx.exception))

    def test_check_imp_rejects_underscore_prefixed(self):
        """Names starting with `_` are CPython-internal and must never
        be pip-installed."""
        with self.assertRaises(ImportError) as ctx:
            deps.check_imp("_io")
        self.assertIn("_io", str(ctx.exception))

    def test_ensure_lib_rejects_distutils_at_decoration_time(self):
        """`@ensure_lib('distutils')` must fail loudly with ImportError
        so a future typo cannot silently attempt the install."""
        with self.assertRaises(ImportError):
            deps.ensure_lib("distutils")

    def test_ensure_libs_rejects_distutils_at_decoration_time(self):
        with self.assertRaises(ImportError):
            deps.ensure_libs(["GPUtil", "distutils"])


class InfoGpuDegradeTests(unittest.TestCase):
    def test_info_gpu_prints_friendly_message_when_no_nvidia_smi(self):
        """`info_gpu()` must not raise on a host without nvidia-smi; it
        should print a friendly 'No NVIDIA GPU detected' line and return."""
        buf = io.StringIO()
        with mock.patch.object(hardware_main.shutil, "which", return_value=None):
            with redirect_stdout(buf):
                result = hardware_main.info_gpu()
        self.assertIsNone(result)
        self.assertIn("No NVIDIA GPU detected", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

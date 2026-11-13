"""Tests for the GPU table rendering path of `specs.hardware.main.info_gpu`.

Unlike tests/test_deps.py, these tests DO import the real `tabulate` (a
guaranteed runtime dependency of the package) so the module-vs-function
call inside info_gpu is exercised exactly as on a real GPU host
(issue #20: `TypeError: 'module' object is not callable`). `GPUtil` and
`nvidia-smi` are faked so no NVIDIA hardware or pip install is needed.
"""
import io
import os
import sys
import types
import unittest
from collections import namedtuple
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from specs.hardware import main as hardware_main  # noqa: E402


Gpu = namedtuple(
    "Gpu",
    "id name load memoryFree memoryUsed memoryTotal temperature uuid",
)

FAKE_GPUS = [
    Gpu(
        0,
        "NVIDIA Mock 4090",
        0.25,
        2048,
        4096,
        6144,
        42,
        "GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    ),
]


class FakeGputilModule(types.ModuleType):
    """Minimal stand-in for the GPUtil module: injectable into sys.modules
    so `check_imp` binds it into info_gpu's globals without any pip
    install attempt."""

    def getGPUs(self):
        return list(FAKE_GPUS)


class InfoGpuTableTests(unittest.TestCase):
    """The GPU-present rendering path (issue #20 regression)."""

    def setUp(self):
        fake = FakeGputilModule("GPUtil")
        sys.modules["GPUtil"] = fake
        self.addCleanup(sys.modules.pop, "GPUtil", None)
        # check_imp injects GPUtil / tabulate into hardware_main's globals;
        # remove them afterwards so other tests see pristine globals.
        self.addCleanup(hardware_main.__dict__.pop, "GPUtil", None)
        self.addCleanup(hardware_main.__dict__.pop, "tabulate", None)

    def test_info_gpu_renders_tabulate_table(self):
        buf = io.StringIO()
        with mock.patch.object(
            hardware_main.shutil, "which", return_value="/usr/bin/nvidia-smi"
        ):
            with redirect_stdout(buf):
                # Must not raise: before the fix this crashed with
                # TypeError: 'module' object is not callable (issue #20).
                hardware_main.info_gpu()
        output = buf.getvalue()

        self.assertIn("GPU Details", output)
        for header in ("id", "name", "load", "uuid"):
            self.assertIn(header, output)
        self.assertIn("NVIDIA Mock 4090", output)
        self.assertIn("GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", output)

    def test_info_gpu_degrades_when_check_imp_cannot_load_module(self):
        """check_imp() returning False (module still unimportable after a
        nominal install) must print a friendly message and return — not
        crash with a NameError at the table call. GPUtil is made to load
        while tabulate fails, which is the exact ordering that would
        otherwise reach the unguarded tabulate call."""
        def fake_check_imp(module_name, target_globals=None):
            if module_name == "GPUtil":
                if target_globals is not None:
                    target_globals["GPUtil"] = sys.modules["GPUtil"]
                return True
            return False  # tabulate could not be loaded

        buf = io.StringIO()
        with mock.patch.object(
            hardware_main.shutil, "which", return_value="/usr/bin/nvidia-smi"
        ):
            with mock.patch(
                "specs.hardware.deps.check_imp", side_effect=fake_check_imp
            ):
                with redirect_stdout(buf):
                    # Must not raise NameError (principle: errors are
                    # messages, not stack traces).
                    hardware_main.info_gpu()
        output = buf.getvalue()

        self.assertIn("GPU utilities unavailable", output)
        self.assertNotIn("GPU Details", output)


if __name__ == "__main__":
    unittest.main()

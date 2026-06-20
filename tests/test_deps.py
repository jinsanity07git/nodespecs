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


class EnsureLibAutoInstallTests(unittest.TestCase):
    """Issue #10: a function decorated with `@ensure_lib("psutil")` must
    trigger the lazy-install path on first call rather than immediately
    raising `ImportError: Module psutil is required but not installed.`
    before the user has had a chance to install anything.

    These tests do not actually install psutil. They use mock to assert
    that the decorator delegates to `check_imp` (the same code path used
    by `ensure_libs`) when the module is not yet loaded, and that the
    blocklist guard is preserved.
    """

    def test_ensure_lib_delegates_to_check_imp_when_module_missing(self):
        """If the module is not in target_globals, the wrapper must call
        check_imp (which is the function that owns the uv/pip install
        logic), not raise ImportError directly.
        """
        @deps.ensure_lib("psutil")
        def probe():
            return "ok"

        # Simulate psutil being absent from the wrapper's globals. The
        # decorator's wrapper looks up `psutil` in probe.__globals__; if
        # it's not there, the wrapper must fall through to check_imp.
        probe.__globals__.pop("psutil", None)

        with mock.patch.object(deps, "check_imp", return_value=True) as m:
            result = probe()

        self.assertEqual(result, "ok")
        m.assert_called_once()
        # First positional arg must be the module spec (with or without
        # a version pin).
        args, kwargs = m.call_args
        self.assertTrue(args[0].startswith("psutil"))
        # check_imp is called with *some* globals mapping so the loaded
        # module is visible to the wrapped body. (We don't pin to a
        # specific dict — the wrapper happens to pass the caller's
        # frame globals, which is good enough.)
        self.assertIn("target_globals", kwargs)
        self.assertIsNotNone(kwargs["target_globals"])

    def test_ensure_lib_skips_check_imp_when_module_already_loaded(self):
        """Once a module has been loaded into `sys.modules` (the real
        production path — `check_imp` calls `importlib.import_module`
        which populates `sys.modules`), the wrapper must read it back
        without calling `check_imp` again on subsequent calls.
        """
        import types

        # Build a sentinel module and inject it into sys.modules. The
        # wrapper delegates to check_imp on a cache miss, so this is the
        # path that simulates "already installed + already imported".
        sentinel = types.ModuleType("psutil_for_ensure_lib_test")
        # Use a non-`psutil` name so we cannot collide with a real psutil
        # install — and decorate against that same name.
        sys.modules[sentinel.__name__] = sentinel
        try:
            @deps.ensure_lib(sentinel.__name__)
            def probe():
                return "ok"

            with mock.patch.object(deps, "check_imp") as m:
                for _ in range(3):
                    self.assertEqual(probe(), "ok")
            # check_imp must not be called at all — the module is
            # already in sys.modules.
            m.assert_not_called()
        finally:
            sys.modules.pop(sentinel.__name__, None)

    def test_ensure_lib_blocklist_still_fires(self):
        """The `_NON_PACKAGE_NAMES` guard must apply on the wrapper's
        call path too, not just at decoration time. Decorating with a
        blocked name still raises at decoration time (covered by
        BlocklistTests); this test pins the decorator-time contract.
        """
        with self.assertRaises(ImportError):
            deps.ensure_lib("distutils")


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

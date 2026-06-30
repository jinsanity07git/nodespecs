"""Tests for the compact default hardware summary."""
import io
import os
import socket
import sys
import unittest
from collections import namedtuple
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from specs import cli, cpuinfo  # noqa: E402
from specs.hardware import main as hardware_main  # noqa: E402


Partition = namedtuple("Partition", "device mountpoint fstype")
Usage = namedtuple("Usage", "total used free percent")
Memory = namedtuple("Memory", "total used free available percent")
NetIo = namedtuple("NetIo", "bytes_sent bytes_recv")
Address = namedtuple("Address", "family address netmask broadcast")


GIB = 1024 ** 3


class FakePsutil:
    def __init__(self):
        self.partitions = [
            Partition("/dev/sda1", "/", "ext4"),
            Partition("/dev/sda1", "/home", "ext4"),
            Partition("/dev/sdb1", "/data", "xfs"),
            Partition("/dev/loop0", "/snap/tool", "squashfs"),
            Partition("/dev/secret", "/secret", "ext4"),
        ]
        self.usages = {
            "/": Usage(100 * GIB, 40 * GIB, 60 * GIB, 40.0),
            "/home": Usage(100 * GIB, 60 * GIB, 40 * GIB, 60.0),
            "/data": Usage(60 * GIB, 10 * GIB, 50 * GIB, 16.7),
        }

    def cpu_count(self, logical=True):
        return 8 if logical else 4

    def cpu_percent(self, interval=None):
        return 12.5

    def virtual_memory(self):
        return Memory(16 * GIB, 6 * GIB, 10 * GIB, 10 * GIB, 37.5)

    def swap_memory(self):
        return Memory(
            2 * GIB,
            512 * 1024 ** 2,
            1536 * 1024 ** 2,
            1536 * 1024 ** 2,
            25.0,
        )

    def disk_partitions(self):
        return list(self.partitions)

    def disk_usage(self, mountpoint):
        if mountpoint == "/secret":
            raise PermissionError("denied")
        return self.usages[mountpoint]

    def net_if_addrs(self):
        return {
            "lo": [
                Address(socket.AF_INET, "127.0.0.1", "255.0.0.0", None),
            ],
            "eth0": [
                Address(socket.AF_INET, "192.0.2.10", "255.255.255.0", "192.0.2.255"),
            ],
        }

    def net_io_counters(self):
        return NetIo(5 * 1024 ** 2, 7 * 1024 ** 2)


class NetworkBlockedPsutil(FakePsutil):
    def net_if_addrs(self):
        raise PermissionError("blocked")

    def net_io_counters(self):
        raise PermissionError("blocked")


class CompactSystemInfoTests(unittest.TestCase):
    def _render_summary(self, fake_psutil=None):
        fake_psutil = fake_psutil or FakePsutil()
        buf = io.StringIO()
        with mock.patch.object(hardware_main, "psutil", fake_psutil, create=True):
            with mock.patch.object(
                cpuinfo,
                "get_cpu_info",
                return_value={"brand_raw": "Mock CPU 9000"},
            ):
                with redirect_stdout(buf):
                    result = hardware_main.get_system_info()
        return result, buf.getvalue()

    def test_get_system_info_prints_compact_summary_only(self):
        result, output = self._render_summary()

        self.assertEqual(result[0], 8)
        self.assertEqual(result[1], 16.0)
        self.assertIn("OS      :", output)
        self.assertIn("Host    :", output)
        self.assertIn("CPU     : Mock CPU 9000", output)
        self.assertIn("vCPUs   : 8", output)
        self.assertIn("CPU Use : 12.5%", output)
        self.assertIn("Memory  : 6.00GB / 16.00GB (37.5%)", output)
        self.assertIn("Swap    : 512.00MB / 2.00GB (25.0%)", output)
        self.assertIn("IPv4    : eth0 192.0.2.10/255.255.255.0", output)
        self.assertIn("Net I/O : 5.00MB sent / 7.00MB recv", output)

        for verbose_header in (
            "CPU Info",
            "Memory Information",
            "Disk Information",
            "Network Information",
            "CPU Usage Per Core",
            "Core",
        ):
            self.assertNotIn(verbose_header, output)

    def test_disk_rows_are_deduped_and_inaccessible_partitions_skipped(self):
        result, output = self._render_summary()
        storage_info = result[2]

        self.assertEqual(output.count("/dev/sda1"), 1)
        self.assertIn("/dev/sdb1 on /data (xfs)", output)
        self.assertIn("Storage : 160.00GB total", output)
        self.assertNotIn("/dev/loop0", output)
        self.assertNotIn("/snap/tool", output)
        self.assertNotIn("/dev/secret", output)
        self.assertFalse(any("/dev/secret" in row for row in storage_info))

    def test_network_permission_errors_print_unavailable(self):
        result, output = self._render_summary(NetworkBlockedPsutil())

        self.assertEqual(result[0], 8)
        self.assertIn("IPv4    : unavailable", output)
        self.assertIn("Net I/O : unavailable", output)


class CliDefaultTests(unittest.TestCase):
    def test_default_cli_calls_only_compact_system_info(self):
        with mock.patch(
            "specs.hardware.get_system_info",
            return_value=(8, 16.0, []),
        ) as compact:
            with mock.patch("specs.hardware.info_cpu") as info_cpu:
                with mock.patch("specs.hardware.info_mem") as info_mem:
                    with mock.patch("specs.hardware.info_disk") as info_disk:
                        with mock.patch("specs.hardware.info_net") as info_net:
                            exit_code = cli.main([])

        self.assertEqual(exit_code, 0)
        compact.assert_called_once_with()
        info_cpu.assert_not_called()
        info_mem.assert_not_called()
        info_disk.assert_not_called()
        info_net.assert_not_called()


if __name__ == "__main__":
    unittest.main()

# hardwareSummary

[![PyPI version](https://img.shields.io/pypi/v/nodespecs)](https://pypi.org/project/nodespecs/)
[![Python](https://img.shields.io/pypi/pyversions/nodespecs)](https://pypi.org/project/nodespecs/#files)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/jinsanity07git/nodespecs/blob/main/LICENSE)
[![CI](https://github.com/jinsanity07git/nodespecs/actions/workflows/ci.yml/badge.svg)](https://github.com/jinsanity07git/nodespecs/actions/workflows/ci.yml)

A Swiss Army Knife library for system, hardware, and filesystem utilities. Reports OS / CPU / GPU / memory / disk / network, runs a CPU benchmark, organizes a downloads folder, indexes a filesystem to SQLite, generates a Mermaid `gitGraph`, and ships a streaming upload server plus a custom TCP file-transfer client/server. **Python 3.6+**, single runtime dependency (`tabulate`), heavy deps lazy-installed on first use.

```shell
pip install nodespecs
python -m specs                      # compact system report
python -m specs bcpu                 # CPU benchmark
python -c "import specs; specs.info_gpu()"
```


### install with UV
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.12

# On modern Linux (Ubuntu 22.04+, Debian 12+) the system Python is
# marked as "externally managed" by PEP 668. If a bare `pip install`
# fails with `externally-managed-environment`, either add
# `--break-system-packages` or use a virtualenv:
sudo apt install python-is-python3
sudo apt install python3-pip
pip install nodespecs --break-system-packages

uv init
uv add nodespecs
# v0.4.2+ auto-installs heavy deps (psutil, etc.) on first use via
# the `@ensure_lib` decorator — no separate `uv pip install psutil`.
uv run -m specs
uv run -m specs bcpu

# or
source .venv/bin/activate
python -m specs bcpu

```
### install and use with pip
```shell
sudo apt install python-is-python3
sudo apt install python3-pip

```

> **Note on PEP 668.** On modern Linux distros (Ubuntu 22.04+, Debian
> 12+, etc.), the system Python is marked as "externally managed."
> If `pip install nodespecs` fails with `externally-managed-environment`,
> add `--break-system-packages` or use a virtual environment
> (`python3 -m venv .venv && source .venv/bin/activate`).
>
> v0.4.2+ no longer requires a separate `pip install psutil` — the
> `@ensure_lib` decorator auto-installs missing heavy deps (`psutil`,
> etc.) on first use. You only need `pip install nodespecs`.

```shell
pip install nodespecs
python -m specs
python -c "import specs; specs.bench_cpu()"
python -c "import specs; specs.hardware.get_system_info()"

python -c "import specs; specs.info_gpu()"
python -c "from specs import disk;print(disk.resolve_user_path())"
python -c "from specs.disk import resolve_user_path;print(resolve_user_path())"
```

```shell
# clean and orgnized download folder for WINDOWS user
python -m specs fclean

# for the machine not compatible with psutil
python -m specs -v
python -m specs -l=1

python -m specs bcpu
python -m specs upload
python -m specs server
python -m specs cld -i='172.25.1.228'
```

### File Indexer Script

`python -m specs.disk.drive` walks a directory tree, captures per-file
metadata (logical size, on-disk usage in 512-byte blocks, hardlinks,
inode, device), and writes the result to a SQLite database. It also
prints a side-by-side comparison between the indexer's `on_disk_size`
and `shutil.disk_usage(root_dir)` so the gap from filesystem metadata,
snapshots, and unread subtrees is visible.

The new on-disk size is deduped by inode, so a file with N hardlinks
contributes its real allocation once instead of N times. Cluster
rounding on NTFS / exFAT and sparse files are automatically accounted
for via `st_blocks * 512`.

##### Usage

Run from the repository root. `--dir` defaults to the current working
directory on Linux / macOS and to `F:\\` on Windows:

```shell
python -m specs.disk.drive
```

To index a custom directory, pass `--dir` explicitly:

```shell
python -m specs.disk.drive --dir "F:\\"            # Windows
python -m specs.disk.drive --dir /home/me/data    # Linux / macOS
```

To set the SQLite output path explicitly:

```shell
python -m specs.disk.drive --dir "F:\\" --db "F:\\file_index.db"
```

##### Expected Output

On success:

```
Indexed <N> files (<U> unique inodes)
  logical size:         <bytes> bytes
  on-disk size:         <bytes> bytes  (deduped by inode; accounts for cluster rounding + sparse files)
  hardlink paths:       <count> (extra paths sharing an inode)
  skipped:              <count> (permission / access errors during walk)
Successfully exported to SQLite database: <path>/file_index.db

OS-reported usage of the volume containing <root_dir> (indexer covers this subtree only):
  total:                <bytes> bytes
  used:                 <bytes> bytes
  free:                 <bytes> bytes
  OS - indexer:         <bytes> bytes  (includes every file outside the indexed subtree, plus metadata, snapshots, etc.)
```

When the indexed directory is the volume root (e.g. `C:\\` on Windows
or `/` on Linux), the OS-reported block reports the volume itself and
the gap is attributed to "metadata, system files, unread subtrees,
snapshots" instead of "files outside the indexed subtree."

On failure to export:

```
Export failed: <error message>
```

The SQLite `files` table has columns for `filepath`, `filename`,
`extension`, `size`, `on_disk`, `blocks`, `nlinks`, `inode`, `device`,
`last_modified`, and `indexed_at`. The `statistics` table holds the
same counters that the CLI prints.


```shell
## server
python -c "import specs; print(specs.__version__)"

python -c "import specs; specs.whoish()"
python -c "import specs; specs.server()"
## client upload wt progress bar
python -c "import specs; specs.client('172.25.1.175', 12345,'./README.md',False)"

## client upload wo progress bar
python -c "import specs; specs.client('172.25.1.175', 12345,'./README.md',False)"
## client upload top level files in the cwd
python -c "import specs; specs.clientd('192.168.0.157')"
python -c "import specs; specs.clientd('192.168.0.157', 12345)"
```


```
sudo apt update
sudo apt install python3-pip
python3 -m pip install nodespecs && python3 -m specs
```



```python
import specs

specs.info_gpu()
specs.bench_cpu()
```





#### Deprecated  (install and use with git)

```
!git clone https://github.com/jinsanity07git/hardwareSummary && python hardwareSummary/hardware.py && python hardwareSummary/cpu-benchmark.py

```

```cmd
git clone https://github.com/jinsanity07git/hardwareSummary && python hardwareSummary/hardware.py && python hardwareSummary/cpu-benchmark.py

```

```bash
sudo apt upgrade
sudo apt install python3-pip
git clone https://github.com/jinsanity07git/hardwareSummary && python3 hardwareSummary/hardware.py && python3 hardwareSummary/cpu-benchmark.py
```



### CPU collection


| Nickname                                                     | CPU                                            | Arch    | OS             | Python  | Benchmarking | Comb                                                         | Score |
| ------------------------------------------------------------ | ---------------------------------------------- | ------- | -------------- | ------- | ------------ | ------------------------------------------------------------ | ----- |
| TC01                                                         | Intel(R) Core(TM) i9-14900K                    | x86_64  | Linux 5.15.153.1-microsoft-standard-WSL2 | 3.12.12 | 5.43                            | Core-i9-14900KF | 39.25 |
| lab-aws                                                      | Intel(R) Xeon(R) Platinum 8488C                | x86_64  | Linux          | 3.11.12 | 11.174       |                                                              | 38.76 |
| TC14                                                         | 13th Gen Intel(R) Core(TM) i9-13900K           | AMD64   | Windows 10     |         | 12.991       | Core-i9-13900K                                               | 38.76 |
| TC17<br />TC16                                               | Intel(R) Core(TM) i9-14900KF                   | AMD64   | Windows        |         | 15.654       | Core-i9-14900KF                                              | 39.25 |
| iPhone 14 Pro Max<br />iPhone15,3[^3]                        | Apple A16 Bionic[^2]                           | arm64e  | Darwin 23.4.0  |         | 15.962       |                                                              |       |
| 10cent CloudStudio                                           | Intel(R) Xeon(R) Platinum 8255C CPU @ 2.50GHz  | x86_64  | Linux          | 3.10.11 | 19.891       |                                                              |       |
| TC19                                                         | Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz       | sAMD64  | Windows 10     |         | 20.534       | Core-i7-9700K                                                | 9.45  |
| Dell Precision 5690                                          | Intel(R) Core(TM) Ultra 9 185H                 | AMD64   | Windows 11 Pro | 3.8.12  | 23.824       |                                                              |       |
| CHINAMI                                                      | Intel(R) Xeon(R) w5-3435X                      | AMD64   | Windows 10     |         | 23.849       | [Xeon w5-3435X](https://technical.city/en/cpu/Xeon-w5-3435X) | 28.58 |
| Dell Precision 3561                                          | 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz | AMD64   | Windows        |         | 23.852       | Core-i7-11800H                                               | 13.47 |
| github codespaces                                            | AMD EPYC 7763 64-Core Processor                | x86_64  | Linux          |         | 24.259       | [EPYC-7763](https://technical.city/en/cpu/EPYC-7763)         | 54.65 |
| alibaba t5                                                   | Intel(R) Xeon(R) Platinum 8269CY CPU @ 2.50GH  | x86_64  | Linux          | 3.12.3  | 25.44        |                                                              |       |
| TC07                                                         | Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz       | AMD64   | Windows        |         | 26.723       | Core-i7-9700K                                                | 9.45  |
| oracle cloudshell                                            | ARM Cortex-A53                                 | aarch64 | Linux          |         | 27.489       |                                                              |       |
| AWS `t2.micro`                                               | Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz      | x86_64  | Linux          |         | 27.785       | [Core-i7-9700K](https://technical.city/en/cpu/Core-i7-9700K) | 8.81  |
| AWS workspace                                                | Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz | x86_64  | Linux          | 3.10.12 | 29.355       |                                                              |       |
| google cloudshell                                            | Intel(R) Xeon(R) CPU @ 2.20GHz                 | x86_64  | Linux          |         | 29.818       |                                                              |       |
| WUYING: 8 vCPU / 16 GiB Linux                                | Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz   | x86_64  | Linux          |         | 33.572       | [Xeon-Platinum-8163](https://versus.com/en/intel-xeon-gold-6126-vs-intel-xeon-platinum-8168) |       |
| TC03<br />TC11                                               | Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz      | AMD64   | Window         |         | 34.612       | Xeon-Gold-6248R                                              | 23.26 |
| 2018 Macbook pro                                             | Intel(R) Core(TM) i7-8559U CPU @ 2.70GHz       | x86_64  | Darwin 22.1.0  |         | 37.105       | [Core-i7-8559U](https://technical.city/en/cpu/Core-i7-8559U) | 5.38  |
| JVM                                                          | Intel(R) Xeon(R) Gold 6126 CPU @ 2.60GHz       | x86_64  | Linux          |         | 38.685       | [Xeon-Gold-6126](https://technical.city/en/cpu/Xeon-Gold-6126) | 12.21 |
| TC01                                                         | Intel(R) Xeon(R) CPU E5-2643 v4 @ 3.40GHz      | AMD64   | Windows        |         | 39.258       | Xeon-E5-2643-v4                                              | 7.62  |
| Jquant                                                       | Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz   | x86_64  | Linux          |         | 40.128       | Xeon-Platinum-8163                                           |       |
| google colab free tier                                       | Intel(R) Xeon(R) CPU @ 2.20GHz                 | x86_64  | Linux          |         | 43.078       |                                                              |       |
| aws cloudshell                                               | Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz | x86_64  | Linux          |         | 49.396       |                                                              |       |
| JVM                                                          | Intel(R) Xeon(R) Gold 6126 CPU @ 2.60GHz       | AMD64   | Windows        |         | 62.969       |                                                              |       |
| [binder-examples/conda](https://github.com/binder-examples/conda)[^4] | Intel(R) Xeon(R) Gold 6140 CPU @ 2.30GHz       | x86_64  | Linux          |         | 74.349       | [Xeon-Gold-6140](https://technical.city/en/cpu/Xeon-Gold-6140) | 15.8  |
| serv00-FreeBSD                                               | Intel(R) Xeon(R) Silver 4214R CPU @ 2.40GHz    | AMD64   | Linux          |         | 75.571       |                                                              |       |
| Oracle 1G-1G-0.5Gbps                                         | AMD EPYC 7551 32-Core Processor                | x86_64  | Linux          |         | 98.732       | EPYC-7551                                                    | 14.67 |
| mini PC                                                      | Intel(R) Atom(TM) x5-Z8350 CPU @ 1.44GHz       | x86_64  | Linux          |         | 135.107      | Atom-x5-Z8350                                                | 0.57  |

* Note
  * Kinds of Arch explanation[^1] 


### GPU collection

| id                             | name                                      | total memory | Synthetic benchmark | CUDA API |
| ------------------------------ | ----------------------------------------- | ------------ | ------------------- | -------- |
| 17                             | NVIDIA GeForce RTX 4060                   | 8188.0MB     | 50.69               | NA       |
| colab <br />10cent CloudStudio | Tesla T4                                  | 15360.0MB    | 28.16               | 70627    |
| 5690                           | NVIDIA RTX 3500 Ada Generation Laptop GPU | 12282 MB     |                     |          |
| dell                           | NVIDIA T600 Laptop GPU                    | 4096.0MB     | 16.69               | 26600    |
| 01                             | Quadro M4000                              | 8192.0MB     | 17.27               | 16648    |




## Feature in develop

1. work through [ws](https://websockets.readthedocs.io/en/stable/intro/index.html), transfer file using `websocket`
2. [py-ios-device](https://github.com/YueChen-C/py-ios-device) python based Apple instruments protocol，you can get CPU, Memory and 
* [x] Streaming upload server in Python extended from [uploadserver](https://github.com/Densaugeo/uploadserver).other metrics from real iOS devices





Performance source

* https://browser.geekbench.com/
  * 
* https://technical.city/en/video/GeForce-RTX-4060-vs-Tesla-T4
* https://technical.city/en/video/Tesla-T4-vs-T600

[^1]: [mainstream CPU architecture](https://jinsanity07git.github.io/post/mainstream%20CPU%20architecture.html)
[^2]: [Apple A16](https://en.wikipedia.org/wiki/Apple_A16) 
[^3]: [apple ios devices name](https://www.innerfence.com/howto/apple-ios-devices-dates-versions-instruction-sets)

[^4]: binder: [Get your own copy of this repository](https://mybinder.readthedocs.io/en/latest/introduction.html)

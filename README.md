# hardwareSummary
Extracting and Fetching all system and hardware information such as os details, CPU and GPU information, disk and network usage in Python using platform, psutil and gputil libraries.



### install and use with pip

```shell
pip install nodespecs
python -m specs
python -c "import specs; specs.bench_cpu()"
python -c "import specs; specs.info_gpu()"
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
| Nickname                      | CPU                                            | Arch   | OS            | Benchmarking | Comb                                                         | Score |
| ----------------------------- | ---------------------------------------------- | ------ | ------------- | ------------ | ------------------------------------------------------------ | ----- |
| TC17<br />TC16                | Intel(R) Core(TM) i9-14900KF                   | AMD64  | Windows       | 15.654       | Core-i9-14900KF                                              | 39.25 |
| TC14                          | 13th Gen Intel(R) Core(TM) i9-13900K           | AMD64  | Windows 10    | 12.991       | Core-i9-13900K                                               | 38.76 |
| Dell Precision 3561           | 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz | AMD64  | Windows       | 23.852       | Core-i7-11800H                                               | 13.47 |
| TC07                          | Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz       | AMD64  | Windows       | 26.723       | Core-i7-9700K                                                | 9.45  |
| AWS `t2.micro`                | Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz      | x86_64 | Linux         | 27.785       | [Core-i7-9700K](https://technical.city/en/cpu/Core-i7-9700K) | 8.81  |
| WUYING: 8 vCPU / 16 GiB Linux | Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz   | x86_64 | Linux         | 33.572       | [Xeon-Platinum-8163](https://versus.com/en/intel-xeon-gold-6126-vs-intel-xeon-platinum-8168) |       |
| TC03<br />TC11                | Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz      | AMD64  | Window        | 34.612       | Xeon-Gold-6248R                                              | 23.26 |
| 2018 Macbook pro              | Intel(R) Core(TM) i7-8559U CPU @ 2.70GHz       | x86_64 | Darwin 22.1.0 | 37.105       | [Core-i7-8559U](https://technical.city/en/cpu/Core-i7-8559U) | 5.38  |
| JVM                           | Intel(R) Xeon(R) Gold 6126 CPU @ 2.60GHz       | x86_64 | Linux         | 38.685       | [Xeon-Gold-6126](https://technical.city/en/cpu/Xeon-Gold-6126) | 12.21 |
| TC01                          | Intel(R) Xeon(R) CPU E5-2643 v4 @ 3.40GHz      | AMD64  | Windows       | 39.258       | Xeon-E5-2643-v4                                              | 7.62  |
| Jquant                        | Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz   | x86_64 | Linux         | 40.128       | Xeon-Platinum-8163                                           |       |
| google colab free tier        | Intel(R) Xeon(R) CPU @ 2.20GHz                 | x86_64 | Linux         | 43.078       |                                                              |       |
| aws cloudshell                | Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz | x86_64 | Linux         | 49.396       |                                                              |       |
| JVM                           | Intel(R) Xeon(R) Gold 6126 CPU @ 2.60GHz       | AMD64  | Windows       | 62.969       |                                                              |       |
| Oracle 1G-1G-0.5Gbps          | AMD EPYC 7551 32-Core Processor                | x86_64 | Linux         | 98.732       | EPYC-7551                                                    | 14.67 |
| mini PC                       | Intel(R) Atom(TM) x5-Z8350 CPU @ 1.44GHz       | x86_64 | Linux         | 135.107      | Atom-x5-Z8350                                                | 0.57  |

### GPU collection



| id    | name                    | total memory | Synthetic benchmark | CUDA API |
| ----- | ----------------------- | ------------ | ------------------- | -------- |
| 17    | NVIDIA GeForce RTX 4060 | 8188.0MB     | 50.69               | NA       |
| colab | Tesla T4                | 15360.0MB    | 28.16               | 70627    |
| dell  | NVIDIA T600 Laptop GPU  | 4096.0MB     | 16.69               | 26600    |
| 01    | Quadro M4000            | 8192.0MB     | 17.27               | 16648    |





Performance source

* https://browser.geekbench.com/
  * 
* https://technical.city/en/video/GeForce-RTX-4060-vs-Tesla-T4
* https://technical.city/en/video/Tesla-T4-vs-T600

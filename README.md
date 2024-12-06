# hardwareSummary
Extracting and Fetching all system and hardware information such as os details, CPU and GPU information, disk and network usage in Python using platform, psutil and gputil libraries.



### install and use with pip

```shell
pip install nodespecs
python -m specs
python -c "import specs; specs.bench_cpu()"
python -c "import specs; specs.info_gpu()"
python -c "from specs import disk;print(disk.resolve_path())"
python -c "from specs.disk import resolve_path;print(resolve_path())"
```

```shell
# clean and orgnized download folder for WINDOWS user
python -m specs -u="fclean"

# for the machine not compatible with psutil
python -m specs -v
python -m specs -l=1

python -m specs -u="bcpu"
python -m specs -u="upload"
python -m specs -u="server"
python -m specs -u="cld" -i='172.25.1.228'
```

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
| TC14                                                         | 13th Gen Intel(R) Core(TM) i9-13900K           | AMD64   | Windows 10     |         | 12.991       | Core-i9-13900K                                               | 38.76 |
| TC17<br />TC16                                               | Intel(R) Core(TM) i9-14900KF                   | AMD64   | Windows        |         | 15.654       | Core-i9-14900KF                                              | 39.25 |
| iPhone 14 Pro Max<br />iPhone15,3[^3]                        | Apple A16 Bionic[^2]                           | arm64e  | Darwin 23.4.0  |         | 15.962       |                                                              |       |
| TC19                                                         | Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz       | sAMD64  | Windows 10     |         | 20.534       | Core-i7-9700K                                                | 9.45  |
| Dell Precision 5690                                          | Intel(R) Core(TM) Ultra 9 185H                 | AMD64   | Windows 11 Pro | 3.8.12  | 23.824       |                                                              |       |
| Dell Precision 3561                                          | 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz | AMD64   | Windows        |         | 23.852       | Core-i7-11800H                                               | 13.47 |
| github codespaces                                            | AMD EPYC 7763 64-Core Processor                | x86_64  | Linux          |         | 24.259       | [EPYC-7763](https://technical.city/en/cpu/EPYC-7763)         | 54.65 |
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

| id    | name                                      | total memory | Synthetic benchmark | CUDA API |
| ----- | ----------------------------------------- | ------------ | ------------------- | -------- |
| 17    | NVIDIA GeForce RTX 4060                   | 8188.0MB     | 50.69               | NA       |
| colab | Tesla T4                                  | 15360.0MB    | 28.16               | 70627    |
| 5690  | NVIDIA RTX 3500 Ada Generation Laptop GPU | 12282 MB     |                     |          |
| dell  | NVIDIA T600 Laptop GPU                    | 4096.0MB     | 16.69               | 26600    |
| 01    | Quadro M4000                              | 8192.0MB     | 17.27               | 16648    |




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

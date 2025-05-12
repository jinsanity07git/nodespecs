keymap = {

    "DiskUsage" : { 
        "Linux"   :  "df -H",
        "macOS"   :  "df -H",
        "windows" :  "Get-PSDrive -PSProvider 'FileSystem'"
     },

     "OSrelease" : {
        "Linux"   :  "cat /etc/os-release",
        "macOS"   :  "",
        "windows" :  "systeminfo | findstr /B /C:'OS'"
     },
     "SysmArch" : {
        "Linux"   :  "uname -m",
        "macOS"   :  "",
        "windows" :  "systeminfo | findstr /B /C:'System Type'"
     },

     "CPUinfo" : {
        "Linux"   :  ["cat /proc/cpuinfo","lscpu"],
        "macOS"   :  "",
        "windows" :  ""
     },
     "Meminfo" : {
        "Linux"   :  "cat /proc/meminfo", 
        "macOS"   :  "",
        "windows" :  ""
     },
}


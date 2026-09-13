import os
import time
import platform
import shutil
import urllib.request
from typing import Dict, Any

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        self._last_connectivity_check = 0
        self._cached_connectivity_status = "ONLINE"

    def get_system_stats(self) -> Dict[str, Any]:
        uptime_sec = int(time.time() - self.start_time)
        total, used, free = shutil.disk_usage(os.getcwd())
        disk_stats = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 1)
        }

        mem_stats = {"total_mb": 4096, "used_mb": 1024, "free_mb": 3072, "percent_used": 25.0}
        try:
            if platform.system() == "Linux" and os.path.exists("/proc/meminfo"):
                meminfo = {}
                with open("/proc/meminfo") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = int(parts[1].split()[0])
                total_k = meminfo.get("MemTotal", 4194304)
                free_k = meminfo.get("MemAvailable", meminfo.get("MemFree", 2097152))
                used_k = total_k - free_k
                mem_stats = {
                    "total_mb": round(total_k / 1024, 1),
                    "used_mb": round(used_k / 1024, 1),
                    "free_mb": round(free_k / 1024, 1),
                    "percent_used": round((used_k / total_k) * 100, 1)
                }
        except Exception:
            pass

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "uptime_seconds": uptime_sec,
            "uptime_formatted": f"{uptime_sec // 3600}h {(uptime_sec % 3600) // 60}m {uptime_sec % 60}s",
            "disk": disk_stats,
            "memory": mem_stats,
            "connectivity": self.check_connectivity()
        }

    def check_connectivity(self, force: bool = False) -> str:
        now = time.time()
        if not force and (now - self._last_connectivity_check < 30):
            return self._cached_connectivity_status

        self._last_connectivity_check = now
        try:
            req = urllib.request.Request("https://1.1.1.1", headers={"User-Agent": "BillingerMonitor/3.0"})
            with urllib.request.urlopen(req, timeout=2):
                self._cached_connectivity_status = "ONLINE"
        except Exception:
            self._cached_connectivity_status = "OFFLINE"

        return self._cached_connectivity_status

system_monitor = SystemMonitor()

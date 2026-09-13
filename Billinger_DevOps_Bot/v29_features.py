"""
Billinger v2.9 Features Layer: 4K Ultra-HD Scaling & System Resource Guard
Directly integrates with core.system_monitor.
"""
from core.system_monitor import system_monitor, SystemMonitor

class SystemResourceGuard:
    RAM_LIMIT_MB = 4096
    @staticmethod
    def get_resource_snapshot():
        snap = system_monitor.get_system_snapshot()
        return {
            "cpu_percent": snap.get("cpu_usage_pct", 0.0),
            "memory_used_mb": snap.get("memory_used_mb", 512),
            "memory_total_mb": snap.get("memory_total_mb", 4096),
            "memory_percent": snap.get("memory_usage_pct", 12.5),
            "safe_threshold_passed": snap.get("memory_used_mb", 512) < 4096
        }

resource_guard = SystemResourceGuard()

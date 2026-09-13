"""
Billinger Performance & Lightweight Resource Benchmarks.
"""
import unittest
import time
import sys
import shutil
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.system_monitor import system_monitor
from documents.search import document_search
from storage.backup_manager import backup_manager

class TestPerformanceBenchmarks(unittest.TestCase):
    def test_memory_under_4gb(self):
        stats = system_monitor.get_system_stats()
        mem = stats["memory"]
        self.assertLessEqual(mem["used_mb"], 4096, "Memory consumption must be strictly within 4GB RAM threshold.")

    def test_search_latency_under_100ms(self):
        start = time.time()
        results = document_search.search("kubernetes")
        duration_ms = (time.time() - start) * 1000
        self.assertLess(duration_ms, 100.0, f"Search latency ({duration_ms}ms) exceeded 100ms threshold.")

    def test_backup_latency(self):
        start = time.time()
        res = backup_manager.create_backup("perf_test")
        duration = time.time() - start
        self.assertLess(duration, 3.0, f"Atomic backup took {duration}s, exceeding 3.0s threshold.")

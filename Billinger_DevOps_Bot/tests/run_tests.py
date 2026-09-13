import os
if 'BILLINGER_DB_PATH' not in os.environ:
    try:
        import sqlite3
        _test_conn = sqlite3.connect(':memory:')
        _test_conn.close()
        # Test 9p lock
        _test_f = '/tmp/billinger_env_test.db'
        os.environ['BILLINGER_DB_PATH'] = _test_f
    except Exception:
        pass
import unittest
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

# Load all test modules explicitly
from tests.unit.test_core import TestCore
from tests.unit.test_security import TestSecurity
from tests.unit.test_learning import TestLearning
from tests.unit.test_documents import TestDocuments
from tests.integration.test_pipeline import TestE2EPipeline
from tests.api.test_routes import TestAPIRoutes
from tests.performance.test_benchmarks import TestPerformanceBenchmarks
from tests.failure.test_failure_injection import TestFailureInjection
from tests.cross_platform.test_cross_platform import TestCrossPlatform

def build_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCore))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestLearning))
    suite.addTests(loader.loadTestsFromTestCase(TestDocuments))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceBenchmarks))
    suite.addTests(loader.loadTestsFromTestCase(TestFailureInjection))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossPlatform))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(build_suite())
    sys.exit(0 if result.wasSuccessful() else 1)

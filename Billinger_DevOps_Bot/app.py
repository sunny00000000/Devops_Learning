"""
Billinger DevOps Bot — Main Unified Application & Server
Master Production Release v3.0.0

Runs the complete, multi-threaded production server with port auto-failover,
full 13-tab Comfort Dark / High-Contrast 4K UI, 25+ REST API endpoints,
12-domain DevOps Master Curriculum, 3-tier command sandbox, production incident center,
adaptive AI router, and ATS resume engine.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Direct access to all modular feature layers
import v2_features
import v23_features
import v24_features
import v26_features
import v27_features
import v28_features
import v29_features
import v30_features

from api.server import run_server
from core.configuration.config import Config

if __name__ == "__main__":
    port_env = os.environ.get("BILLINGER_PORT")
    port = int(port_env) if port_env and port_env.isdigit() else Config.PORT
    run_server(host=Config.HOST, port=port)

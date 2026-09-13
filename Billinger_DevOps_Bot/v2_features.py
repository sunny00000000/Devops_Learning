"""
Billinger v2.0 Features Layer: Interactive Lab Workspaces, Verification & Telemetry
Directly integrates with learning.playground, storage.db, and core logging.
"""
from pathlib import Path
from learning.playground import playground, CommandPlayground
from core.logging.logger import logger
from storage.db import db

class InteractiveLabManager:
    """Manages student workspace isolation and task validation"""
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent)
        self.labs_dir = self.base_dir / "labs"
        self.labs_dir.mkdir(parents=True, exist_ok=True)

    def get_student_workspace(self, student_id="student_1"):
        workspace = self.labs_dir / student_id
        workspace.mkdir(parents=True, exist_ok=True)
        return str(workspace)

    def verify_command_objective(self, student_id, expected_file=None, expected_content=None):
        ws = Path(self.get_student_workspace(student_id))
        if expected_file:
            target = ws / expected_file
            if not target.exists():
                return False, f"File {expected_file} was not created in lab workspace."
            if expected_content:
                text = target.read_text(encoding="utf-8", errors="ignore")
                if expected_content not in text:
                    return False, f"Content mismatch in {expected_file}."
        return True, "Objective verified successfully."

class TelemetryCollector:
    """Tracks learner interactions and performance metrics"""
    def __init__(self):
        self.events = []

    def record_event(self, event_type, details=None):
        import time
        entry = {"event_type": event_type, "details": details or {}, "timestamp": time.time()}
        self.events.append(entry)
        return entry

    def get_summary(self):
        return {"total_events": len(self.events), "recent_events": self.events[-10:]}

lab_manager = InteractiveLabManager()
telemetry_collector = TelemetryCollector()

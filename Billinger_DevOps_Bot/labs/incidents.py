import time
import json
from storage.db import db
from labs.simulation import company_simulation

class IncidentCenter:
    @staticmethod
    def trigger_incident(user_id: str, severity: str = "L1") -> dict:
        scenarios = company_simulation.list_scenarios()
        selected = scenarios[0] if scenarios else {}
        
        incident_id = f"inc_{severity.lower()}_{int(time.time())}"
        title = f"[{severity.upper()} Critical] {selected.get('title', 'Service Interruption Detected')}"
        
        db.execute("""
            INSERT INTO incident_records (id, user_id, severity, title, acknowledged_time, resolved_time, mttr_seconds, status, postmortem_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id, user_id, severity, title,
            None, None, None, "TRIGGERED", "{}", time.time()
        ))

        return {
            "incident_id": incident_id,
            "severity": severity,
            "title": title,
            "scenario": selected,
            "alert_time": time.time(),
            "status": "TRIGGERED"
        }

    @staticmethod
    def acknowledge_incident(incident_id: str) -> dict:
        now = time.time()
        db.execute("UPDATE incident_records SET acknowledged_time = ?, status = 'ACKNOWLEDGED' WHERE id = ?", (now, incident_id))
        return {"incident_id": incident_id, "status": "ACKNOWLEDGED", "acknowledged_time": now}

    @staticmethod
    def resolve_incident(incident_id: str, postmortem: dict) -> dict:
        record = db.fetchone("SELECT timestamp, acknowledged_time FROM incident_records WHERE id = ?", (incident_id,))
        if not record:
            return {"error": "Incident record not found"}

        now = time.time()
        ack_time = record["acknowledged_time"] or record["timestamp"]
        mttr = round(now - ack_time, 1)

        db.execute("""
            UPDATE incident_records 
            SET resolved_time = ?, mttr_seconds = ?, status = 'RESOLVED', postmortem_json = ?
            WHERE id = ?
        """, (now, mttr, json.dumps(postmortem), incident_id))

        return {
            "incident_id": incident_id,
            "status": "RESOLVED",
            "mttr_seconds": mttr,
            "mttr_formatted": f"{int(mttr // 60)}m {int(mttr % 60)}s",
            "postmortem": postmortem
        }

incident_center = IncidentCenter()

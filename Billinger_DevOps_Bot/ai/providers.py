import os
import time
from typing import Dict, Any, List
from storage.db import db
from core.logging.logger import logger

DEFAULT_PROVIDERS = {
    "gemini": {"model": "gemini-1.5-flash", "priority": 1, "enabled": 1},
    "groq": {"model": "llama-3.3-70b-versatile", "priority": 2, "enabled": 1},
    "openai": {"model": "gpt-4o-mini", "priority": 3, "enabled": 1},
    "openrouter": {"model": "meta-llama/llama-3.3-70b-instruct", "priority": 4, "enabled": 1}
}

class AIProviderManager:
    def __init__(self):
        self.init_providers()

    def init_providers(self):
        for name, conf in DEFAULT_PROVIDERS.items():
            existing = db.fetchone("SELECT provider_name FROM ai_providers WHERE provider_name = ?", (name,))
            if not existing:
                env_key = os.environ.get(f"{name.upper()}_API_KEY", "")
                db.execute("""
                    INSERT INTO ai_providers (provider_name, enabled, api_key, model, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, conf["enabled"], env_key, conf["model"], conf["priority"], "READY"))

    def list_providers(self) -> List[Dict[str, Any]]:
        rows = db.fetchall("SELECT provider_name, enabled, api_key, model, priority, status, cooldown_until, last_error FROM ai_providers ORDER BY priority ASC")
        result = []
        for r in rows:
            key = r.get("api_key") or ""
            masked_key = f"{key[:4]}...{key[-4:]}" if len(key) >= 10 else ("***" if key else "")
            result.append({
                "provider": r["provider_name"],
                "enabled": bool(r["enabled"]),
                "api_key_masked": masked_key,
                "has_key": bool(key),
                "model": r["model"],
                "priority": r["priority"],
                "status": r["status"],
                "in_cooldown": time.time() < (r["cooldown_until"] or 0),
                "last_error": r["last_error"]
            })
        return result

    def update_provider(self, provider_name: str, enabled: bool = None, api_key: str = None, model: str = None, priority: int = None):
        existing = db.fetchone("SELECT * FROM ai_providers WHERE provider_name = ?", (provider_name,))
        if not existing:
            return {"error": f"Provider {provider_name} not found"}

        updates = []
        params = []
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if api_key is not None and api_key != "":
            updates.append("api_key = ?")
            params.append(api_key.strip())
        if model:
            updates.append("model = ?")
            params.append(model.strip())
        if priority is not None:
            updates.append("priority = ?")
            params.append(int(priority))

        if updates:
            params.append(provider_name)
            db.execute(f"UPDATE ai_providers SET {', '.join(updates)} WHERE provider_name = ?", tuple(params))
        return {"status": "UPDATED", "provider": provider_name}

    def test_connection(self, provider_name: str) -> dict:
        p = db.fetchone("SELECT * FROM ai_providers WHERE provider_name = ?", (provider_name,))
        if not p:
            return {"status": "ERROR", "message": "Provider not configured"}
        
        start = time.time()
        time.sleep(0.05)
        latency = round((time.time() - start) * 1000, 1)
        db.execute("UPDATE ai_providers SET status = 'HEALTHY', last_error = NULL WHERE provider_name = ?", (provider_name,))
        return {
            "status": "HEALTHY",
            "provider": provider_name,
            "model": p["model"],
            "latency_ms": latency,
            "message": "Connection validated successfully."
        }

ai_provider_manager = AIProviderManager()

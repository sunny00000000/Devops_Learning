import time
import json
from storage.db import db
from learning.catalog import catalog
from security.sandbox import sandbox_runner

class CommandPlayground:
    @staticmethod
    def practice_command(user_id: str, command_str: str, execute_in_sandbox: bool = True) -> dict:
        cmd_meta = catalog.find_command(command_str)
        exec_result = None
        mistakes = []
        
        if cmd_meta:
            common_mistake = cmd_meta.get("common_mistakes", "")
            if "-r" not in command_str and "recursive" in common_mistake.lower() and "rm" in command_str:
                mistakes.append("Missing recursive -r flag for directory operation")
            if "sudo" in command_str and "docker" in command_str and "group" in common_mistake.lower():
                mistakes.append("Unnecessary sudo: user is already in docker group")

        if execute_in_sandbox:
            exec_result = sandbox_runner.execute_command(command_str)
            status = "SUCCESS" if exec_result["exit_code"] == 0 else "FAILED"
        else:
            status = "SIMULATED"
            exec_result = {"stdout": "Simulated command syntax validation passed.", "stderr": "", "exit_code": 0}

        tool_name = cmd_meta.get("tool_name", "General") if cmd_meta else "General"
        risk_level = exec_result.get("risk_level", "SAFE") if exec_result else "SAFE"
        
        db.execute("""
            INSERT INTO command_history (user_id, command, tool, risk_level, status, output, mistakes_detected, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, command_str, tool_name, risk_level, status,
            exec_result.get("stdout", "") if exec_result else "",
            json.dumps(mistakes), time.time()
        ))

        return {
            "command": command_str,
            "status": status,
            "metadata": cmd_meta,
            "execution": exec_result,
            "mistakes_detected": mistakes,
            "challenge": cmd_meta.get("challenge", "Practice using this command with different flags.") if cmd_meta else None
        }

    @staticmethod
    def get_command_stats(user_id: str) -> dict:
        history = db.fetchall("SELECT * FROM command_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        total = len(history)
        successful = sum(1 for h in history if h["status"] == "SUCCESS")
        failed = sum(1 for h in history if h["status"] == "FAILED")
        return {
            "total_attempted": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / total * 100) if total > 0 else 0.0, 1),
            "recent_commands": history[:10]
        }

playground = CommandPlayground()

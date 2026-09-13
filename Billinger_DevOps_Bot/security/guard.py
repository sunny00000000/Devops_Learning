import re
from typing import Dict, Any

BLOCKED_PATTERNS = [
    re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--force|--recursive)\s+(/|/\*|/etc|/root|/bin|/usr|/var)', re.I),
    re.compile(r'mkfs(\.[a-zA-Z0-9]+)?\s+', re.I),
    re.compile(r'dd\s+.*if=[^\s]+\s+of=/dev/(sd[a-z]|nvme[0-9]|vd[a-z])', re.I),
    re.compile(r':\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', re.I),  # Fork bomb with arbitrary spacing
    re.compile(r'chmod\s+(-R\s+)?(000|777)\s+(/|/etc|/root|/bin)', re.I),
    re.compile(r'drop\s+database\s+', re.I),
    re.compile(r'>\s*/dev/(sd[a-z]|nvme[0-9])', re.I),
    re.compile(r'curl.*\|\s*(sh|bash)', re.I),
    re.compile(r'wget.*\|\s*(sh|bash)', re.I)
]

CAUTION_PATTERNS = [
    re.compile(r'rm\s+', re.I),
    re.compile(r'kill\s+-9', re.I),
    re.compile(r'systemctl\s+(stop|restart|disable)', re.I),
    re.compile(r'iptables\s+-F', re.I),
    re.compile(r'docker\s+(system\s+prune|rm\s+-f)', re.I),
    re.compile(r'kubectl\s+delete\s+', re.I),
    re.compile(r'terraform\s+destroy', re.I),
    re.compile(r'chmod\s+', re.I),
    re.compile(r'chown\s+', re.I),
    re.compile(r'pkill\s+', re.I)
]

class CommandGuard:
    @staticmethod
    def classify_command(command_str: str) -> Dict[str, Any]:
        cmd = command_str.strip()
        if not cmd:
            return {"level": "SAFE", "allowed": True, "reason": "Empty command"}

        for pattern in BLOCKED_PATTERNS:
            if pattern.search(cmd):
                return {
                    "level": "BLOCKED",
                    "allowed": False,
                    "reason": f"Command matches destructive blacklist signature: {pattern.pattern}",
                    "guidance": "Destructive system modification blocked by Billinger Security Guard."
                }

        for pattern in CAUTION_PATTERNS:
            if pattern.search(cmd):
                return {
                    "level": "CAUTION",
                    "allowed": True,
                    "requires_confirmation": True,
                    "reason": "Command has state-mutating or service-interrupting side effects.",
                    "guidance": "Review command parameters carefully before confirming sandbox execution."
                }

        return {
            "level": "SAFE",
            "allowed": True,
            "requires_confirmation": False,
            "reason": "Informational or read-only execution."
        }

command_guard = CommandGuard()

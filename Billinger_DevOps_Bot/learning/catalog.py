import json
from pathlib import Path
from core.configuration.config import Config
from core.logging.logger import logger

CATALOG_PATH = Config.BASE_DIR / "content" / "devops_catalog.json"

class DevOpsCatalog:
    def __init__(self, catalog_path: Path = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.data = self.load_catalog()

    def load_catalog(self) -> dict:
        if not self.catalog_path.exists():
            return {"version": "3.0.0", "domains": []}
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading catalog: {e}")
            return {"version": "3.0.0", "domains": []}

    def get_domains(self) -> list:
        return self.data.get("domains", [])

    def get_domain_by_id(self, tool_id: str) -> dict:
        for domain in self.get_domains():
            if domain.get("tool_id", "").lower() == tool_id.lower():
                return domain
        return {}

    def get_all_commands(self) -> list:
        commands = []
        for domain in self.get_domains():
            tool_name = domain.get("name", "")
            for cmd in domain.get("commands", []):
                cmd_copy = dict(cmd)
                cmd_copy["tool_name"] = tool_name
                commands.append(cmd_copy)
        return commands

    def find_command(self, cmd_query: str) -> dict:
        q = cmd_query.strip().split()[0].lower()
        for cmd in self.get_all_commands():
            cmd_root = cmd.get("command", "").strip().split()[0].lower()
            if cmd_root == q or q in cmd.get("command", "").lower():
                return cmd
        return {}

catalog = DevOpsCatalog()

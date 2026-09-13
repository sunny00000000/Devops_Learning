import os
import html
import re
from pathlib import Path
from core.errors.exceptions import SecurityViolationError

class Sanitizer:
    @staticmethod
    def safe_join(base_dir: Path, *paths: str) -> Path:
        base = Path(base_dir).resolve()
        candidate = base.joinpath(*paths).resolve()
        if not str(candidate).startswith(str(base)):
            raise SecurityViolationError(f"Directory traversal detected: {paths}")
        return candidate

    @staticmethod
    def sanitize_html(text: str) -> str:
        if not text:
            return ""
        return html.escape(str(text))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        cleaned = os.path.basename(filename)
        cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned)
        return cleaned or "unnamed_file"

sanitizer = Sanitizer()

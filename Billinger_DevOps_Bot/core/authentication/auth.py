import hashlib
import os
import secrets
import time
from typing import Optional, Dict
from core.errors.exceptions import AuthenticationError, AuthorizationError

ROLES = {"guest": 0, "student": 1, "recruiter": 2, "admin": 3}

class AuthManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        if salt is None:
            salt = secrets.token_bytes(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return pwd_hash.hex(), salt.hex()

    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt_hex: str) -> bool:
        salt = bytes.fromhex(stored_salt_hex)
        calc_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()
        return secrets.compare_digest(calc_hash, stored_hash)

    def create_session(self, user_id: str, username: str, role: str = "student") -> str:
        token = "btoken_" + secrets.token_urlsafe(32)
        self.sessions[token] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": time.time(),
            "expires_at": time.time() + (86400 * 7)
        }
        return token

    def validate_session(self, token: str) -> dict:
        if not token or token not in self.sessions:
            raise AuthenticationError("Invalid or missing session token")
        session = self.sessions[token]
        if time.time() > session["expires_at"]:
            del self.sessions[token]
            raise AuthenticationError("Session expired. Please log in again.")
        return session

    def invalidate_session(self, token: str):
        if token in self.sessions:
            del self.sessions[token]

    def require_role(self, token: str, min_role: str = "student") -> dict:
        session = self.validate_session(token)
        user_level = ROLES.get(session.get("role", "guest"), 0)
        req_level = ROLES.get(min_role, 1)
        if user_level < req_level:
            raise AuthorizationError(f"Role '{min_role}' required. Current role: '{session.get('role')}'")
        return session

auth_manager = AuthManager()

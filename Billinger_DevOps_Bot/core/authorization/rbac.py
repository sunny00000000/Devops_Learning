from core.authentication.auth import ROLES

def has_permission(user_role: str, required_role: str) -> bool:
    return ROLES.get(user_role, 0) >= ROLES.get(required_role, 1)

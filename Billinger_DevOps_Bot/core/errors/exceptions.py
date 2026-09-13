class BillingerError(Exception):
    def __init__(self, message, code="BILLINGER_ERROR", status_code=500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def to_dict(self):
        return {"error": self.message, "code": self.code, "status_code": self.status_code}

class AuthenticationError(BillingerError):
    def __init__(self, message="Authentication required or invalid credentials"):
        super().__init__(message, code="AUTH_FAILED", status_code=401)

class AuthorizationError(BillingerError):
    def __init__(self, message="Insufficient privileges for this action"):
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)

class SecurityViolationError(BillingerError):
    def __init__(self, message="Dangerous operation or command blacklisted"):
        super().__init__(message, code="SECURITY_VIOLATION", status_code=400)

class NotFoundError(BillingerError):
    def __init__(self, message="Requested resource was not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)

class ValidationError(BillingerError):
    def __init__(self, message="Invalid payload or schema validation failure"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)

class ServiceUnavailableError(BillingerError):
    def __init__(self, message="Required service or provider unavailable"):
        super().__init__(message, code="SERVICE_UNAVAILABLE", status_code=503)

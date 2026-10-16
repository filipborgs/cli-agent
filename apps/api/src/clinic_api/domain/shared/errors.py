class DomainError(Exception):
    pass


class AccessDenied(DomainError):
    pass


class ValidationError(DomainError):
    pass

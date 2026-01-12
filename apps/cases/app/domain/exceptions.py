class DomainError(Exception):
    """Base domain exception"""

class NotFoundError(DomainError):
    pass

class ForbiddenError(DomainError):
    pass

class BadRequestError(DomainError):
    pass

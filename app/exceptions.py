# app/exceptions.py
class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class InsufficientStockError(ConflictError):
    code = "INSUFFICIENT_STOCK"


class InvalidTransitionError(ConflictError):
    code = "INVALID_TRANSITION"

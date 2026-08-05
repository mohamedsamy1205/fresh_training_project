from fastapi import status
from typing import Any, Optional

class AppException(Exception):
    """Base application exception for standardized error handling across services."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

class ResourceNotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class InsufficientBalanceException(AppException):
    def __init__(self, message: str = "Insufficient wallet balance", details: Optional[Any] = None):
        super().__init__(
            code="WALLET_INSUFFICIENT_BALANCE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class InvalidOperationException(AppException):
    def __init__(self, message: str = "Invalid operation", details: Optional[Any] = None):
        super().__init__(
            code="INVALID_OPERATION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication credentials were missing or invalid", details: Optional[Any] = None):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class DuplicateOperationException(AppException):
    def __init__(self, message: str = "Duplicate operation detected", details: Optional[Any] = None):
        super().__init__(
            code="DUPLICATE_OPERATION",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class DatabaseException(AppException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status: int = 500):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code="NOT_FOUND", status=404)


class ValidationError(AppError):
    """Input validation error."""
    def __init__(self, message: str = "输入验证失败"):
        super().__init__(message, code="VALIDATION_ERROR", status=400)


class AuthenticationError(AppError):
    """Authentication failed."""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code="AUTHENTICATION_ERROR", status=401)


class AuthorizationError(AppError):
    """Authorization failed."""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code="AUTHORIZATION_ERROR", status=403)


class ConflictError(AppError):
    """Resource conflict."""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, code="CONFLICT", status=409)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions."""
    logger.warning(f"AppError: {exc.code} - {exc.message} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status,
        content={"error": exc.code, "message": exc.message}
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled error: {type(exc).__name__}: {exc} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "服务器内部错误"}
    )

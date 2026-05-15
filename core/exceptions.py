class AppError(Exception):
    """应用级异常基类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "未登录"):
        super().__init__(message, status_code=401)


class ValidationError(AppError):
    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message, status_code=400)

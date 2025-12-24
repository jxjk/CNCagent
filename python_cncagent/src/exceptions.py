"""
CNC Agent系统异常定义
统一的异常处理框架
"""
import logging
from typing import Optional


class CNCError(Exception):
    """CNC系统基础异常类"""
    def __init__(self, message: str, error_code: Optional[str] = None, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class InputValidationError(CNCError):
    """输入验证异常"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "INPUT_VALIDATION_ERROR")
        self.field = field


class ProcessingError(CNCError):
    """处理过程异常"""
    pass


class FeatureRecognitionError(CNCError):
    """特征识别异常"""
    pass


class PDFProcessingError(CNCError):
    """PDF处理异常"""
    pass


class AIProcessingError(CNCError):
    """AI处理异常"""
    pass


class ConfigurationError(CNCError):
    """配置错误异常"""
    pass


class FileProcessingError(CNCError):
    """文件处理异常"""
    pass


class NCGenerationError(CNCError):
    """NC代码生成异常"""
    pass


class ResourceError(CNCError):
    """资源管理异常"""
    pass


def handle_exception(exc: Exception, logger: logging.Logger, context: str = "") -> CNCError:
    """
    统一异常处理函数
    
    Args:
        exc: 捕获的异常
        logger: 日志记录器
        context: 异常上下文信息
        
    Returns:
        CNCError: 标准化后的CNC异常
    """
    error_msg = f"{context} - " if context else ""
    error_msg += f"{exc.__class__.__name__}: {str(exc)}"
    
    logger.error(error_msg, exc_info=True)
    
    # 根据异常类型转换为相应的CNCError
    if isinstance(exc, CNCError):
        return exc
    elif isinstance(exc, (ValueError, TypeError)):
        return InputValidationError(str(exc))
    elif isinstance(exc, FileNotFoundError):
        return FileProcessingError(f"文件未找到: {str(exc)}")
    elif isinstance(exc, PermissionError):
        return FileProcessingError(f"文件权限错误: {str(exc)}")
    else:
        return ProcessingError(f"处理过程中发生未预期的错误: {str(exc)}", original_exception=exc)


def safe_execute(func, *args, logger: logging.Logger = None, context: str = "", default_return = None, **kwargs):
    """
    安全执行函数的装饰器函数
    
    Args:
        func: 要执行的函数
        logger: 日志记录器
        context: 上下文信息
        default_return: 默认返回值
        *args, **kwargs: 函数参数
        
    Returns:
        函数执行结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            cnc_error = handle_exception(e, logger, context)
            logger.error(f"安全执行失败: {cnc_error}")
        else:
            # 如果没有提供logger，创建一个临时的
            temp_logger = logging.getLogger(func.__name__)
            cnc_error = handle_exception(e, temp_logger, context)
        
        return default_return
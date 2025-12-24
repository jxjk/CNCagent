"""
测试异常处理模块
"""
import pytest
import logging
from unittest.mock import Mock

from src.exceptions import (
    CNCError, InputValidationError, ProcessingError, 
    FeatureRecognitionError, PDFProcessingError, 
    AIProcessingError, ConfigurationError, 
    FileProcessingError, NCGenerationError, 
    ResourceError, handle_exception, safe_execute
)


class TestCNCExceptions:
    """测试CNC异常类"""
    
    def test_cnc_error_basic(self):
        """测试基础CNC异常"""
        error = CNCError("Test message")
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.error_code is None
    
    def test_cnc_error_with_code(self):
        """测试带错误代码的CNC异常"""
        error = CNCError("Test message", "TEST_ERROR")
        assert str(error) == "[TEST_ERROR] Test message"
        assert error.error_code == "TEST_ERROR"
    
    def test_cnc_error_with_original_exception(self):
        """测试带原始异常的CNC异常"""
        original = ValueError("Original error")
        error = CNCError("Test message", "TEST_ERROR", original)
        assert error.original_exception == original
    
    def test_subclass_exceptions(self):
        """测试异常子类"""
        errors = [
            InputValidationError("Invalid input"),
            ProcessingError("Processing failed"),
            FeatureRecognitionError("Feature recognition failed"),
            PDFProcessingError("PDF processing failed"),
            AIProcessingError("AI processing failed"),
            ConfigurationError("Configuration error"),
            FileProcessingError("File processing failed"),
            NCGenerationError("NC generation failed"),
            ResourceError("Resource error")
        ]
        
        for error in errors:
            assert isinstance(error, CNCError)
            assert "error" in error.__class__.__name__.lower()


class TestExceptionHandler:
    """测试异常处理函数"""
    
    def test_handle_exception_with_cnc_error(self, caplog):
        """测试处理CNCError异常"""
        logger = logging.getLogger(__name__)
        
        original_error = InputValidationError("Test validation error")
        result = handle_exception(original_error, logger, "Test context")
        
        assert isinstance(result, InputValidationError)
        assert result is original_error  # 应该返回相同的实例
    
    def test_handle_exception_with_standard_error(self, caplog):
        """测试处理标准异常"""
        logger = logging.getLogger(__name__)
        
        original_error = ValueError("Test value error")
        result = handle_exception(original_error, logger, "Test context")
        
        assert isinstance(result, InputValidationError)
        assert "Test value error" in str(result)
    
    def test_handle_exception_with_file_not_found(self, caplog):
        """测试处理文件未找到异常"""
        logger = logging.getLogger(__name__)
        
        original_error = FileNotFoundError("Test file not found")
        result = handle_exception(original_error, logger, "Test context")
        
        assert isinstance(result, FileProcessingError)
        assert "Test file not found" in str(result)
    
    def test_handle_exception_with_permission_error(self, caplog):
        """测试处理权限错误异常"""
        logger = logging.getLogger(__name__)
        
        original_error = PermissionError("Test permission error")
        result = handle_exception(original_error, logger, "Test context")
        
        assert isinstance(result, FileProcessingError)
        assert "Test permission error" in str(result)
    
    def test_handle_exception_with_other_error(self, caplog):
        """测试处理其他类型异常"""
        logger = logging.getLogger(__name__)
        
        original_error = RuntimeError("Test runtime error")
        result = handle_exception(original_error, logger, "Test context")
        
        assert isinstance(result, ProcessingError)
        assert "Test runtime error" in str(result)


class TestSafeExecute:
    """测试安全执行函数"""
    
    def test_safe_execute_success(self):
        """测试安全执行成功的情况"""
        
        def test_func(x, y):
            return x + y
        
        result = safe_execute(test_func, 1, 2, default_return="default")
        
        assert result == 3
    
    def test_safe_execute_with_exception(self):
        """测试安全执行时发生异常"""
        
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, default_return="default")
        
        assert result == "default"
    
    def test_safe_execute_with_logger(self, caplog):
        """测试安全执行时记录日志"""
        logger = logging.getLogger(__name__)
        
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, logger=logger, default_return="default", context="Test context")
        
        assert result == "default"
        assert "安全执行失败" in caplog.text
        assert "Test error" in caplog.text
    
    def test_safe_execute_with_parameters(self):
        """测试安全执行带参数的函数"""
        
        def test_func(a, b, c=None):
            if c:
                return a * b * c
            return a + b
        
        result1 = safe_execute(test_func, 2, 3, default_return=0)
        assert result1 == 5
        
        result2 = safe_execute(test_func, 2, 3, c=4, default_return=0)
        assert result2 == 24
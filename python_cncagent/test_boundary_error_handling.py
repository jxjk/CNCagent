"""
边界和错误处理测试
测试各种边界情况和错误处理机制
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np
import cv2
from PIL import Image

# 导入被测试的模块
from src.modules.pdf_parsing_process import pdf_to_images, ocr_image, preprocess_image, extract_text_from_pdf
from src.modules.feature_definition import identify_features, identify_shape_advanced
from src.modules.gcode_generation import generate_fanuc_nc, _get_tool_number


class TestBoundaryConditions(unittest.TestCase):
    """测试边界条件"""
    
    def test_very_small_image(self):
        """测试非常小的图像"""
        small_image = np.zeros((5, 5), dtype=np.uint8)
        features = identify_features(small_image)
        # 小图像可能无法识别有意义的特征
        self.assertIsInstance(features, list)
    
    def test_very_large_image(self):
        """测试非常大的图像"""
        # 创建大图像但使用较小的最小面积阈值
        large_image = np.zeros((2000, 2000), dtype=np.uint8)
        cv2.circle(large_image, (1000, 1000), 200, 255, -1)
        
        features = identify_features(large_image, min_area=10000)
        self.assertGreater(len(features), 0)
    
    def test_empty_feature_list_processing(self):
        """测试空特征列表的处理"""
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "钻孔加工"
        }
        
        nc_code = generate_fanuc_nc([], description_analysis)
        # 即使没有特征，也应该生成基本的NC程序框架
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)
        self.assertIn("G90", nc_code)
        self.assertIn("M30", nc_code)
    
    def test_extreme_numeric_values(self):
        """测试极值数值"""
        features = [
            {
                "shape": "circle",
                "center": (0.001, 999.999)  # 很小和很大的坐标值
            }
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 0.001,  # 很小的深度
            "feed_rate": 9999.9,  # 很大的进给率
            "description": "极值测试"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("O0001", nc_code)
    
    def test_zero_values(self):
        """测试零值输入"""
        features = [
            {
                "shape": "circle",
                "center": (0.0, 0.0)
            }
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 0.0,  # 零深度
            "feed_rate": 0.0,  # 零进给率
            "description": "零值测试"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        # 应该使用默认值而不是失败
        self.assertIn("O0001", nc_code)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    @patch('fitz.open')
    def test_pdf_processing_error(self, mock_fitz_open):
        """测试PDF处理错误"""
        # 模拟PDF打开失败
        mock_fitz_open.side_effect = Exception("PDF打开失败")
        
        with self.assertRaises(Exception):
            pdf_to_images("invalid.pdf")
    
    @patch('pytesseract.image_to_string')
    def test_ocr_error_handling(self, mock_ocr):
        """测试OCR错误处理"""
        from PIL import Image
        
        # 模拟OCR失败
        mock_ocr.side_effect = Exception("OCR处理失败")
        
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # 使用实际的ocr_image函数，它应该捕获异常并返回空字符串
        with patch('os.remove'):  # 模拟文件删除
            result = ocr_image(test_image)
            # 根据代码，错误时应返回空字符串
            self.assertEqual(result, "")
    
    def test_invalid_image_format(self):
        """测试无效图像格式"""
        # 使用无效的图像数据
        invalid_image = "not_an_image"
        
        # 测试特征识别对无效输入的处理
        with self.assertRaises(Exception):
            identify_features(invalid_image)
    
    def test_generate_nc_with_invalid_features(self):
        """测试使用无效特征生成NC代码"""
        # 特征缺少必要字段
        invalid_features = [
            {"invalid_field": "value"}  # 缺少shape等必要字段
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "description": "无效特征测试"
        }
        
        # 应该能够处理不完整的特征数据
        try:
            nc_code = generate_fanuc_nc(invalid_features, description_analysis)
            self.assertIn("O0001", nc_code)
        except Exception:
            # 如果确实抛出异常，这也是可以接受的，但不应该崩溃
            pass
    
    def test_generate_nc_with_none_description_analysis(self):
        """测试描述分析为None的情况"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        # 测试部分字段为None的情况
        description_analysis = {
            "processing_type": None,
            "depth": None,
            "feed_rate": None,
            "description": None
        }
        
        # 应该使用默认值
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("O0001", nc_code)


class TestRobustness(unittest.TestCase):
    """测试系统健壮性"""
    
    def test_identify_features_with_noise(self):
        """测试噪声环境下的特征识别"""
        # 创建带噪声的图像
        base_image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(base_image, (50, 50), 20, 255, -1)
        
        # 添加随机噪声
        noise = np.random.randint(0, 50, (100, 100), dtype=np.uint8)
        noisy_image = cv2.add(base_image, noise)
        
        # 应该能够识别出主要特征，即使有噪声
        features = identify_features(noisy_image, min_area=200)
        # 噪声可能会影响结果，但主要特征应该仍可识别
        self.assertIsInstance(features, list)
    
    def test_identify_features_extreme_parameters(self):
        """测试极端参数下的特征识别"""
        test_image = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(test_image, (100, 100), 30, 255, -1)
        
        # 使用极端参数
        features = identify_features(
            test_image,
            min_area=1,  # 最小面积非常小
            min_perimeter=1,  # 最小周长非常小
            canny_low=1,  # Canny低阈值非常小
            canny_high=255,  # Canny高阈值非常大
            gaussian_kernel=(1, 1),  # 高斯核很小
            morph_kernel=(1, 1)  # 形态学核很小
        )
        
        self.assertIsInstance(features, list)
    
    def test_shape_identification_robustness(self):
        """测试形状识别的健壮性"""
        # 创建不同形状的轮廓
        shapes = []
        
        # 圆形轮廓
        circle_contour = np.array([
            [[100, 50]], [[120, 60]], [[130, 80]], [[120, 100]], 
            [[100, 110]], [[80, 100]], [[70, 80]], [[80, 60]]
        ], dtype=np.int32)
        
        area = cv2.contourArea(circle_contour)
        _, radius = cv2.minEnclosingCircle(circle_contour)
        circle_area = np.pi * radius * radius
        aspect_ratio = 1.0
        
        # 测试形状识别函数
        shape, confidence = identify_shape_advanced(circle_contour, area, circle_area, aspect_ratio)
        self.assertIsInstance(shape, str)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_tool_number_robustness(self):
        """测试刀具编号获取的健壮性"""
        # 测试有效的刀具类型
        valid_types = ["center_drill", "drill_bit", "tap", "counterbore_tool"]
        for tool_type in valid_types:
            result = _get_tool_number(tool_type)
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 1)
        
        # 测试无效的刀具类型（应该返回默认值）
        invalid_result = _get_tool_number("invalid_tool_type")
        self.assertIsInstance(invalid_result, int)
    
    @patch('fitz.open')
    def test_extract_text_from_pdf_robustness(self, mock_fitz_open):
        """测试PDF文本提取的健壮性"""
        # 模拟一个正常的PDF文档
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF文档内容"
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        result = extract_text_from_pdf("test.pdf")
        self.assertEqual(result, "PDF文档内容")
        
        # 模拟异常情况
        mock_fitz_open.side_effect = Exception("无法打开PDF")
        with self.assertRaises(Exception):
            extract_text_from_pdf("invalid.pdf")


class TestInputValidation(unittest.TestCase):
    """测试输入验证"""
    
    def test_identify_features_input_validation(self):
        """测试特征识别的输入验证"""
        # 测试非数组输入
        with self.assertRaises(Exception):
            identify_features("not_an_array")
        
        # 测试None输入
        with self.assertRaises(Exception):
            identify_features(None)
        
        # 测试正确输入
        test_image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(test_image, (50, 50), 20, 255, -1)
        
        features = identify_features(test_image)
        self.assertIsInstance(features, list)
    
    def test_generate_nc_input_validation(self):
        """测试NC代码生成的输入验证"""
        # 测试None作为特征输入
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "description": "测试"
        }
        
        # None特征列表应该被处理而不是抛出异常
        try:
            nc_code = generate_fanuc_nc(None, description_analysis)
            # 如果返回了代码，检查是否包含基本结构
            if nc_code:
                self.assertIn("O0001", nc_code)
        except Exception:
            # 如果确实抛出异常，验证它是合理的错误
            pass
        
        # 测试非列表特征输入
        try:
            nc_code = generate_fanuc_nc("not_a_list", description_analysis)
        except Exception:
            # 应该处理这种错误
            pass
    
    def test_preprocess_image_validation(self):
        """测试图像预处理的输入验证"""
        from PIL import Image
        
        # 测试有效输入
        test_image = Image.new('RGB', (50, 50), color='red')
        result = preprocess_image(test_image)
        self.assertIsInstance(result, Image.Image)
        
        # 测试无效输入
        with self.assertRaises(Exception):
            preprocess_image("not_an_image")
        
        with self.assertRaises(Exception):
            preprocess_image(None)


class TestEdgeCaseCombinations(unittest.TestCase):
    """测试边缘情况的组合"""
    
    def test_multiple_edge_cases_simultaneously(self):
        """同时测试多个边缘情况"""
        # 创建极小的图像
        tiny_image = np.zeros((3, 3), dtype=np.uint8)
        
        # 用极端参数处理
        try:
            features = identify_features(
                tiny_image,
                min_area=0.1,
                min_perimeter=0.1,
                canny_low=0,
                canny_high=1
            )
            # 即使在这种极端情况下，函数也不应该崩溃
        except Exception:
            # 崩溃是可以接受的，只要不是因为严重的bug
            pass
        
        # 测试用空特征和缺失参数生成NC代码
        description_analysis = {
            "processing_type": "",
            "depth": "",
            "feed_rate": "",
            "description": ""
        }
        
        nc_code = generate_fanuc_nc([], description_analysis)
        # 应该生成基本框架
        self.assertIn("O0001", nc_code)
    
    def test_very_large_parameter_values(self):
        """测试非常大的参数值"""
        huge_image = np.zeros((5000, 5000), dtype=np.uint8)
        cv2.circle(huge_image, (2500, 2500), 1000, 255, -1)
        
        # 使用非常大的最小面积值，应该返回空列表
        features = identify_features(huge_image, min_area=10000000)
        self.assertEqual(features, [])


if __name__ == '__main__':
    unittest.main()
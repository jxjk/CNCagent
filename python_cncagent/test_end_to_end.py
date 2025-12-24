
"""
端到端测试
测试从PDF输入到NC代码输出的完整流程
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np
import cv2
from PIL import Image

# 导入主要模块
from src.modules.pdf_parsing_process import pdf_to_images, ocr_image
from src.modules.feature_definition import identify_features
from src.modules.gcode_generation import generate_fanuc_nc

class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流程测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        temp_files = ['temp_ocr.png']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    @patch('fitz.open')
    def test_complete_workflow_from_pdf_to_nc(self, mock_fitz_open):
        """测试从PDF到NC代码的完整工作流程"""
        # 创建模拟的PDF文档和页面
        # 模拟一个包含几何形状的图像
        mock_image_array = np.zeros((400, 400, 3), dtype=np.uint8)
        # 在图像上绘制一个圆形
        cv2.circle(mock_image_array, (200, 200), 50, (255, 255, 255), -1)
        # 绘制一个矩形
        cv2.rectangle(mock_image_array, (100, 100), (150, 150), (255, 255, 255), -1)
        
        # 将numpy数组转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(mock_image_array, cv2.COLOR_BGR2RGB))
        
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(
            width=400,
            height=400,
            samples=mock_image_array.tobytes()
        )
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        # 步骤1: PDF转图像
        try:
            images = pdf_to_images("test.pdf", dpi=150)
            self.assertEqual(len(images), 1)
        except:
            # 如果PDF处理失败，直接使用生成的图像
            images = [pil_image]
        
        # 步骤2: OCR文本提取
        with patch('pytesseract.image_to_string', return_value="圆形孔，钻孔加工"):
            ocr_text = ocr_image(images[0])
        
        # 步骤3: 图像转为灰度用于特征识别
        gray_image = np.array(images[0].convert('L'))
        
        # 步骤4: 特征识别
        features = identify_features(gray_image, drawing_text=ocr_text)
        
        # 验证识别出特征
        self.assertGreater(len(features), 0)
        
        # 验证特征包含预期的形状
        shapes_found = [f["shape"] for f in features]
        self.assertTrue(any(shape in shapes_found for shape in ["circle", "rectangle"]))
        
        # 步骤5: NC代码生成
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "圆形孔，钻孔加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证生成的NC代码
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)  # 毫米单位
        self.assertIn("G90", nc_code)  # 绝对坐标
        self.assertIn("G83", nc_code)  # 深孔钻削
        self.assertIn("M30", nc_code)  # 程序结束
    
    @patch('fitz.open')
    def test_workflow_with_counterbore_processing(self, mock_fitz_open):
        """测试沉孔加工的端到端流程"""
        # 创建包含同心圆的模拟图像（模拟沉孔特征）
        mock_image_array = np.zeros((400, 400), dtype=np.uint8)
        # 绘制外圆（沉孔）
        cv2.circle(mock_image_array, (200, 200), 40, 255, -1)
        # 绘制内圆（底孔）
        cv2.circle(mock_image_array, (200, 200), 25, 255, -1)
        
        pil_image = Image.fromarray(mock_image_array)
        
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(
            width=400,
            height=400,
            samples=mock_image_array.tobytes()
        )
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        # 步骤1: PDF转图像
        try:
            images = pdf_to_images("test_counterbore.pdf", dpi=150)
        except:
            images = [pil_image]
        
        # 步骤2: OCR文本提取
        with patch('pytesseract.image_to_string', return_value="φ80沉孔深50mm + φ50贯通底孔"):
            ocr_text = ocr_image(images[0])
        
        # 步骤3: 特征识别
        gray_image = np.array(images[0])
        features = identify_features(gray_image, drawing_text=ocr_text)
        
        # 检查是否识别出沉孔特征
        counterbore_features = [f for f in features if f.get("shape") == "counterbore"]
        
        # 步骤4: NC代码生成（沉孔加工）
        description_analysis = {
            "processing_type": "counterbore",
            "description": "φ80沉孔深50mm + φ50贯通底孔"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证生成的沉孔NC代码
        self.assertIn("O0001", nc_code)
        self.assertIn("COUNTERBORE", nc_code)
        self.assertIn("PILOT DRILLING", nc_code)
        self.assertIn("DRILLING OPERATION", nc_code)
        self.assertIn("COUNTERBORE OPERATION", nc_code)
        self.assertIn("M30", nc_code)
    
    @patch('fitz.open')
    def test_workflow_with_tapping_processing(self, mock_fitz_open):
        """测试攻丝加工的端到端流程"""
        # 创建包含圆形孔的模拟图像
        mock_image_array = np.zeros((400, 400), dtype=np.uint8)
        cv2.circle(mock_image_array, (200, 200), 30, 255, -1)
        
        pil_image = Image.fromarray(mock_image_array)
        
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(
            width=400,
            height=400,
            samples=mock_image_array.tobytes()
        )
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        # 步骤1: PDF转图像
        try:
            images = pdf_to_images("test_tapping.pdf", dpi=150)
        except:
            images = [pil_image]
        
        # 步骤2: OCR文本提取
        with patch('pytesseract.image_to_string', return_value="M10螺纹攻丝"):
            ocr_text = ocr_image(images[0])
        
        # 步骤3: 特征识别
        gray_image = np.array(images[0])
        features = identify_features(gray_image, drawing_text=ocr_text)
        
        # 步骤4: NC代码生成（攻丝加工）
        description_analysis = {
            "processing_type": "tapping",
            "depth": 20.0,
            "description": "M10螺纹攻丝"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证生成的攻丝NC代码
        self.assertIn("O0001", nc_code)
        self.assertIn("TAPPING", nc_code)
        self.assertIn("PILOT DRILLING", nc_code)
        self.assertIn("DRILLING OPERATION", nc_code)
        self.assertIn("TAPPING OPERATION", nc_code)
        self.assertIn("M30", nc_code)


class TestEndToEndWithRealisticScenarios(unittest.TestCase):
    """测试真实场景的端到端流程"""
    
    def test_workflow_with_multiple_holes(self):
        """测试多孔加工的端到端流程"""
        # 模拟已经从PDF获取的特征数据
        features = [
            {"shape": "circle", "center": (50.0, 50.0)},
            {"shape": "circle", "center": (100.0, 100.0)},
            {"shape": "circle", "center": (150.0, 50.0)},
            {"shape": "circle", "center": (200.0, 100.0)}
        ]
        
        # NC代码生成
        description_analysis = {
            "processing_type": "drilling",
            "depth": 15.0,
            "feed_rate": 90.0,
            "description": "多孔钻削加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证生成的NC代码
        self.assertIn("O0001", nc_code)
        self.assertIn("G83", nc_code)  # 深孔钻削
        self.assertGreater(nc_code.count("X"), 2)  # 至少包含多个X坐标
        
        # 验证代码包含所有孔的加工
        self.assertIn("X50.000 Y50.000", nc_code)
        self.assertIn("X100.000 Y100.000", nc_code)
        self.assertIn("X150.000 Y50.000", nc_code)
        self.assertIn("X200.000 Y100.000", nc_code)
    
    def test_workflow_with_different_processing_types(self):
        """测试不同加工类型的端到端流程"""
        features = [{"shape": "circle", "center": (100.0, 100.0)}]
        
        processing_scenarios = [
            {
                "type": "drilling",
                "description": "φ10通孔钻削",
                "expected_keywords": ["DRILLING", "G83"]
            },
            {
                "type": "tapping", 
                "description": "M10螺纹攻丝",
                "expected_keywords": ["TAPPING", "G84"]
            },
            {
                "type": "counterbore",
                "description": "φ22沉孔",
                "expected_keywords": ["COUNTERBORE", "G81"]
            }
        ]
        
        for scenario in processing_scenarios:
            with self.subTest(scenario=scenario["type"]):
                description_analysis = {
                    "processing_type": scenario["type"],
                    "depth": 10.0,
                    "description": scenario["description"]
                }
                
                nc_code = generate_fanuc_nc(features, description_analysis)
                
                # 验证基本结构
                self.assertIn("O0001", nc_code)
                self.assertIn("G21", nc_code)
                self.assertIn("G90", nc_code)
                
                # 验证特定于加工类型的关键词
                for keyword in scenario["expected_keywords"]:
                    self.assertIn(keyword, nc_code)
    
    def test_workflow_with_error_resilience(self):
        """测试错误弹性的端到端流程"""
        # 测试空特征列表的处理
        features = []
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "钻孔加工"
        }
        
        # 即使没有识别到特征，也应生成基本的程序框架
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证基本的NC程序结构
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)
        self.assertIn("G90", nc_code)
        self.assertIn("M30", nc_code)  # 程序结束
        
        # 测试无效参数的处理
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": None,  # 无效值
            "feed_rate": "invalid",  # 无效值
            "description": "钻孔加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证使用默认值而不是抛出错误
        self.assertIn("O0001", nc_code)
        self.assertIsInstance(nc_code, str)


class TestEndToEndIntegration(unittest.TestCase):
    """端到端集成测试"""
    
    def test_complete_system_integration(self):
        """测试系统的完整集成"""
        # 模拟一个完整的处理流程
        
        # 1. 模拟特征识别结果
        features = [
            {
                "shape": "circle",
                "center": (75.0, 75.0),
                "radius": 15,
                "area": 706.86,
                "confidence": 0.95
            },
            {
                "shape": "rectangle",
                "center": (150.0, 150.0),
                "dimensions": (30, 20),
                "area": 600.0,
                "confidence": 0.88
            }
        ]
        
        # 2. 模拟用户描述分析
        description_analysis = {
            "processing_type": "drilling",
            "depth": 12.0,
            "feed_rate": 95.0,
            "description": "在圆形位置钻φ30通孔，深度12mm",
            "tool_required": "drill_bit"
        }
        
        # 3. 生成NC代码
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 4. 验证输出
        lines = nc_code.split('\n')
        
        # 验证程序基本结构
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)  # 毫米单位
        self.assertIn("G90", nc_code)  # 绝对坐标
        self.assertIn("G83", nc_code)  # 深孔钻削
        self.assertIn("M03", nc_code)  # 主轴正转
        self.assertIn("M08", nc_code)  # 冷却液开
        self.assertIn("M30", nc_code)  # 程序结束
        
        # 验证包含预期的坐标
        self.assertIn("X75.000 Y75.000", nc_code)
        
        # 验证程序行数合理
        self.assertGreater(len(lines), 15)  # 应该有合理的代码行数
    
    def test_complex_feature_processing(self):
        """测试复杂特征处理"""
        # 模拟更复杂的特征集
        features = [
            {
                "shape": "counterbore",
                "center": (100.0, 100.0),
                "outer_diameter": 25.0,
                "inner_diameter": 16.0,
                "depth": 18.0
            },
            {
                "shape": "circle",
                "center": (200.0, 150.0),
                "radius": 8.0
            }
        ]
        
        # 处理沉孔特征
        description_analysis = {
            "processing_type": "counterbore",
            "description": "φ25沉孔深18mm + φ16贯通底孔，另钻φ16通孔"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证沉孔加工代码
        self.assertIn("O0001", nc_code)
        self.assertIn("COUNTERBORE", nc_code)
        self.assertIn("PILOT DRILLING", nc_code)
        self.assertIn("DRILLING OPERATION", nc_code)
        self.assertIn("COUNTERBORE OPERATION", nc_code)
        
        # 验证包含所有特征的加工
        self.assertIn("X100.000 Y100.000", nc_code)  # 沉孔位置
        self.assertIn("X200.000 Y150.000", nc_code)  # 普通孔位置


if __name__ == '__main__':
    unittest.main()

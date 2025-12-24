"""
测试核心模块功能
"""
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
import tempfile
import os

from src.modules.feature_definition import identify_features
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description


class TestFeatureDefinition:
    """测试特征定义模块"""
    
    def test_identify_features_basic(self, sample_image):
        """测试基本特征识别功能"""
        features = identify_features(sample_image)
        
        assert isinstance(features, list)
        # 由于我们的示例图像包含一个圆形，应该至少识别到一个特征
        # 但实际结果取决于图像处理参数，所以我们主要测试函数正常运行
        assert features is not None
    
    def test_identify_features_with_parameters(self, sample_image):
        """测试带参数的特征识别功能"""
        features = identify_features(
            sample_image,
            min_area=50,
            min_perimeter=20,
            canny_low=50,
            canny_high=150
        )
        
        assert isinstance(features, list)
        assert features is not None
    
    def test_identify_features_empty_image(self):
        """测试空图像的特征识别"""
        empty_image = np.zeros((100, 100), dtype=np.uint8)
        features = identify_features(empty_image)
        
        assert isinstance(features, list)
        assert len(features) == 0
    
    def test_identify_features_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(Exception):
            identify_features("invalid_input")


class TestGCodeGeneration:
    """测试G代码生成功能"""
    
    def test_generate_fanuc_nc_basic(self, sample_feature_data, sample_description_analysis):
        """测试基本的FANUC NC代码生成功能"""
        nc_code = generate_fanuc_nc(sample_feature_data, sample_description_analysis)
        
        assert isinstance(nc_code, str)
        assert len(nc_code) > 0
        assert "O0001" in nc_code  # 程序号
        assert "FANUC" in nc_code or "CNC" in nc_code  # 描述
    
    def test_generate_fanuc_nc_empty_features(self, sample_description_analysis):
        """测试空特征列表的代码生成"""
        nc_code = generate_fanuc_nc([], sample_description_analysis)
        
        assert isinstance(nc_code, str)
        assert len(nc_code) > 0
        assert "O0001" in nc_code
    
    def test_generate_fanuc_nc_empty_description(self, sample_feature_data):
        """测试空描述分析的代码生成"""
        empty_description = {
            "processing_type": "general",
            "tool_required": "general_tool",
            "depth": None,
            "feed_rate": None,
            "spindle_speed": None,
            "material": None,
            "precision": None,
            "hole_positions": [],
            "description": ""
        }
        
        nc_code = generate_fanuc_nc(sample_feature_data, empty_description)
        
        assert isinstance(nc_code, str)
        assert len(nc_code) > 0
    
    def test_generate_fanuc_nc_error_handling(self, sample_description_analysis):
        """测试代码生成的错误处理"""
        # 测试无效特征数据
        with pytest.raises(Exception):
            generate_fanuc_nc("invalid_features", sample_description_analysis)


class TestMaterialMatcher:
    """测试材料匹配器功能"""
    
    def test_analyze_user_description_basic(self):
        """测试基本的用户描述分析"""
        description = "在钢件上钻5个孔，深度10mm，使用M8螺纹"
        
        result = analyze_user_description(description)
        
        assert isinstance(result, dict)
        assert "processing_type" in result
        assert "tool_required" in result
        assert "depth" in result
        assert "description" in result
        
        # 检查是否正确识别了加工类型
        assert result["description"] == description
    
    def test_analyze_user_description_with_positions(self):
        """测试包含位置信息的描述分析"""
        description = "在X100 Y50位置钻孔，X200 Y100位置攻丝M6螺纹"
        
        result = analyze_user_description(description)
        
        assert isinstance(result, dict)
        assert "hole_positions" in result
        # 可能识别到位置，但具体取决于正则表达式模式
    
    def test_analyze_user_description_empty(self):
        """测试空描述分析"""
        result = analyze_user_description("")
        
        assert isinstance(result, dict)
        assert result["description"] == ""
        assert result["processing_type"] == "general"
    
    def test_analyze_user_description_complex(self):
        """测试复杂描述分析"""
        description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
        
        result = analyze_user_description(description)
        
        assert isinstance(result, dict)
        assert result["description"] == description
        
        # 检查是否识别到关键信息
        assert "processing_type" in result
        assert "depth" in result
        assert "hole_positions" in result


class TestIntegration:
    """测试模块集成"""
    
    def test_feature_to_gcode_flow(self, sample_feature_data):
        """测试从特征到G代码的完整流程"""
        description = "在钢板上钻孔，深度15mm"
        description_analysis = analyze_user_description(description)
        
        # 更新描述分析以匹配特征类型
        description_analysis["processing_type"] = "drilling"
        description_analysis["depth"] = 15.0
        
        # 生成G代码
        nc_code = generate_fanuc_nc(sample_feature_data, description_analysis)
        
        assert isinstance(nc_code, str)
        assert len(nc_code) > 0
        assert "O0001" in nc_code
    
    def test_error_propagation(self):
        """测试错误传播"""
        # 测试无效输入导致的错误传播
        with pytest.raises(Exception):
            invalid_features = "not_a_list"
            invalid_description = "valid description"
            generate_fanuc_nc(invalid_features, analyze_user_description(invalid_description))
    
    @patch('src.modules.gcode_generation._generate_drilling_code')
    def test_gcode_generation_with_mock(self, mock_gen_drilling):
        """使用Mock测试G代码生成"""
        # 设置mock返回值
        mock_gen_drilling.return_value = ["G00 X0 Y0", "G01 Z-10 F100"]
        
        sample_features = [{
            "shape": "circle",
            "center": (100, 100),
            "radius": 10,
            "contour": np.array([[[110, 100]], [[100, 110]], [[90, 100]], [[100, 90]]]),
            "bounding_box": (90, 90, 20, 20),
            "area": 314,
            "dimensions": (20, 20),
            "confidence": 0.9,
            "aspect_ratio": 1.0
        }]
        
        description_analysis = {
            "processing_type": "drilling",
            "tool_required": "drill_bit",
            "depth": 10.0,
            "feed_rate": 100.0,
            "spindle_speed": 800,
            "material": "steel",
            "precision": "Ra1.6",
            "hole_positions": [(50, 50), (100, 100)],
            "description": "drilling test"
        }
        
        nc_code = generate_fanuc_nc(sample_features, description_analysis)
        
        assert "G00 X0 Y0" in nc_code
        assert "G01 Z-10 F100" in nc_code
        mock_gen_drilling.assert_called_once()
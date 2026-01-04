import pytest
import sys
from pathlib import Path
import json
import os

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config import ConfigManager, config_manager, IMAGE_PROCESSING_CONFIG, FEATURE_RECOGNITION_CONFIG, GCODE_GENERATION_CONFIG, THREAD_PITCH_MAP, TOOL_MAPPING, COORDINATE_CONFIG, OCR_CONFIG, VALIDATION_CONFIG

class TestConfigManager:
    """测试配置管理器类"""
    
    def test_config_manager_initialization(self):
        """测试配置管理器初始化"""
        config = ConfigManager()
        
        # 验证配置对象是否正确初始化
        assert isinstance(config.IMAGE_PROCESSING_CONFIG, dict)
        assert isinstance(config.FEATURE_RECOGNITION_CONFIG, dict)
        assert isinstance(config.GCODE_GENERATION_CONFIG, dict)
        assert isinstance(config.THREAD_PITCH_MAP, dict)
        assert isinstance(config.TOOL_MAPPING, dict)
        
    def test_image_processing_config_defaults(self):
        """测试图像处理配置默认值"""
        config = config_manager
        
        img_config = config.IMAGE_PROCESSING_CONFIG
        assert img_config['default_min_area'] == 100
        assert img_config['default_min_perimeter'] == 10
        assert img_config['default_canny_low'] == 50
        assert img_config['default_canny_high'] == 150
        assert img_config['default_gaussian_kernel'] == (5, 5)
        assert img_config['default_morph_kernel'] == (2, 2)
        assert img_config['min_confidence_threshold'] == 0.7
        assert img_config['duplicate_distance_threshold'] == 3.0
        assert img_config['iou_threshold'] == 0.3
        
    def test_feature_recognition_config_defaults(self):
        """测试特征识别配置默认值"""
        config = config_manager
        
        feat_config = config.FEATURE_RECOGNITION_CONFIG
        assert feat_config['circularity_threshold'] == 0.8
        assert feat_config['solidity_threshold'] == 0.7
        assert feat_config['extent_threshold'] == 0.8
        assert feat_config['aspect_ratio_tolerance'] == 0.2
        assert feat_config['ellipse_eccentricity_min'] == 0.4
        assert feat_config['ellipse_eccentricity_max'] == 0.9
        assert feat_config['corner_radius_threshold'] == 2.0
        assert feat_config['pocket_solidity_threshold'] == 0.85
        
    def test_gcode_generation_config_defaults(self):
        """测试G代码生成配置默认值"""
        config = config_manager
        
        gcode_config = config.GCODE_GENERATION_CONFIG
        assert gcode_config['drilling']['default_depth'] == 10.0
        assert gcode_config['drilling']['default_feed_rate'] == 100.0
        assert gcode_config['drilling']['default_spindle_speed'] == 800
        assert gcode_config['drilling']['drilling_depth_factor'] == 1.5
        
        assert gcode_config['tapping']['default_thread_pitch'] == 1.5
        assert gcode_config['tapping']['tapping_feed_rate_factor'] == 1.2
        assert gcode_config['tapping']['tapping_spindle_speed'] == 300
        
        assert gcode_config['counterbore']['default_outer_diameter'] == 22.0
        assert gcode_config['counterbore']['default_inner_diameter'] == 14.5
        assert gcode_config['counterbore']['default_depth'] == 20.0
        assert gcode_config['counterbore']['radius_ratio_min'] == 1.2
        assert gcode_config['counterbore']['radius_ratio_max'] == 3.0
        
        assert gcode_config['milling']['default_feed_rate'] == 200.0
        assert gcode_config['milling']['default_spindle_speed'] == 1200
        
        assert gcode_config['safety']['safe_height'] == 100.0
        assert gcode_config['safety']['approach_height'] == 2.0
        assert gcode_config['safety']['dwell_time'] == 1000
        assert gcode_config['safety']['delay_time'] == 1000
        
    def test_thread_pitch_map_defaults(self):
        """测试螺纹参数映射默认值"""
        config = config_manager
        
        thread_map = config.THREAD_PITCH_MAP
        assert thread_map["M3"] == 0.5
        assert thread_map["M4"] == 0.7
        assert thread_map["M5"] == 0.8
        assert thread_map["M6"] == 1.0
        assert thread_map["M8"] == 1.25
        assert thread_map["M10"] == 1.5
        assert thread_map["M12"] == 1.75
        
    def test_tool_mapping_defaults(self):
        """测试刀具映射默认值"""
        config = config_manager
        
        tool_map = config.TOOL_MAPPING
        assert tool_map["center_drill"] == 1
        assert tool_map["drill_bit"] == 2
        assert tool_map["tap"] == 3
        assert tool_map["counterbore_tool"] == 4
        assert tool_map["end_mill"] == 5
        assert tool_map["cutting_tool"] == 6
        assert tool_map["grinding_wheel"] == 7
        assert tool_map["general_tool"] == 8
        assert tool_map["thread_mill"] == 9
        
    def test_coordinate_config_defaults(self):
        """测试坐标系统配置默认值"""
        config = config_manager
        
        coord_config = config.COORDINATE_CONFIG
        assert coord_config['default_coordinate_strategy'] == 'highest_y'
        assert coord_config['polar_coordinate_tolerance'] == 0.15
        assert coord_config['position_match_tolerance'] == 0.1
        assert coord_config['pocket_tolerance'] == 0.2
        
    def test_ocr_config_defaults(self):
        """测试OCR配置默认值"""
        config = config_manager
        
        ocr_config = config.OCR_CONFIG
        assert ocr_config['default_hole_count'] == 3
        assert ocr_config['text_extraction_timeout'] == 30
        assert ocr_config['confidence_threshold'] == 0.8
        
    def test_validation_config_defaults(self):
        """测试验证配置默认值"""
        config = config_manager
        
        validation_config = config.VALIDATION_CONFIG
        assert validation_config['max_file_size_mb'] == 50
        assert '.pdf' in validation_config['allowed_file_types']
        assert '.jpg' in validation_config['allowed_file_types']
        assert validation_config['max_dimension_pixels'] == 10000
        
    def test_config_getter_method(self):
        """测试配置获取方法"""
        config = ConfigManager()
        
        # 验证可以获取已存在的配置
        img_config = config.get_config('IMAGE_PROCESSING_CONFIG')
        assert img_config is not None
        assert isinstance(img_config, dict)
        
        # 验证获取不存在的配置返回None
        nonexistent_config = config.get_config('NONEXISTENT_CONFIG')
        assert nonexistent_config is None
        
    def test_config_update_method(self):
        """测试配置更新方法"""
        config = ConfigManager()
        
        # 测试更新现有配置
        original_value = config.IMAGE_PROCESSING_CONFIG['default_min_area']
        new_values = {'default_min_area': original_value + 100}
        
        result = config.update_config('IMAGE_PROCESSING_CONFIG', new_values)
        assert result is True
        assert config.IMAGE_PROCESSING_CONFIG['default_min_area'] == original_value + 100
        
        # 恢复原始值
        config.update_config('IMAGE_PROCESSING_CONFIG', {'default_min_area': original_value})
        
    def test_config_validation_method(self):
        """测试配置验证方法"""
        config = ConfigManager()
        
        # 验证现有配置
        result = config.validate_config('IMAGE_PROCESSING_CONFIG')
        assert result is True
        
        result = config.validate_config('GCODE_GENERATION_CONFIG')
        assert result is True
        
        result = config.validate_config('VALIDATION_CONFIG')
        assert result is True
        
        # 验证不存在的配置
        result = config.validate_config('NONEXISTENT_CONFIG')
        assert result is False


class TestGlobalConfigVariables:
    """测试全局配置变量"""
    
    def test_global_config_variables_exist(self):
        """测试全局配置变量是否存在"""
        assert IMAGE_PROCESSING_CONFIG is not None
        assert FEATURE_RECOGNITION_CONFIG is not None
        assert GCODE_GENERATION_CONFIG is not None
        assert THREAD_PITCH_MAP is not None
        assert TOOL_MAPPING is not None
        assert COORDINATE_CONFIG is not None
        assert OCR_CONFIG is not None
        assert VALIDATION_CONFIG is not None
        
    def test_global_config_variables_type(self):
        """测试全局配置变量类型正确"""
        assert isinstance(IMAGE_PROCESSING_CONFIG, dict)
        assert isinstance(FEATURE_RECOGNITION_CONFIG, dict)
        assert isinstance(GCODE_GENERATION_CONFIG, dict)
        assert isinstance(THREAD_PITCH_MAP, dict)
        assert isinstance(TOOL_MAPPING, dict)
        assert isinstance(COORDINATE_CONFIG, dict)
        assert isinstance(OCR_CONFIG, dict)
        assert isinstance(VALIDATION_CONFIG, dict)
        
    def test_global_config_variables_match_manager(self):
        """测试全局配置变量与管理器中的配置一致"""
        assert IMAGE_PROCESSING_CONFIG == config_manager.IMAGE_PROCESSING_CONFIG
        assert FEATURE_RECOGNITION_CONFIG == config_manager.FEATURE_RECOGNITION_CONFIG
        assert GCODE_GENERATION_CONFIG == config_manager.GCODE_GENERATION_CONFIG
        assert THREAD_PITCH_MAP == config_manager.THREAD_PITCH_MAP
        assert TOOL_MAPPING == config_manager.TOOL_MAPPING
        assert COORDINATE_CONFIG == config_manager.COORDINATE_CONFIG
        assert OCR_CONFIG == config_manager.OCR_CONFIG
        assert VALIDATION_CONFIG == config_manager.VALIDATION_CONFIG
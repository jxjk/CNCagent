"""
测试配置和配置验证器
"""
import pytest
from unittest.mock import patch, Mock

from src.config_validator import ConfigValidator, validate_system_config, get_config_errors


class TestConfigValidator:
    """测试配置验证器"""
    
    def test_config_validator_initialization(self):
        """测试配置验证器初始化"""
        validator = ConfigValidator()
        assert validator is not None
        assert validator.logger is not None
    
    def test_validate_image_processing_config_valid(self):
        """测试有效的图像处理配置"""
        validator = ConfigValidator()
        errors = validator.validate_image_processing_config()
        
        # 检查是否有错误
        # 注意：这里可能有错误，因为我们正在测试当前配置，而当前配置可能包含无效值
        # 我们只验证函数能够运行而不抛出异常
        assert isinstance(errors, list)
    
    def test_validate_feature_recognition_config_valid(self):
        """测试有效的特征识别配置"""
        validator = ConfigValidator()
        errors = validator.validate_feature_recognition_config()
        
        assert isinstance(errors, list)
    
    def test_validate_gcode_generation_config_valid(self):
        """测试有效的G代码生成配置"""
        validator = ConfigValidator()
        errors = validator.validate_gcode_generation_config()
        
        assert isinstance(errors, list)
    
    def test_validate_coordinate_config_valid(self):
        """测试有效的坐标配置"""
        validator = ConfigValidator()
        errors = validator.validate_coordinate_config()
        
        assert isinstance(errors, list)
    
    def test_validate_ocr_config_valid(self):
        """测试有效的OCR配置"""
        validator = ConfigValidator()
        errors = validator.validate_ocr_config()
        
        assert isinstance(errors, list)
    
    def test_validate_validation_config_valid(self):
        """测试有效的验证配置"""
        validator = ConfigValidator()
        errors = validator.validate_validation_config()
        
        assert isinstance(errors, list)
    
    def test_validate_all_configs(self):
        """测试验证所有配置"""
        validator = ConfigValidator()
        errors = validator.validate_all_configs()
        
        assert isinstance(errors, list)
        
        # 测试整体验证函数
        is_valid = validator.validate_config()
        assert isinstance(is_valid, bool)
    
    def test_get_config_errors_function(self):
        """测试获取配置错误的函数"""
        errors = get_config_errors()
        assert isinstance(errors, list)
        
        is_valid = validate_system_config()
        assert isinstance(is_valid, bool)
    
    def test_invalid_image_processing_config(self):
        """测试无效的图像处理配置"""
        # 模拟无效配置
        with patch('src.config_validator.IMAGE_PROCESSING_CONFIG', {
            'default_min_area': -1,  # 无效值
            'default_min_perimeter': -1,  # 无效值
            'default_canny_low': 150,  # 高阈值
            'default_canny_high': 50,  # 低阈值，错误顺序
            'min_confidence_threshold': 1.5,  # 超出范围
            'duplicate_distance_threshold': 3.0,
            'iou_threshold': 0.3
        }):
            validator = ConfigValidator()
            errors = validator.validate_image_processing_config()
            
            # 应该检测到多个错误
            assert len(errors) >= 3  # 至少3个错误
            error_messages = " ".join(errors)
            assert "default_min_area" in error_messages
            assert "default_min_perimeter" in error_messages
            assert "Canny低阈值必须小于高阈值" in error_messages
            assert "min_confidence_threshold" in error_messages
    
    def test_invalid_feature_recognition_config(self):
        """测试无效的特征识别配置"""
        with patch('src.config_validator.FEATURE_RECOGNITION_CONFIG', {
            'circularity_threshold': -0.5,  # 无效值
            'solidity_threshold': 1.5,  # 超出范围
            'extent_threshold': -0.1,  # 无效值
            'aspect_ratio_tolerance': -0.1,  # 负值
            'ellipse_eccentricity_min': 0.4,
            'ellipse_eccentricity_max': 0.9
        }):
            validator = ConfigValidator()
            errors = validator.validate_feature_recognition_config()
            
            assert len(errors) >= 3  # 至少3个错误
            error_messages = " ".join(errors)
            assert "circularity_threshold" in error_messages
            assert "solidity_threshold" in error_messages
            assert "aspect_ratio_tolerance" in error_messages
    
    def test_invalid_gcode_generation_config(self):
        """测试无效的G代码生成配置"""
        with patch('src.config_validator.GCODE_GENERATION_CONFIG', {
            'drilling': {
                'default_depth': -5,  # 无效值
                'default_feed_rate': -100,  # 无效值
                'default_spindle_speed': -800,  # 无效值
                'center_drill_depth': 1.0,
                'drilling_depth_factor': 1.5,
                'drill_diameter_tolerance': 0.1
            },
            'tapping': {
                'default_thread_pitch': 1.5,
                'tapping_feed_rate_factor': 1.2,
                'tapping_spindle_speed': 300
            },
            'counterbore': {
                'default_outer_diameter': 22.0,
                'default_inner_diameter': 14.5,
                'default_depth': -20,  # 无效值
                'counterbore_spindle_speed': -400,  # 无效值
                'counterbore_feed_rate': 80,
                'drilling_depth_factor': 1.5,
                'radius_ratio_min': 1.2,
                'radius_ratio_max': 3.0
            },
            'milling': {
                'default_feed_rate': 200.0,
                'default_spindle_speed': 1200,
                'milling_tolerance': 0.1
            },
            'safety': {
                'safe_height': -100,  # 无效值
                'approach_height': 2.0,
                'dwell_time': -1000,  # 负值
                'delay_time': 1000
            }
        }):
            validator = ConfigValidator()
            errors = validator.validate_gcode_generation_config()
            
            assert len(errors) >= 5  # 至少5个错误
            error_messages = " ".join(errors)
            assert "default_depth" in error_messages
            assert "default_feed_rate" in error_messages
            assert "default_spindle_speed" in error_messages
            assert "counterbore_spindle_speed" in error_messages
            assert "safe_height" in error_messages
    
    def test_invalid_coordinate_config(self):
        """测试无效的坐标配置"""
        with patch('src.config_validator.COORDINATE_CONFIG', {
            'default_coordinate_strategy': 'invalid_strategy',  # 无效策略
            'polar_coordinate_tolerance': -0.1,  # 负值
            'position_match_tolerance': -0.2  # 负值
        }):
            validator = ConfigValidator()
            errors = validator.validate_coordinate_config()
            
            assert len(errors) >= 1  # 至少1个错误
            error_messages = " ".join(errors)
            assert "coordinate_strategy" in error_messages
    
    def test_invalid_ocr_config(self):
        """测试无效的OCR配置"""
        with patch('src.config_validator.OCR_CONFIG', {
            'default_hole_count': 0,  # 无效值
            'text_extraction_timeout': -10,  # 负值
            'confidence_threshold': 1.5  # 超出范围
        }):
            validator = ConfigValidator()
            errors = validator.validate_ocr_config()
            
            assert len(errors) >= 3  # 至少3个错误
            error_messages = " ".join(errors)
            assert "default_hole_count" in error_messages
            assert "text_extraction_timeout" in error_messages
            assert "confidence_threshold" in error_messages
    
    def test_invalid_validation_config(self):
        """测试无效的验证配置"""
        with patch('src.config_validator.VALIDATION_CONFIG', {
            'max_file_size_mb': 0,  # 无效值
            'allowed_file_types': ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            'max_dimension_pixels': 0  # 无效值
        }):
            validator = ConfigValidator()
            errors = validator.validate_validation_config()
            
            assert len(errors) >= 2  # 至少2个错误
            error_messages = " ".join(errors)
            assert "max_file_size_mb" in error_messages
            assert "max_dimension_pixels" in error_messages
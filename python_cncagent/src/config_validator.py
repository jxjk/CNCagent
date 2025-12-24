"""
配置验证器
验证系统配置参数的有效性
"""
import logging
from typing import Dict, Any, List
from .config import (
    IMAGE_PROCESSING_CONFIG,
    FEATURE_RECOGNITION_CONFIG,
    GCODE_GENERATION_CONFIG,
    COORDINATE_CONFIG,
    OCR_CONFIG,
    VALIDATION_CONFIG
)
from src.exceptions import ConfigurationError


class ConfigValidator:
    """
    配置验证器
    验证所有配置参数是否在合理范围内
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_all_configs(self) -> List[str]:
        """
        验证所有配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        errors.extend(self.validate_image_processing_config())
        errors.extend(self.validate_feature_recognition_config())
        errors.extend(self.validate_gcode_generation_config())
        errors.extend(self.validate_coordinate_config())
        errors.extend(self.validate_ocr_config())
        errors.extend(self.validate_validation_config())
        
        return errors
    
    def validate_image_processing_config(self) -> List[str]:
        """验证图像处理配置"""
        errors = []
        config = IMAGE_PROCESSING_CONFIG
        
        if config['default_min_area'] <= 0:
            errors.append("default_min_area 必须大于0")
        
        if config['default_min_perimeter'] <= 0:
            errors.append("default_min_perimeter 必须大于0")
        
        if config['default_canny_low'] < 0 or config['default_canny_high'] < 0:
            errors.append("Canny阈值必须非负")
        
        if config['default_canny_low'] >= config['default_canny_high']:
            errors.append("Canny低阈值必须小于高阈值")
        
        if config['min_confidence_threshold'] < 0 or config['min_confidence_threshold'] > 1:
            errors.append("min_confidence_threshold 必须在0-1之间")
        
        return errors
    
    def validate_feature_recognition_config(self) -> List[str]:
        """验证特征识别配置"""
        errors = []
        config = FEATURE_RECOGNITION_CONFIG
        
        if config['circularity_threshold'] < 0 or config['circularity_threshold'] > 1:
            errors.append("circularity_threshold 必须在0-1之间")
        
        if config['solidity_threshold'] < 0 or config['solidity_threshold'] > 1:
            errors.append("solidity_threshold 必须在0-1之间")
        
        if config['extent_threshold'] < 0 or config['extent_threshold'] > 1:
            errors.append("extent_threshold 必须在0-1之间")
        
        if config['aspect_ratio_tolerance'] < 0:
            errors.append("aspect_ratio_tolerance 必须非负")
        
        return errors
    
    def validate_gcode_generation_config(self) -> List[str]:
        """验证G代码生成配置"""
        errors = []
        config = GCODE_GENERATION_CONFIG
        
        drilling_config = config['drilling']
        if drilling_config['default_depth'] <= 0:
            errors.append("drilling.default_depth 必须大于0")
        
        if drilling_config['default_feed_rate'] <= 0:
            errors.append("drilling.default_feed_rate 必须大于0")
        
        if drilling_config['default_spindle_speed'] <= 0:
            errors.append("drilling.default_spindle_speed 必须大于0")
        
        counterbore_config = config['counterbore']
        if counterbore_config['default_depth'] <= 0:
            errors.append("counterbore.default_depth 必须大于0")
        
        if counterbore_config['counterbore_spindle_speed'] <= 0:
            errors.append("counterbore.counterbore_spindle_speed 必须大于0")
        
        safety_config = config['safety']
        if safety_config['safe_height'] <= 0:
            errors.append("safety.safe_height 必须大于0")
        
        if safety_config['dwell_time'] < 0:
            errors.append("safety.dwell_time 不能为负")
        
        if safety_config['delay_time'] < 0:
            errors.append("safety.delay_time 不能为负")
        
        return errors
    
    def validate_coordinate_config(self) -> List[str]:
        """验证坐标系统配置"""
        errors = []
        config = COORDINATE_CONFIG
        
        valid_strategies = ['highest_y', 'lowest_y', 'leftmost_x', 'rightmost_x', 'center', 'geometric_center', 'custom']
        if config['default_coordinate_strategy'] not in valid_strategies:
            errors.append(f"coordinate_strategy 必须是 {valid_strategies} 之一")
        
        if config['polar_coordinate_tolerance'] < 0:
            errors.append("polar_coordinate_tolerance 必须非负")
        
        if config['position_match_tolerance'] < 0:
            errors.append("position_match_tolerance 必须非负")
        
        return errors
    
    def validate_ocr_config(self) -> List[str]:
        """验证OCR配置"""
        errors = []
        config = OCR_CONFIG
        
        if config['default_hole_count'] <= 0:
            errors.append("default_hole_count 必须大于0")
        
        if config['text_extraction_timeout'] <= 0:
            errors.append("text_extraction_timeout 必须大于0")
        
        if config['confidence_threshold'] < 0 or config['confidence_threshold'] > 1:
            errors.append("confidence_threshold 必须在0-1之间")
        
        return errors
    
    def validate_validation_config(self) -> List[str]:
        """验证验证配置"""
        errors = []
        config = VALIDATION_CONFIG
        
        if config['max_file_size_mb'] <= 0:
            errors.append("max_file_size_mb 必须大于0")
        
        if config['max_dimension_pixels'] <= 0:
            errors.append("max_dimension_pixels 必须大于0")
        
        return errors
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        errors = self.validate_all_configs()
        
        if errors:
            for error in errors:
                self.logger.error(f"配置错误: {error}")
            return False
        
        self.logger.info("配置验证通过")
        return True


# 全局验证器实例
config_validator = ConfigValidator()


def validate_system_config() -> bool:
    """
    验证系统配置
    
    Returns:
        bool: 配置是否有效
    """
    return config_validator.validate_config()


def get_config_errors() -> List[str]:
    """
    获取配置错误列表
    
    Returns:
        List[str]: 配置错误列表
    """
    return config_validator.validate_all_configs()
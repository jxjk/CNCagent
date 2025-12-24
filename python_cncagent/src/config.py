"""
CNC Agent配置模块
包含所有常量配置，替换原有的魔法数字
"""
from typing import Dict, Tuple, Any
import logging

class ConfigManager:
    """统一的配置管理器"""
    
    def __init__(self):
        # 图像处理参数
        self.IMAGE_PROCESSING_CONFIG = {
            'default_min_area': 100,
            'default_min_perimeter': 10,
            'default_canny_low': 50,
            'default_canny_high': 150,
            'default_gaussian_kernel': (5, 5),
            'default_morph_kernel': (2, 2),
            'min_confidence_threshold': 0.7,
            'duplicate_distance_threshold': 3.0,
            'iou_threshold': 0.3
        }

        # 特征识别参数
        self.FEATURE_RECOGNITION_CONFIG = {
            'circularity_threshold': 0.8,
            'solidity_threshold': 0.7,
            'extent_threshold': 0.8,
            'aspect_ratio_tolerance': 0.2,
            'ellipse_eccentricity_min': 0.4,
            'ellipse_eccentricity_max': 0.9
        }

        # G代码生成参数
        self.GCODE_GENERATION_CONFIG = {
            # 钻孔参数
            'drilling': {
                'default_depth': 10.0,
                'default_feed_rate': 100.0,
                'default_spindle_speed': 800,
                'center_drill_depth': 1.0,
                'drilling_depth_factor': 1.5,  # 钻孔深度 = 要求深度 + 直径/3 + factor
                'drill_diameter_tolerance': 0.1
            },
            
            # 攻丝参数
            'tapping': {
                'default_thread_pitch': 1.5,
                'tapping_feed_rate_factor': 1.2,  # 进给速度 = 螺距 * 转速 * factor
                'tapping_spindle_speed': 300
            },
            
            # 沉孔参数
            'counterbore': {
                'default_outer_diameter': 22.0,
                'default_inner_diameter': 14.5,
                'default_depth': 20.0,
                'counterbore_spindle_speed': 400,
                'counterbore_feed_rate': 80,
                'drilling_depth_factor': 1.5,  # 钻孔深度计算
                'radius_ratio_min': 1.2,
                'radius_ratio_max': 3.0
            },
            
            # 铣削参数
            'milling': {
                'default_feed_rate': 200.0,
                'default_spindle_speed': 1200,
                'milling_tolerance': 0.1
            },
            
            # 安全参数
            'safety': {
                'safe_height': 100.0,
                'approach_height': 2.0,
                'dwell_time': 1000,  # 毫秒
                'delay_time': 1000   # 毫秒
            }
        }

        # 螺纹参数映射
        self.THREAD_PITCH_MAP: Dict[str, float] = {
            "M3": 0.5,
            "M4": 0.7,
            "M5": 0.8,
            "M6": 1.0,
            "M8": 1.25,
            "M10": 1.5,
            "M12": 1.75
        }

        # 刀具映射
        self.TOOL_MAPPING: Dict[str, int] = {
            "center_drill": 1,
            "drill_bit": 2,
            "tap": 3,
            "counterbore_tool": 4,
            "end_mill": 5,
            "cutting_tool": 6,
            "grinding_wheel": 7,
            "general_tool": 8,
            "thread_mill": 9
        }

        # 坐标系统参数
        self.COORDINATE_CONFIG = {
            'default_coordinate_strategy': 'highest_y',
            'polar_coordinate_tolerance': 0.15,  # PCD半径的容差比例
            'position_match_tolerance': 0.1      # 位置匹配容差
        }

        # OCR和文本处理参数
        self.OCR_CONFIG = {
            'default_hole_count': 3,
            'text_extraction_timeout': 30,  # 秒
            'confidence_threshold': 0.8
        }

        # 验证参数
        self.VALIDATION_CONFIG = {
            'max_file_size_mb': 50,  # 最大文件大小MB
            'allowed_file_types': ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
            'max_dimension_pixels': 10000  # 最大图像尺寸像素
        }
    
    def get_config(self, config_name: str) -> Any:
        """获取指定配置"""
        return getattr(self, config_name, None)
    
    def update_config(self, config_name: str, new_values: Dict[str, Any]) -> bool:
        """更新指定配置"""
        try:
            config = getattr(self, config_name, None)
            if config is None:
                logging.warning(f"配置 {config_name} 不存在")
                return False
            
            if isinstance(config, dict):
                config.update(new_values)
                return True
            else:
                setattr(self, config_name, new_values)
                return True
        except Exception as e:
            logging.error(f"更新配置 {config_name} 失败: {str(e)}")
            return False
    
    def validate_config(self, config_name: str) -> bool:
        """验证配置的有效性"""
        config = getattr(self, config_name, None)
        if config is None:
            return False
        
        # 对于特定配置，添加验证逻辑
        if config_name == 'IMAGE_PROCESSING_CONFIG':
            return self._validate_image_processing_config(config)
        elif config_name == 'GCODE_GENERATION_CONFIG':
            return self._validate_gcode_generation_config(config)
        elif config_name == 'VALIDATION_CONFIG':
            return self._validate_validation_config(config)
        
        return True
    
    def _validate_image_processing_config(self, config: Dict) -> bool:
        """验证图像处理配置"""
        required_keys = ['default_min_area', 'default_min_perimeter', 'min_confidence_threshold']
        for key in required_keys:
            if key not in config:
                return False
            if not isinstance(config[key], (int, float)) or config[key] < 0:
                return False
        return True
    
    def _validate_gcode_generation_config(self, config: Dict) -> bool:
        """验证G代码生成配置"""
        required_sections = ['drilling', 'safety']
        for section in required_sections:
            if section not in config:
                return False
        
        drilling = config['drilling']
        required_drilling_keys = ['default_depth', 'default_feed_rate', 'default_spindle_speed']
        for key in required_drilling_keys:
            if key not in drilling:
                return False
            if not isinstance(drilling[key], (int, float)) or drilling[key] < 0:
                return False
        
        safety = config['safety']
        required_safety_keys = ['safe_height', 'dwell_time', 'delay_time']
        for key in required_safety_keys:
            if key not in safety:
                return False
            if not isinstance(safety[key], (int, float)) or safety[key] < 0:
                return False
        
        return True
    
    def _validate_validation_config(self, config: Dict) -> bool:
        """验证验证配置"""
        required_keys = ['max_file_size_mb', 'allowed_file_types', 'max_dimension_pixels']
        for key in required_keys:
            if key not in config:
                return False
            if key == 'allowed_file_types':
                if not isinstance(config[key], list):
                    return False
            else:
                if not isinstance(config[key], (int, float)) or config[key] < 0:
                    return False
        return True

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 为了向后兼容，保留原有的配置变量
IMAGE_PROCESSING_CONFIG = config_manager.IMAGE_PROCESSING_CONFIG
FEATURE_RECOGNITION_CONFIG = config_manager.FEATURE_RECOGNITION_CONFIG
GCODE_GENERATION_CONFIG = config_manager.GCODE_GENERATION_CONFIG
THREAD_PITCH_MAP = config_manager.THREAD_PITCH_MAP
TOOL_MAPPING = config_manager.TOOL_MAPPING
COORDINATE_CONFIG = config_manager.COORDINATE_CONFIG
OCR_CONFIG = config_manager.OCR_CONFIG
VALIDATION_CONFIG = config_manager.VALIDATION_CONFIG
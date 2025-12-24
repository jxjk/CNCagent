"""
CNC Agent配置模块
包含所有常量配置，替换原有的魔法数字
"""
from typing import Dict, Tuple

# 图像处理参数
IMAGE_PROCESSING_CONFIG = {
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
FEATURE_RECOGNITION_CONFIG = {
    'circularity_threshold': 0.8,
    'solidity_threshold': 0.7,
    'extent_threshold': 0.8,
    'aspect_ratio_tolerance': 0.2,
    'ellipse_eccentricity_min': 0.4,
    'ellipse_eccentricity_max': 0.9
}

# G代码生成参数
GCODE_GENERATION_CONFIG = {
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
THREAD_PITCH_MAP: Dict[str, float] = {
    "M3": 0.5,
    "M4": 0.7,
    "M5": 0.8,
    "M6": 1.0,
    "M8": 1.25,
    "M10": 1.5,
    "M12": 1.75
}

# 刀具映射
TOOL_MAPPING: Dict[str, int] = {
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
COORDINATE_CONFIG = {
    'default_coordinate_strategy': 'highest_y',
    'polar_coordinate_tolerance': 0.15,  # PCD半径的容差比例
    'position_match_tolerance': 0.1      # 位置匹配容差
}

# OCR和文本处理参数
OCR_CONFIG = {
    'default_hole_count': 3,
    'text_extraction_timeout': 30,  # 秒
    'confidence_threshold': 0.8
}

# 验证参数
VALIDATION_CONFIG = {
    'max_file_size_mb': 50,  # 最大文件大小MB
    'allowed_file_types': ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
    'max_dimension_pixels': 10000  # 最大图像尺寸像素
}
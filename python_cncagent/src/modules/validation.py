"""
验证模块
用于验证生成的NC代码的正确性
"""
import re
from typing import List, Dict

def validate_features(features: List[Dict]) -> List[str]:
    """
    验证识别出的特征的合理性
    
    Args:
        features: 识别出的特征列表
    
    Returns:
        错误信息列表
    """
    errors = []
    
    for i, feature in enumerate(features):
        # 检查必需字段
        required_fields = ["shape", "contour", "bounding_box", "area"]
        for field in required_fields:
            if field not in feature:
                errors.append(f"特征 {i} 缺少必需字段: {field}")
        
        # 验证数值合理性
        if "area" in feature and feature["area"] <= 0:
            errors.append(f"特征 {i} 的面积不合理: {feature['area']}")
        
        if "bounding_box" in feature:
            x, y, w, h = feature["bounding_box"]
            if w <= 0 or h <= 0:
                errors.append(f"特征 {i} 的边界框尺寸不合理: ({w}, {h})")
    
    return errors

def validate_user_description(description: str) -> List[str]:
    """
    验证用户描述的合理性
    
    Args:
        description: 用户描述文本
    
    Returns:
        错误信息列表
    """
    errors = []
    
    if not description or len(description.strip()) == 0:
        errors.append("用户描述不能为空")
    
    if len(description) > 1000:  # 假设最大长度为1000字符
        errors.append("用户描述过长")
    
    return errors

def validate_parameters(description_analysis: Dict) -> List[str]:
    """
    验证解析出的参数的合理性
    
    Args:
        description_analysis: 用户描述解析结果
    
    Returns:
        错误信息列表
    """
    errors = []
    
    # 检查数值参数的合理性
    depth = description_analysis.get("depth")
    if depth is not None and (depth <= 0 or depth > 1000):  # 假设最大深度为1000mm
        errors.append(f"加工深度不合理: {depth}mm")
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is not None and (feed_rate <= 0 or feed_rate > 10000):  # 假设最大进给速度为10000mm/min
        errors.append(f"进给速度不合理: {feed_rate}mm/min")
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is not None and (spindle_speed <= 0 or spindle_speed > 10000):  # 假设最大转速为10000RPM
        errors.append(f"主轴转速不合理: {spindle_speed}RPM")
    
    return errors

def validate_nc_program(nc_program: str) -> List[str]:
    """
    验证NC程序的基本语法
    
    Args:
        nc_program: NC程序代码
    
    Returns:
        错误信息列表
    """
    errors = []
    lines = nc_program.split('\n')
    
    # 检查程序头
    has_program_number = any(re.match(r'^O\d+', line.strip()) for line in lines)
    if not has_program_number:
        errors.append("缺少程序号 (Oxxxx)")
    
    # 检查单位设置
    has_unit_setting = any('G20' in line or 'G21' in line for line in lines)
    if not has_unit_setting:
        errors.append("缺少单位设置 (G20/G21)")
    
    # 检查坐标系统
    has_coord_setting = any('G90' in line or 'G91' in line for line in lines)
    if not has_coord_setting:
        errors.append("缺少坐标系统设置 (G90/G91)")
    
    # 检查程序结束
    has_program_end = any('M02' in line or 'M30' in line for line in lines)
    if not has_program_end:
        errors.append("缺少程序结束指令 (M02/M30)")
    
    # 检查是否有明显的语法错误
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not re.match(r'^[GTMNFXYZIJRKLPQSEWABCDHUVWM]+', line, re.IGNORECASE):
            # 检查是否是注释或空行
            if not line.startswith(';') and not line.startswith('%'):
                errors.append(f"第 {i+1} 行可能存在语法错误: {line}")
    
    return errors
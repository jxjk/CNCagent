"""
验证模块
用于验证生成的NC代码的正确性
"""
import re
from typing import List, Dict
import os

def validate_features(features: List[Dict]) -> List[str]:
    """
    验证识别出的特征的合理性
    
    Args:
        features: 识别出的特征列表
    
    Returns:
        错误信息列表
    """
    errors = []
    
    if not isinstance(features, list):
        return ["特征列表必须是list类型"]
    
    for i, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"特征 {i} 必须是字典类型")
            continue
        
        # 检查必需字段
        required_fields = ["shape", "contour", "bounding_box", "area"]
        for field in required_fields:
            if field not in feature:
                errors.append(f"特征 {i} 缺少必需字段: {field}")
        
        # 验证数值合理性
        if "area" in feature:
            if not isinstance(feature["area"], (int, float)) or feature["area"] <= 0:
                errors.append(f"特征 {i} 的面积不合理: {feature['area']}")
        
        if "bounding_box" in feature:
            bbox = feature["bounding_box"]
            if isinstance(bbox, (tuple, list)) and len(bbox) >= 4:
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                if not all(isinstance(v, (int, float)) for v in [x, y, w, h]):
                    errors.append(f"特征 {i} 的边界框坐标类型错误")
                elif w <= 0 or h <= 0:
                    errors.append(f"特征 {i} 的边界框尺寸不合理: ({w}, {h})")
            else:
                errors.append(f"特征 {i} 的边界框格式错误: {bbox}")
    
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
    
    if not description:
        errors.append("用户描述不能为空")
        return errors
    
    if not isinstance(description, str):
        errors.append("用户描述必须是字符串类型")
        return errors
    
    # 安全验证：检查是否存在潜在的恶意内容
    dangerous_patterns = [
        r'\b(G[0-9]+.*\bM[0-9]+\b)',  # 避免直接的G代码注入
        r'\b(T[0-9]+\b.*H[0-9]+\b)',  # 避免刀具补偿设置
        r'\b(S[0-9]+\b.*M[0-9]+\b)',  # 避免主轴转速和M代码组合
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            errors.append("用户描述包含可能的恶意G代码模式")
            break
    
    if len(description) > 1000:  # 假设最大长度为1000字符
        errors.append("用户描述过长")
    
    # 检查是否存在潜在的路径遍历或命令注入尝试
    dangerous_keywords = ['../', '..\\', 'exec', 'eval', 'import', 'system', 'shell', 'cmd']
    for keyword in dangerous_keywords:
        if keyword.lower() in description.lower():
            errors.append(f"用户描述包含不安全的关键词: {keyword}")
            break
    
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
    
    if not isinstance(description_analysis, dict):
        return ["描述分析结果必须是字典类型"]
    
    # 检查数值参数的合理性
    depth = description_analysis.get("depth")
    if depth is not None:
        if not isinstance(depth, (int, float)):
            errors.append("深度参数必须是数字类型")
        elif depth <= 0 or depth > 1000:  # 假设最大深度为1000mm
            errors.append(f"加工深度不合理: {depth}mm")
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is not None:
        if not isinstance(feed_rate, (int, float)):
            errors.append("进给速度参数必须是数字类型")
        elif feed_rate <= 0 or feed_rate > 10000:  # 假设最大进给速度为10000mm/min
            errors.append(f"进给速度不合理: {feed_rate}mm/min")
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is not None:
        if not isinstance(spindle_speed, (int, float)):
            errors.append("主轴转速参数必须是数字类型")
        elif spindle_speed <= 0 or spindle_speed > 10000:  # 假设最大转速为10000RPM
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
    
    if not isinstance(nc_program, str):
        return ["NC程序必须是字符串类型"]
    
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
    
    # 检查潜在的安全问题
    dangerous_sequences = [
        'M98',  # 子程序调用
        'G65',  # 宏程序调用
        'G66',  # 宏程序模态调用
        'G67',  # 宏程序调用取消
    ]
    
    for seq in dangerous_sequences:
        if any(seq in line.upper() for line in lines):
            errors.append(f"NC程序包含潜在危险指令: {seq}")
    
    return errors

def validate_file_path(file_path: str) -> List[str]:
    """
    验证文件路径的安全性
    
    Args:
        file_path: 文件路径
    
    Returns:
        错误信息列表
    """
    errors = []
    
    if not isinstance(file_path, str):
        errors.append("文件路径必须是字符串类型")
        return errors
    
    # 规范化路径
    normalized_path = os.path.normpath(file_path)
    
    # 检查路径遍历
    if '..' in normalized_path.split(os.sep):
        errors.append("文件路径包含路径遍历尝试")
    
    # 检查是否是有效的文件扩展名
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.txt', '.nc', '.cnc'}
    if os.path.splitext(normalized_path)[1].lower() not in allowed_extensions:
        errors.append(f"不支持的文件类型: {os.path.splitext(normalized_path)[1]}")
    
    return errors
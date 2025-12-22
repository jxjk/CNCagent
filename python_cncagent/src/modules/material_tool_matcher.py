"""
用户描述理解模块
使用规则匹配技术分析用户对加工需求的描述，提取关键信息如加工类型、材料、精度要求等
"""
import re
from typing import Dict, List, Optional


def analyze_user_description(description: str) -> Dict:
    """
    分析用户描述，提取关键信息
    
    Args:
        description (str): 用户对加工需求的描述
    
    Returns:
        dict: 包含提取信息的字典
    """
    # 分析加工类型
    processing_type = _identify_processing_type(description)
    
    # 提取数值信息（深度、转速等）
    depth = _extract_depth(description)
    feed_rate = _extract_feed_rate(description)
    spindle_speed = _extract_spindle_speed(description)
    
    # 提取材料信息
    material = _extract_material(description)
    
    # 提取精度要求
    precision = _extract_precision(description)
    
    # 提取孔位置信息
    hole_positions = _extract_hole_positions(description)
    
    # 确定所需刀具
    tool_required = _identify_tool_required(processing_type)
    
    return {
        "processing_type": processing_type,
        "tool_required": tool_required,
        "depth": depth,
        "feed_rate": feed_rate,
        "spindle_speed": spindle_speed,
        "material": material,
        "precision": precision,
        "hole_positions": hole_positions,  # 添加孔位置信息
        "description": description
    }


def _identify_processing_type(description: str) -> str:
    """识别加工类型"""
    description_lower = description.lower()
    
    # 关键词映射
    drilling_keywords = ['drill', 'hole', '钻孔', '打孔', '孔', '钻']
    milling_keywords = ['mill', 'milling', 'cut', 'cutting', '铣', '铣削', '切削']
    turning_keywords = ['turn', 'turning', 'lathe', '车', '车削']
    grinding_keywords = ['grind', 'grinding', '磨', '磨削']
    tapping_keywords = ['tapping', 'tap', '螺纹', '攻丝', 'thread', '丝锥']
    
    # 检查攻丝相关关键词（优先级高于钻孔）
    if any(keyword in description_lower for keyword in tapping_keywords):
        return 'tapping'
    elif any(keyword in description_lower for keyword in drilling_keywords):
        return 'drilling'
    elif any(keyword in description_lower for keyword in milling_keywords):
        return 'milling'
    elif any(keyword in description_lower for keyword in turning_keywords):
        return 'turning'
    elif any(keyword in description_lower for keyword in grinding_keywords):
        return 'grinding'
    else:
        return 'general'


def _identify_tool_required(processing_type: str) -> str:
    """根据加工类型确定需要的刀具"""
    # 对于攻丝工艺，我们使用完整的三步工艺，所以返回tap作为主要标识
    tool_mapping = {
        'drilling': 'drill_bit',
        'milling': 'end_mill',
        'turning': 'cutting_tool',
        'grinding': 'grinding_wheel',
        'tapping': 'tap'  # 新增攻丝类型
    }
    
    return tool_mapping.get(processing_type, 'general_tool')


def _extract_depth(description: str) -> Optional[float]:
    """提取加工深度"""
    # 匹配 "深度5mm" 或 "5mm深" 或简单的 "深度6" 等模式
    patterns = [
        r'深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'(\d+\.?\d*)\s*([mM]?[mM])\s*深',
        r'depth[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'深[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'螺纹深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',  # 螺纹深度
        r'攻丝深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',   # 攻丝深度
        r'深度\s*(\d+\.?\d*)\s*(?=，|。|;|:| |$)',  # 匹配 "深度6" 这格式
        r'(\d+\.?\d*)\s*(?=深度|mm深|深)',  # 匹配 "6深度" 格式
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description)
        for match in matches:
            try:
                # 如果匹配结果是元组（有多个组），取第一个
                if isinstance(match, tuple):
                    value = float(match[0])
                    # 如果还有单位信息
                    if len(match) > 1:
                        unit = match[1].lower()
                        if 'cm' in unit:
                            return value * 10
                        elif 'm' in unit and 'mm' not in unit:
                            return value * 1000
                        else:
                            return value  # 默认为mm
                    else:
                        return value  # 没有单位，默认为mm
                else:
                    value = float(match)
                    return value  # 默认为mm
            except (ValueError, TypeError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_feed_rate(description: str) -> Optional[float]:
    """提取进给速度"""
    patterns = [
        r'进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
        r'feed[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
        r'速度[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
        r'攻丝进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',  # 攻丝进给
        r'螺纹进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)'   # 螺纹进给
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_spindle_speed(description: str) -> Optional[float]:
    """提取主轴转速"""
    patterns = [
        r'转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',
        r'speed[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|rev/min)',
        r'主轴[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM)',
        r'攻丝转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',  # 攻丝转速
        r'螺纹转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)'   # 螺纹转速
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_material(description: str) -> Optional[str]:
    """提取材料信息"""
    materials = ['steel', 'aluminum', 'aluminium', 'titanium', 'copper', 'brass', 
                 'plastic', 'wood', 'steel', '不锈钢', '铝合金', '钛合金', '铜', 
                 '塑料', '木材', 'steel', '铁', 'metal', '金属']
    
    for material in materials:
        if material in description.lower():
            return material
    
    return None


def _extract_precision(description: str) -> Optional[str]:
    """提取精度要求"""
    # 匹配 "精度0.01mm" 或 "Ra1.6" 等
    patterns = [
        r'精度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'Ra\s*(\d+\.?\d*)',
        r'粗糙度[：:]?\s*Ra\s*(\d+\.?\d*)',
        r'精度[：:]?\s*Ra\s*(\d+\.?\d*)',
        r'螺纹精度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])'  # 螺纹精度
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            try:
                return f"Ra{match.group(1)}"
            except (IndexError, TypeError):
                continue  # 如果提取失败，继续尝试下一个模式
    
    return None


def _extract_hole_positions(description: str) -> List[tuple]:
    """
    从描述中提取孔位置信息
    支持格式如: "X10.0Y-16.0", "X=10, Y=-16", "位置X10 Y-16", "(80,7.5)", "(80,-7.5)", "（80,7.5）", "（80，-7.5）"等
    """
    positions = []
    seen_positions = set()  # 用于避免重复位置
    
    # 匹配 "X10.0Y-16.0" 格式
    pattern1 = r'X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)'
    matches1 = re.findall(pattern1, description)
    for match in matches1:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "X=10.0, Y=-16.0" 格式
    pattern2 = r'X\s*[=:]\s*([+-]?\d+\.?\d*)\s*[,，和]\s*Y\s*[=:]\s*([+-]?\d+\.?\d*)'
    matches2 = re.findall(pattern2, description)
    for match in matches2:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "X 10.0 Y -16.0" 格式（带空格）
    pattern3 = r'X\s+([+-]?\d+\.?\d*)\s+Y\s+([+-]?\d+\.?\d*)'
    matches3 = re.findall(pattern3, description)
    for match in matches3:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "(80,7.5)" 格式（英文圆括号坐标） - 只匹配不在中文括号内的
    pattern4 = r'\(\s*([+-]?\d+\.?\d*)\s*[,\s]\s*([+-]?\d+\.?\d*)\s*\)'
    matches4 = re.findall(pattern4, description)
    for match in matches4:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "（80,7.5）" 格式（中文圆括号坐标）
    pattern5 = r'（\s*([+-]?\d+\.?\d*)\s*[，,\s]\s*([+-]?\d+\.?\d*)\s*）'
    matches5 = re.findall(pattern5, description)
    for match in matches5:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "位置（80,7.5）" 或类似的中文描述
    pattern6 = r'[位置坐标]\s*（\s*([+-]?\d+\.?\d*)\s*[，,\s]\s*([+-]?\d+\.?\d*)\s*）'
    matches6 = re.findall(pattern6, description)
    for match in matches6:
        try:
            x = float(match[0])
            y = float(match[1])
            pos = (x, y)
            if pos not in seen_positions:
                positions.append(pos)
                seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    return positions
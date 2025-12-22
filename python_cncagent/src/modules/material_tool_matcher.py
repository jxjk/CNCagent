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
    
    if any(keyword in description_lower for keyword in drilling_keywords):
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
    tool_mapping = {
        'drilling': 'drill_bit',
        'milling': 'end_mill',
        'turning': 'cutting_tool',
        'grinding': 'grinding_wheel'
    }
    
    return tool_mapping.get(processing_type, 'general_tool')


def _extract_depth(description: str) -> Optional[float]:
    """提取加工深度"""
    # 匹配 "深度5mm" 或 "5mm深" 等模式
    patterns = [
        r'深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'(\d+\.?\d*)\s*([mM]?[mM])\s*深',
        r'depth[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
        r'深[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2).lower()
                
                # 如果单位是mm，则直接返回；如果是cm或m，则转换为mm
                if 'cm' in unit:
                    return value * 10
                elif 'm' in unit and 'mm' not in unit:
                    return value * 1000
                else:
                    return value  # 默认为mm
            except (ValueError, TypeError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_feed_rate(description: str) -> Optional[float]:
    """提取进给速度"""
    patterns = [
        r'进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
        r'feed[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
        r'速度[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)'
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
        r'主轴[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM)'
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
        r'精度[：:]?\s*Ra\s*(\d+\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            try:
                return f"Ra{match.group(1)}"
            except (IndexError, TypeError):
                continue  # 如果提取失败，继续尝试下一个模式
    
    return None
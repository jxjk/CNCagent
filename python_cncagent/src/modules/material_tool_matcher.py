"""
用户描述理解模块
使用规则匹配技术分析用户对加工需求的描述，提取关键信息如加工类型、材料、精度要求等
"""
import re
from typing import Dict, List, Optional, Tuple
from .mechanical_drawing_expert import MechanicalDrawingExpert
from src.exceptions import InputValidationError, handle_exception


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
    
    # 提取参考点信息
    reference_points = _extract_reference_points(description)
    
    # 提取沉孔直径信息
    outer_diameter, inner_diameter = _extract_counterbore_diameters(description)
    
    # 确定所需刀具
    tool_required = _identify_tool_required(processing_type)
    
    # 从描述中提取孔数量
    hole_count = _extract_hole_count(description)
    
    result = {
        "processing_type": processing_type,
        "tool_required": tool_required,
        "depth": depth,
        "feed_rate": feed_rate,
        "spindle_speed": spindle_speed,
        "material": material,
        "precision": precision,
        "hole_positions": hole_positions,  # 添加孔位置信息
        "reference_points": reference_points,  # 添加参考点信息
        "hole_count": hole_count,  # 添加孔数量信息
        "description": description
    }
    
    # 如果提取到沉孔直径信息，添加到结果中
    if outer_diameter is not None:
        result["outer_diameter"] = outer_diameter
    if inner_diameter is not None:
        result["inner_diameter"] = inner_diameter
    
    return result


def _identify_processing_type(description: str) -> str:
    """识别加工类型"""
    description_lower = description.lower()
    
    # 关键词映射 - 改进关键词匹配，增加更多变体
    counterbore_keywords = [
        '沉孔', 'counterbore', '锪孔', 'counter bore', 'counter-bore', 
        '沉头孔', '锪平孔', '埋头孔'
    ]
    drilling_keywords = [
        'drill', 'hole', '钻孔', '打孔', '孔', '钻', '钻削', '钻床'
    ]
    milling_keywords = [
        'mill', 'milling', 'cut', 'cutting', '铣', '铣削', '切削', 
        '铣床', '平面', '轮廓', '铣加工'
    ]
    turning_keywords = [
        'turn', 'turning', 'lathe', '车', '车削', '车床', '外圆', '内孔车削'
    ]
    grinding_keywords = [
        'grind', 'grinding', '磨', '磨削', '磨床', '精磨', '抛光'
    ]
    tapping_keywords = [
        'tapping', 'tap', '螺纹', '攻丝', 'thread', '丝锥', 
        '螺纹孔', '攻螺纹', '套丝'
    ]
    
    # 检查沉孔相关关键词（优先级最高）
    for keyword in counterbore_keywords:
        if keyword in description_lower:
            return 'counterbore'
    
    # 检查攻丝相关关键词
    for keyword in tapping_keywords:
        if keyword in description_lower:
            return 'tapping'
    
    # 检查钻孔相关关键词
    for keyword in drilling_keywords:
        if keyword in description_lower:
            return 'drilling'
    
    # 检查铣削相关关键词
    for keyword in milling_keywords:
        if keyword in description_lower:
            return 'milling'
    
    # 检查车削相关关键词
    for keyword in turning_keywords:
        if keyword in description_lower:
            return 'turning'
    
    # 检查磨削相关关键词
    for keyword in grinding_keywords:
        if keyword in description_lower:
            return 'grinding'
    
    return 'general'


def _identify_tool_required(processing_type: str) -> str:
    """根据加工类型确定需要的刀具"""
    # 对于攻丝工艺，我们使用完整的三步工艺，所以返回tap作为主要标识
    tool_mapping = {
        'drilling': 'drill_bit',
        'milling': 'end_mill',
        'turning': 'cutting_tool',
        'grinding': 'grinding_wheel',
        'tapping': 'tap',  # 新增攻丝类型
        'counterbore': 'counterbore_tool'  # 新增沉孔类型
    }
    
    return tool_mapping.get(processing_type, 'general_tool')


def _extract_depth(description: str) -> Optional[float]:
    """提取加工深度"""
    # 匹配 "深度5mm" 或 "5mm深" 或简单的 "深度6" 等模式 - 增强正则表达式
    patterns = [
        r'深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 支持"深度20mm"或"深度20"
        r'(\d+\.?\d*)\s*([mM]?[mM]?)\s*深',  # 支持"20mm深"或"20深"
        r'depth[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 英文支持
        r'深[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 支持"深20mm"
        r'螺纹深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 螺纹深度
        r'攻丝深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 攻丝深度
        r'锪孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 锪孔深度
        r'沉孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 沉孔深度
        r'钻孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 钻孔深度
        r'深度\s*(\d+\.?\d*)\s*(?=，|。|;|:| |$)',  # 匹配 "深度6" 这格式
        r'(\d+\.?\d*)\s*(?=深度|mm深|深)',  # 匹配 "6深度" 格式
        r'(\d+\.?\d*)\s*mm\s*(?=锪孔|沉孔|钻孔|攻丝|螺纹)',  # 如"20mm锪孔"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            try:
                # 如果匹配结果是元组（有多个组），取第一个
                if isinstance(match, tuple):
                    value = float(match[0])
                    # 如果还有单位信息
                    if len(match) > 1:
                        unit = match[1].lower().strip()
                        if 'cm' in unit:
                            return value * 10
                        elif 'm' in unit and 'mm' not in unit:
                            return value * 1000
                        elif 'mm' in unit or unit == '':  # 默认为mm，或明确指定mm
                            return value
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
    # 改进的进给速度提取模式，支持更多格式
    patterns = [
        r'(?:进给|feed|进刀|走刀)[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev|mm/min|mm/s|mm/rev|f)',
        r'(?:进给|feed|进刀|走刀)\s*[：:]?\s*(\d+\.?\d*)',
        r'f\s*(\d+\.?\d*)\s*(?:mm/min|mm/s|mm/rev|mm/min|mm/s|mm/rev)?',  # F100格式
        r'(?:速度|speed)[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev|mm/min|mm/s|mm/rev)',
        r'攻丝进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',  # 攻丝进给
        r'螺纹进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',   # 螺纹进给
        r'钻孔进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',   # 钻孔进给
        r'铣削进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',   # 铣削进给
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                # 检查单位，如果没有单位，默认为mm/min
                if len(match.groups()) > 1 and match.group(2):
                    unit = match.group(2).lower()
                    # 这里可以根据单位进行转换，当前统一返回数值
                    return value
                else:
                    return value  # 默认为mm/min
            except (ValueError, TypeError, IndexError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_spindle_speed(description: str) -> Optional[float]:
    """提取主轴转速"""
    # 改进的主轴转速提取模式，支持更多格式
    patterns = [
        r'(?:转速|speed|spindle|主轴)[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟|转每分钟|转/min)',
        r'(?:转速|speed|spindle|主轴)\s*[：:]?\s*(\d+\.?\d*)',
        r's\s*(\d+\.?\d*)\s*(?:rpm|RPM|转/分钟|转每分钟)?',  # S1000格式
        r'(?:主轴|spindle)[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',
        r'攻丝转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',  # 攻丝转速
        r'螺纹转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',   # 螺纹转速
        r'钻孔转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',   # 钻孔转速
        r'铣削转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',   # 铣削转速
        r'车削转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',   # 车削转速
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                # 检查单位，如果没有单位，默认为rpm
                if len(match.groups()) > 1 and match.group(2):
                    unit = match.group(2).lower()
                    # 这里可以根据单位进行转换，当前统一返回数值
                    return value
                else:
                    return value  # 默认为rpm
            except (ValueError, TypeError, IndexError):
                continue  # 如果转换失败，继续尝试下一个模式
    
    return None


def _extract_material(description: str) -> Optional[str]:
    """提取材料信息"""
    # 改进的材料识别模式，包含更多材料类型
    patterns = [
        r'(?:材料|material)\s*[：:]?\s*([a-zA-Z\u4e00-\u9fa5]+)',
        r'([a-zA-Z\u4e00-\u9fa5]+)\s*(?:材料|material)',
        r'(\w+)\s*(?:板|件|工件)',
    ]
    
    # 通用材料关键词
    materials = [
        'steel', 'aluminum', 'aluminium', 'titanium', 'copper', 'brass', 
        'plastic', 'wood', 'steel', '不锈钢', '铝合金', '钛合金', '铜', 
        '塑料', '木材', 'steel', '铁', 'metal', '金属', '碳钢', '合金钢',
        '铸铁', '青铜', '黄铜', '有机玻璃', '亚克力', 'abs', 'pc', 'pvc',
        '45号钢', '40cr', '304', '316', '6061', '7075', 'a356'
    ]
    
    # 首先尝试正则表达式匹配
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            material = match.group(1).lower()
            # 验证是否为真实材料
            for valid_material in materials:
                if valid_material in material or material in valid_material:
                    return material
    
    # 然后尝试关键词匹配
    description_lower = description.lower()
    for material in materials:
        if material in description_lower:
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


def _extract_reference_points(description: str) -> Dict[str, Tuple[float, float]]:
    """
    从描述中提取参考点信息
    支持格式如: "以左下角为原点", "基准A", "datum A", "原点(0,0)", "origin(0,0)"等
    
    Args:
        description: 用户描述字符串
        
    Returns:
        Dict: 包含参考点名称和坐标的字典
    """
    reference_points = {}
    
    # 匹配以某点为原点的描述
    origin_patterns = [
        r'以\s*([东南西北上下前后左右中])\s*([东南西北上下前后左右中])\s*角为原点',
        r'原点[：:]?\s*[:：]?\s*([-\d.]+)\s*,\s*([-\d.]+)',
        r'origin[：:]?\s*[:：]?\s*([-\d.]+)\s*,\s*([-\d.]+)',
        r'原点[：:]?\s*[:：]?\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
        r'origin[：:]?\s*[:：]?\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
    ]
    
    for pattern in origin_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            if len(match) == 2 and match[0].isdigit() and match[1].isdigit():
                # 坐标原点格式
                x, y = float(match[0]), float(match[1])
                reference_points['origin'] = (x, y)
            elif len(match) == 2 and all(c in '东南西北上下前后左右中' for c in match):
                # 角点描述格式
                direction = ''.join(match)
                reference_points[f'origin_{direction}'] = (0, 0)
    
    # 匹配基准点描述
    datum_patterns = [
        r'基准\s*([A-Z])',
        r'datum\s*([A-Z])',
        r'reference\s*([A-Z])',
        r'基准点\s*([A-Z])',
    ]
    
    for pattern in datum_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            reference_points[f'datum_{match.upper()}'] = (0, 0)
    
    # 匹配自定义参考点
    custom_patterns = [
        r'参考点\s*([A-Z])\s*[：:]?\s*([-\d.]+)\s*,\s*([-\d.]+)',
        r'reference\s+point\s*([A-Z])\s*[：:]?\s*([-\d.]+)\s*,\s*([-\d.]+)',
    ]
    
    for pattern in custom_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                point_name = match[0].upper()
                x, y = float(match[1]), float(match[2])
                reference_points[f'custom_{point_name}'] = (x, y)
    
    return reference_points


def _extract_counterbore_diameters(description: str) -> tuple:
    """
    从描述中提取沉孔的外径和内径
    
    Args:
        description: 用户描述字符串
        
    Returns:
        tuple: (外径, 内径) 或 (None, None) 如果没有找到
    """
    description_lower = description.lower()
    
    # 匹配"φ22深20底孔φ14.5贯通"或类似格式的沉孔描述
    # 使用更精确的模式，确保直径数字出现在沉孔相关上下文中，避免匹配坐标和无关数字
    patterns = [
        r'(?:加工|沉孔|counterbore|锪孔).*?φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|counterbore|锪孔|深|，|\.|;).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:底孔|贯通|thru|，|\.|;).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通|贯通孔|钻孔)', # 加工φ22沉孔深20 φ14.5底孔/贯通
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|counterbore|锪孔).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:底孔|贯通|thru|，|\.|;).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通|贯通孔|钻孔)',  # φ22沉孔深20 φ14.5底孔/贯通
        r'φ\s*(\d+(?:\.\d+)?).*?沉孔.*?深.*?φ\s*(\d+(?:\.\d+)?)\s*底孔',  # φ22沉孔深20 φ14.5底孔
        r'沉孔.*?φ\s*(\d+(?:\.\d+)?).*?深.*?φ\s*(\d+(?:\.\d+)?)\s*底孔',  # 沉孔φ22深20 φ14.5底孔
        r'(\d+)\s*个.*?φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|counterbore|锪孔).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?.*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*贯通',  # 3个φ22沉孔深20 底孔φ14.5贯通
        r'φ\s*(\d+(?:\.\d+)?).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:沉孔|counterbore|锪孔).*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*贯通',  # φ22深20沉孔 底孔φ14.5贯通
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|counterbore|锪孔).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通)',  # φ22锪孔 φ14.5底孔
        r'沉孔.*?φ\s*(\d+(?:\.\d+)?)\s*.*?底孔.*?φ\s*(\d+(?:\.\d+)?)',  # 沉孔φ22 底孔φ14.5
        r'锪孔.*?φ\s*(\d+(?:\.\d+)?)\s*.*?钻孔.*?φ\s*(\d+(?:\.\d+)?)',  # 锪孔φ22 钻孔φ14.5
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description_lower)
        for match in matches:
            try:
                # 根据匹配的模式，提取外径和内径
                if len(match) >= 3:  # 包含数量的模式
                    outer_diameter = float(match[1])  # 外径
                    inner_diameter = float(match[2])  # 内径
                elif len(match) == 2:  # 外径和内径的模式
                    outer_diameter = float(match[0])
                    inner_diameter = float(match[1])
                else:
                    continue
                
                # 确保提取的直径在合理范围内，排除误匹配的数字（如φ234中的数字）
                # 并确保外径大于内径
                if outer_diameter > 100 or inner_diameter > 100:  # 扩大合理范围到100mm
                    continue
                if outer_diameter <= inner_diameter:  # 外径应该大于内径
                    continue
                if outer_diameter <= 0 or inner_diameter <= 0:  # 确保直径为正数
                    continue
                
                return outer_diameter, inner_diameter
            except (ValueError, IndexError):
                continue
    
    # 如果上述模式没有匹配到，尝试提取描述末尾的直径信息
    # 格式如: "...φ22深20，φ14.5贯通底孔"
    end_patterns = [
        r'φ\s*(\d+(?:\.\d+)?)\s*深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:沉孔|counterbore|锪孔|，|\.|;).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通|，|\.|;)',  # φ22深20，φ14.5贯通底孔
    ]
    
    for pattern in end_patterns:
        matches = re.findall(pattern, description_lower)
        for match in matches:
            try:
                if len(match) == 2:
                    outer_diameter = float(match[0])
                    inner_diameter = float(match[1])
                    # 确保提取的直径在合理范围内
                    # 并确保外径大于内径
                    if outer_diameter > 100 or inner_diameter > 100:
                        continue
                    if outer_diameter <= inner_diameter:  # 外径应该大于内径
                        continue
                    if outer_diameter <= 0 or inner_diameter <= 0:  # 确保直径为正数
                        continue
                    return outer_diameter, inner_diameter
            except (ValueError, IndexError):
                continue
    
    return None, None


def _extract_hole_count(description: str) -> int:
    """
    从描述中提取孔的数量
    
    Args:
        description: 用户描述字符串
        
    Returns:
        int: 孔的数量，如果没有找到则返回1
    """
    # 匹配"3个φ22沉孔"或"3个孔"等模式
    patterns = [
        r'(\d+)\s*个.*?(?:沉孔|孔|hole|holes)',
        r'(\d+)\s*个',
        r'总共.*?(\d+)\s*个',
        r'共计.*?(\d+)\s*个',
        r'(\d+)\s*个.*?(?:螺纹|钻|锪|沉)',
        r'([一二三四五六七八九十])\s*个.*?(?:沉孔|孔|hole|holes)',  # 支持中文数字
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            try:
                if match in ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']:
                    # 中文数字转换
                    chinese_to_num = {
                        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
                    }
                    return chinese_to_num.get(match, 1)
                else:
                    return int(match)
            except (ValueError, TypeError):
                continue
    
    # 如果没有找到明确数量，默认为1个
    return 1
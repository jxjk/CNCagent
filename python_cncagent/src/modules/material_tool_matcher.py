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
    # 确保描述字符串使用UTF-8编码处理中文字符
    if isinstance(description, bytes):
        try:
            description = description.decode('utf-8')
        except UnicodeError:
            description = description.decode('utf-8', errors='replace')
    elif not isinstance(description, str):
        description = str(description)
    
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
    
    # 改进关键词匹配逻辑，使用更精确的模式匹配，避免冲突
    # 使用正则表达式和更复杂的匹配逻辑
    
    # 沉孔相关关键词（最高优先级）
    counterbore_patterns = [
        r'(?:沉孔|counterbore|锪孔|counter bore|counter-bore|沉头孔|锪平孔|埋头孔)',
        r'(?:沉孔|锪孔).*?(?:深|深度|φ\d+|底孔)',
        r'φ\d+.*?(?:沉孔|锪孔)',
    ]
    
    # 攻丝相关关键词（第二优先级）
    tapping_patterns = [
        r'(?:tapping|tap|螺纹|攻丝|thread|丝锥|螺纹孔|攻螺纹|套丝)',
        r'(?:攻丝|螺纹).*?(?:M\d+|螺纹)',
    ]
    
    # 钻孔相关关键词（第三优先级）
    drilling_patterns = [
        r'(?:drill|hole|钻孔|打孔|孔|钻|钻削|钻床)',
        r'(?:钻|孔).*?(?:深|深度|φ\d+)',
        r'φ\d+.*?(?:钻|孔)',
    ]
    
    # 铣削相关关键词（第四优先级，避免与沉孔混淆）
    milling_patterns = [
        r'(?<!锪)(?<!沉)(?<!攻)(?<!钻)(?:mill|milli|铣|铣削|铣床|切削|平面|轮廓|铣加工)',
        r'(?:铣|mill).*?(?:平面|轮廓|外形|周边)',
    ]
    
    # 车削相关关键词（第五优先级）
    turning_patterns = [
        r'(?:turn|turning|lathe|车|车削|车床|外圆|内孔车削)',
    ]
    
    # 磨削相关关键词（第六优先级）
    grinding_patterns = [
        r'(?:grind|grinding|磨|磨削|磨床|精磨|抛光)',
    ]
    
    # 按优先级顺序检查
    for pattern in counterbore_patterns:
        if re.search(pattern, description_lower):
            return 'counterbore'
    
    for pattern in tapping_patterns:
        if re.search(pattern, description_lower):
            return 'tapping'
    
    for pattern in drilling_patterns:
        if re.search(pattern, description_lower):
            return 'drilling'
    
    # 特别处理铣削，避免与沉孔/锪孔混淆
    for pattern in milling_patterns:
        if re.search(pattern, description_lower):
            # 额外检查是否包含锪孔/沉孔关键词，如果有则优先返回counterbore
            if re.search(r'(?:沉孔|锪孔|counterbore)', description_lower):
                return 'counterbore'  # 沉孔优先级更高
            return 'milling'
    
    for pattern in turning_patterns:
        if re.search(pattern, description_lower):
            return 'turning'
    
    for pattern in grinding_patterns:
        if re.search(pattern, description_lower):
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
    # 修复：优先匹配与深度相关的关键词，避免将φ22等直径误认为深度
    # 匹配 "深度5mm" 或 "5mm深" 或简单的 "深度6" 等模式 - 增强正则表达式
    patterns = [
        r'沉孔.*?深[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # "沉孔深20mm" - 最高优先级
        r'(?:锪孔|沉孔|钻孔|攻丝|螺纹)\s*深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 优先匹配具体加工类型+深度
        r'深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 支持"深度20mm"或"深度20"
        r'(?:锪孔|沉孔|钻孔|攻丝|螺纹)\s*(\d+\.?\d*)\s*([mM]?[mM]?)\s*深',  # 支持"锪孔20mm深"
        r'(\d+\.?\d*)\s*([mM]?[mM]?)\s*深',  # 支持"20mm深"或"20深"
        r'depth[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 英文支持
        r'深[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 支持"深20mm"
        r'螺纹深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',  # 螺纹深度
        r'攻丝深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 攻丝深度
        r'锪孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 锪孔深度
        r'沉孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 沉孔深度
        r'钻孔深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM]?)',   # 钻孔深度
        r'深度\s*(\d+\.?\d*)\s*(?=，|。|;|:| |$)',  # 匹配 "深度6" 这格式
        r'(\d+\.?\d*)\s*mm\s*(?=锪孔|沉孔|钻孔|攻丝|螺纹)',  # 如"20mm锪孔"
        # 避免匹配φ22这样的直径 - 不再使用简单的数字匹配
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
    支持极坐标格式: "R=50 θ=30°", "R50θ30", "极径50 极角30度"等
    """
    positions = []
    seen_positions = set()  # 用于避免重复位置
    
    # 匹配极坐标格式 - R和角度
    polar_patterns = [
        r'R\s*[=:]\s*(\d+\.?\d*)\s*(?:θ|theta|角度|θ=|θ:)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R=50 θ=30°
        r'R\s*(\d+\.?\d*)\s*(?:θ|theta|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R50θ30
        r'(?:极径|半径)\s*(\d+\.?\d*)\s*(?:极角|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # 极径50 极角30度
    ]
    
    for pattern in polar_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            try:
                radius = float(match[0])
                angle_deg = float(match[1])
                # 将极坐标转换为直角坐标
                import math
                angle_rad = math.radians(angle_deg)
                x = radius * math.cos(angle_rad)
                y = radius * math.sin(angle_rad)
                
                # 验证转换后的坐标是否在合理范围内
                if -200 <= x <= 200 and -200 <= y <= 200:
                    pos = (round(x, 3), round(y, 3))
                    if pos not in seen_positions:
                        positions.append(pos)
                        seen_positions.add(pos)
            except (ValueError, TypeError, AttributeError):
                continue

    # 匹配 "X10.0Y-16.0" 格式
    # 首先匹配所有X-Y格式
    pattern1_general = r'X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)'
    all_matches = re.findall(pattern1_general, description)
    for match in all_matches:
        try:
            x = float(match[0])
            y = float(match[1])
            # 检查这个X-Y坐标是否紧跟在φ数字后面（避免误匹配孔径信息）
            # 修复：更精确地检查X坐标是否可能是直径而不是位置
            # 查找X坐标在原文中的位置
            x_pattern = r'X\s*' + re.escape(match[0])
            x_matches = list(re.finditer(x_pattern, description))
            
            is_valid = True
            for x_match in x_matches:
                # 检查X坐标前是否有"φ数字"模式（如"φ22 X10"这种情况，X坐标可能是孔径而不是位置）
                start_search = max(0, x_match.start() - 20)  # 向前搜索20个字符
                preceding_text = description[start_search:x_match.start()]
                # 检查是否有φ+数字的模式
                phi_pattern = r'φ\s*\d+\.?\d*'
                if re.search(phi_pattern, preceding_text):
                    is_valid = False
                    break
                
                # 进一步检查：如果X值与已知的沉孔直径相似，则不将其作为位置
                # 获取从描述中提取的已知直径
                from .material_tool_matcher import _extract_counterbore_diameters
                outer_dia, inner_dia = _extract_counterbore_diameters(description)
                if outer_dia and abs(x - outer_dia) < 2:  # 允许2mm的误差
                    is_valid = False
                    break
                if inner_dia and abs(x - inner_dia) < 2:
                    is_valid = False
                    break
            
            # 同样检查Y坐标前是否有φ数字模式
            y_pattern = r'Y\s*' + re.escape(match[1])
            y_matches = list(re.finditer(y_pattern, description))
            
            for y_match in y_matches:
                start_search = max(0, y_match.start() - 20)  # 向前搜索20个字符
                preceding_text = description[start_search:y_match.start()]
                phi_pattern = r'φ\s*\d+\.?\d*'
                if re.search(phi_pattern, preceding_text):
                    is_valid = False
                    break
            
            # 扩大坐标范围以容纳更大的Y值
            if is_valid and -300 <= x <= 300 and -300 <= y <= 300:
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
            # 验证坐标值是否在合理范围内，避免匹配到其他数字
            # 检查是否与已知直径冲突
            from .material_tool_matcher import _extract_counterbore_diameters
            outer_dia, inner_dia = _extract_counterbore_diameters(description)
            if not ((outer_dia and abs(x - outer_dia) < 2) or (inner_dia and abs(x - inner_dia) < 2)):
                if -300 <= x <= 300 and -300 <= y <= 300:
                    pos = (x, y)
                    if pos not in seen_positions:
                        positions.append(pos)
                        seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "X 10.0 Y -16.0" 格式（带空格）
    # 用同样的方法处理
    pattern3_general = r'X\s+([+-]?\d+\.?\d*)\s+Y\s+([+-]?\d+\.?\d*)'
    all_matches3 = re.findall(pattern3_general, description)
    for match in all_matches3:
        try:
            x = float(match[0])
            y = float(match[1])
            # 检查这个X-Y坐标是否紧跟在φ数字后面
            x_pattern = r'X\s+' + re.escape(match[0])
            x_matches = list(re.finditer(x_pattern, description))
            
            is_valid = True
            for x_match in x_matches:
                # 检查X坐标前是否有"φ数字"模式
                start_search = max(0, x_match.start() - 20)  # 向前搜索20个字符
                preceding_text = description[start_search:x_match.start()]
                # 检查是否有φ+数字的模式
                phi_pattern = r'φ\s*\d+\.?\d*'
                if re.search(phi_pattern, preceding_text):
                    is_valid = False
                    break
                
                # 检查X值是否与已知直径相似
                from .material_tool_matcher import _extract_counterbore_diameters
                outer_dia, inner_dia = _extract_counterbore_diameters(description)
                if outer_dia and abs(x - outer_dia) < 2:
                    is_valid = False
                    break
                if inner_dia and abs(x - inner_dia) < 2:
                    is_valid = False
                    break
            
            # 同样检查Y坐标前是否有φ数字模式
            y_pattern = r'Y\s+' + re.escape(match[1])
            y_matches = list(re.finditer(y_pattern, description))
            
            for y_match in y_matches:
                start_search = max(0, y_match.start() - 20)  # 向前搜索20个字符
                preceding_text = description[start_search:y_match.start()]
                phi_pattern = r'φ\s*\d+\.?\d*'
                if re.search(phi_pattern, preceding_text):
                    is_valid = False
                    break
            
            if is_valid and -300 <= x <= 300 and -300 <= y <= 300:
                pos = (x, y)
                if pos not in seen_positions:
                    positions.append(pos)
                    seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "(80,7.5)" 格式（英文圆括号坐标） - 只匹配不在中文括号内的
    # 避免匹配"坐标原点（0,0）"这类描述
    pattern4 = r'\(\s*([+-]?\d+\.?\d*)\s*[,\s]\s*([+-]?\d+\.?\d*)\s*\)'
    all_matches4 = re.findall(pattern4, description)
    for match in all_matches4:
        try:
            x = float(match[0])
            y = float(match[1])
            # 检查这个坐标是否是坐标原点描述
            # 查找坐标在原文中的位置
            coord_pattern = r'\(\s*' + re.escape(match[0]) + r'\s*[,\s]\s*' + re.escape(match[1]) + r'\s*\)'
            coord_matches = list(re.finditer(coord_pattern, description))
            
            is_valid = True
            for coord_match in coord_matches:
                # 检查坐标前后是否有"坐标原点"、"原点"等描述
                start_search = max(0, coord_match.start() - 20)  # 向前搜索20个字符
                end_search = min(len(description), coord_match.end() + 20)  # 向后搜索20个字符
                surrounding_text = description[start_search:end_search].lower()
                # 检查是否包含原点相关的描述
                if re.search(r'(?:坐标原点|原点|origin)', surrounding_text):
                    is_valid = False
                    break
                
                # 检查坐标值是否与直径值冲突
                from .material_tool_matcher import _extract_counterbore_diameters
                outer_dia, inner_dia = _extract_counterbore_diameters(description)
                if outer_dia and abs(x - outer_dia) < 2:
                    is_valid = False
                    break
                if inner_dia and abs(x - inner_dia) < 2:
                    is_valid = False
                    break
            
            # 验证坐标值是否在合理范围内，避免匹配到其他数字
            if is_valid and -300 <= x <= 300 and -300 <= y <= 300:
                pos = (x, y)
                if pos not in seen_positions:
                    positions.append(pos)
                    seen_positions.add(pos)
        except (ValueError, TypeError):
            continue

    # 匹配 "（80,7.5）" 格式（中文圆括号坐标）
    # 避免匹配"坐标原点（0,0）"这类描述
    pattern5 = r'（\s*([+-]?\d+\.?\d*)\s*[，,\s]\s*([+-]?\d+\.?\d*)\s*）'
    all_matches5 = re.findall(pattern5, description)
    for match in all_matches5:
        try:
            x = float(match[0])
            y = float(match[1])
            # 检查这个坐标是否是坐标原点描述
            # 查找坐标在原文中的位置
            coord_pattern = r'（\s*' + re.escape(match[0]) + r'\s*[，,\s]\s*' + re.escape(match[1]) + r'\s*）'
            coord_matches = list(re.finditer(coord_pattern, description))
            
            is_valid = True
            for coord_match in coord_matches:
                # 检查坐标前后是否有"坐标原点"、"原点"等描述
                start_search = max(0, coord_match.start() - 20)  # 向前搜索20个字符
                end_search = min(len(description), coord_match.end() + 20)  # 向后搜索20个字符
                surrounding_text = description[start_search:end_search].lower()
                # 检查是否包含原点相关的描述
                if re.search(r'(?:坐标原点|原点|origin)', surrounding_text):
                    is_valid = False
                    break
                
                # 检查坐标值是否与直径值冲突
                from .material_tool_matcher import _extract_counterbore_diameters
                outer_dia, inner_dia = _extract_counterbore_diameters(description)
                if outer_dia and abs(x - outer_dia) < 2:
                    is_valid = False
                    break
                if inner_dia and abs(x - inner_dia) < 2:
                    is_valid = False
                    break
            
            # 验证坐标值是否在合理范围内，避免匹配到其他数字
            if is_valid and -300 <= x <= 300 and -300 <= y <= 300:
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
            # 验证坐标值是否在合理范围内，避免匹配到其他数字
            # 检查是否与已知直径冲突
            from .material_tool_matcher import _extract_counterbore_diameters
            outer_dia, inner_dia = _extract_counterbore_diameters(description)
            if not ((outer_dia and abs(x - outer_dia) < 2) or (inner_dia and abs(x - inner_dia) < 2)):
                if -300 <= x <= 300 and -300 <= y <= 300:
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
    
    # 优化的模式，能更好地匹配目标描述 "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    # 提高匹配的准确性，避免误匹配
    patterns = [
        # 最精确的模式：匹配"加工3个φXX深YY底孔φZZ贯通"格式
        r'(?:加工|要求|需要)\s*(?:\d+)\s*个.*?φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore|沉头孔).*?深\s*(?:\d+(?:\.\d+)?(?:\s*mm)?(?:\s*[，,\.])?)?.*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*(?:贯通|thru|通孔|穿透)',
        # 匹配"φXX深YY底孔φZZ贯通"格式
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore|沉头孔).*?深\s*(?:\d+(?:\.\d+)?(?:\s*mm)?)?.*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*(?:贯通|thru|通孔)',
        # 匹配"φXX锪孔深度YY φZZ底孔"格式
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:锪孔|沉孔|counterbore).*?(?:深度|深)\s*(?:\d+(?:\.\d+)?(?:\s*mm)?)?.*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|通孔|thru)',
        # 匹配"φXX沉孔，深度YY，底孔φZZ贯通"格式
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore).*?(?:，|\.|;).*?(?:深度|深)\s*(?:\d+(?:\.\d+)?(?:\s*mm)?)?.*?(?:，|\.|;).*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*(?:贯通|thru|通孔)',
        # 匹配"沉孔φXX深YY底孔φZZ"格式
        r'(?:沉孔|锪孔|counterbore).*?φ\s*(\d+(?:\.\d+)?).*?深\s*(?:\d+(?:\.\d+)?(?:\s*mm)?)?.*?底孔\s*φ\s*(\d+(?:\.\d+)?)',
        # 匹配"φXX锪孔 φYY底孔"格式
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:锪孔|沉孔|counterbore|沉头孔).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|通孔|thru|贯通)',
        # 原有模式作为备选
        r'(?:加工|沉孔|锪孔|counterbore).*?φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore|深|，|\.|;).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:底孔|贯通|thru|，|\.|;).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通|贯通孔|钻孔)',
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:底孔|贯通|thru|，|\.|;).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|thru|贯通|贯通孔|钻孔)',
        r'φ\s*(\d+(?:\.\d+)?).*?沉孔.*?深.*?φ\s*(\d+(?:\.\d+)?)\s*底孔',
        r'沉孔.*?φ\s*(\d+(?:\.\d+)?).*?深.*?φ\s*(\d+(?:\.\d+)?)\s*底孔',
        r'(\d+)\s*个.*?φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?.*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*贯通',
        r'φ\s*(\d+(?:\.\d+)?).*?深\s*(?:\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:沉孔|锪孔|counterbore).*?底孔\s*φ\s*(\d+(?:\.\d+)?)\s*贯通',
        # 通用模式，匹配"φXX 沉孔" 和 "φYY 底孔"形式
        r'φ\s*(\d+(?:\.\d+)?)\s*(?:沉孔|锪孔|counterbore).*?φ\s*(\d+(?:\.\d+)?)\s*(?:底孔|钻孔|thru|贯通)',
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
                
                # 确保提取的直径在合理范围内，排除误匹配的数字
                # 并确保外径大于内径
                if outer_diameter > 100 or inner_diameter > 100:  # 扩大合理范围到100mm
                    continue
                if outer_diameter <= inner_diameter:  # 外径应该大于内径
                    continue
                if outer_diameter <= 0 or inner_diameter <= 0:  # 确保直径为正数
                    continue
                if inner_diameter >= outer_diameter * 0.9:  # 确保内外径差异合理（内径不应接近外径）
                    continue
                
                return outer_diameter, inner_diameter
            except (ValueError, IndexError):
                continue
    
    # 如果上面的模式都没匹配到，尝试更通用的提取方法
    # 先提取所有直径
    diameter_matches = re.findall(r'φ\s*(\d+(?:\.\d+)?)', description_lower)
    if len(diameter_matches) >= 2:
        try:
            # 检查描述中是否包含"沉孔"或"锪孔"等关键词
            if re.search(r'(?:沉孔|锪孔|counterbore|锪平|沉头)', description_lower):
                # 从描述中过滤掉可能的图纸参考尺寸（通常是第一个出现的φ值，如φ234）
                # 查找与"沉孔"、"锪孔"、"底孔"、"贯通"相关的直径
                relevant_diameters = []
                
                # 查找与沉孔加工相关的直径描述
                # 匹配 "φXX沉孔" 或 "沉孔φXX" 格式
                counterbore_dia_matches = re.findall(r'(?:沉孔|锪孔|counterbore|锪平|沉头).*?φ\s*(\d+(?:\.\d+)?)|φ\s*(\d+(?:\.\d+)?).*?(?:沉孔|锪孔|counterbore|锪平|沉头)', description_lower)
                for match in counterbore_dia_matches:
                    # match 是一个元组，取非空的值
                    dia = match[0] if match[0] else match[1]
                    if dia:
                        try:
                            relevant_diameters.append(float(dia))
                        except ValueError:
                            continue
                
                # 查找与底孔相关的直径
                bottom_hole_dia_matches = re.findall(r'(?:底孔|贯通|thru|通孔|钻孔).*?φ\s*(\d+(?:\.\d+)?)|φ\s*(\d+(?:\.\d+)?).*?(?:底孔|贯通|thru|通孔|钻孔)', description_lower)
                for match in bottom_hole_dia_matches:
                    # match 是一个元组，取非空的值
                    dia = match[0] if match[0] else match[1]
                    if dia:
                        try:
                            relevant_diameters.append(float(dia))
                        except ValueError:
                            continue
                
                # 如果找到了相关直径，使用它们
                if len(relevant_diameters) >= 2:
                    # 过滤合理范围内的直径
                    valid_diameters = [d for d in relevant_diameters if 2 <= d <= 50]
                    if len(valid_diameters) >= 2:
                        # 排序，通常外径较大
                        diameters_sorted = sorted(valid_diameters, reverse=True)
                        # 确保内外径差异合理
                        if diameters_sorted[0] > diameters_sorted[1] and diameters_sorted[1] < diameters_sorted[0] * 0.9:
                            return diameters_sorted[0], diameters_sorted[1]  # 外径，内径
                
                # 如果上面方法没找到，尝试使用原始方法但排除明显不合理的值
                all_diameters = [float(d) for d in diameter_matches if 2 <= float(d) <= 100]
                # 过滤掉可能的图纸参考尺寸（如φ234），这些通常与沉孔加工无关
                filtered_diameters = [d for d in all_diameters if d <= 50]  # 沉孔很少会是φ50以上
                if len(filtered_diameters) >= 2:
                    diameters_sorted = sorted(filtered_diameters, reverse=True)
                    # 确保内外径差异合理
                    if diameters_sorted[0] > diameters_sorted[1] and diameters_sorted[1] < diameters_sorted[0] * 0.9:
                        return diameters_sorted[0], diameters_sorted[1]  # 外径，内径
        except:
            pass
    
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
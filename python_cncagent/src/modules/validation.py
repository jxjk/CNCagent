"""
CNC加工验证和错误处理模块
"""
import re
from typing import Dict, List, Any, Tuple, Set


def validate_gcode_blocks(gcode_blocks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    验证G代码块的有效性
    
    Args:
        gcode_blocks: G代码块列表
        
    Returns:
        验证结果，包含错误和警告
    """
    if not isinstance(gcode_blocks, list):
        raise ValueError('G代码块必须是列表')

    errors = []
    warnings = []

    for i, block in enumerate(gcode_blocks):
        if not block or not isinstance(block, dict):
            errors.append(f'G代码块 {i} 无效: 不是字典')
            continue

        if not block.get('id') or not isinstance(block.get('id'), str):
            errors.append(f'G代码块 {i} 无效: 缺少有效的ID')

        if not isinstance(block.get('code'), list):
            errors.append(f'G代码块 {i} 无效: 代码不是列表')
            continue

        # 检查代码行
        for j, line in enumerate(block.get('code', [])):
            if not isinstance(line, str):
                errors.append(f'G代码块 {i} 行 {j} 无效: 代码行不是字符串')

        # 检查是否存在危险的G代码指令
        for j, line in enumerate(block.get('code', [])):
            if 'M30' in line.upper() and j != len(block.get('code', [])) - 1:
                warnings.append(f'G代码块 {i}: 程序结束指令M30不在最后')

    return {'errors': errors, 'warnings': warnings}


def validate_feature_parameters(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证特征参数的有效性
    
    Args:
        feature: 特征对象
        
    Returns:
        验证结果
    """
    if not feature or not isinstance(feature, dict):
        return {'valid': False, 'errors': ['特征参数无效']}

    errors = []

    if not feature.get('feature_type'):
        errors.append('缺少特征类型')

    params = feature.get('parameters', {})
    if not isinstance(params, dict):
        errors.append('缺少特征参数或参数格式无效')
    else:
        feature_type = feature.get('feature_type')

        if feature_type in ['hole', 'counterbore']:
            if isinstance(params.get('diameter'), (int, float)) and params['diameter'] <= 0:
                errors.append('孔径必须大于0')
            if isinstance(params.get('depth'), (int, float)) and params['depth'] <= 0:
                errors.append('深度必须大于0')
        elif feature_type == 'pocket':
            if isinstance(params.get('width'), (int, float)) and params['width'] <= 0:
                errors.append('宽度必须大于0')
            if isinstance(params.get('length'), (int, float)) and params['length'] <= 0:
                errors.append('长度必须大于0')
            if isinstance(params.get('depth'), (int, float)) and params['depth'] <= 0:
                errors.append('深度必须大于0')
        elif feature_type == 'thread':
            if isinstance(params.get('diameter'), (int, float)) and params['diameter'] <= 0:
                errors.append('螺纹直径必须大于0')
            if isinstance(params.get('pitch'), (int, float)) and params['pitch'] <= 0:
                errors.append('螺距必须大于0')

    return {'valid': len(errors) == 0, 'errors': errors}


def validate_geometry_elements(geometry_elements: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    验证几何元素的有效性
    
    Args:
        geometry_elements: 几何元素列表
        
    Returns:
        验证结果
    """
    if not isinstance(geometry_elements, list):
        return {'valid': False, 'errors': ['几何元素必须是列表']}

    errors = []
    warnings = []

    for i, element in enumerate(geometry_elements):
        if not element or not isinstance(element, dict):
            errors.append(f'几何元素 {i} 无效: 不是字典')
            continue

        if not element.get('type'):
            errors.append(f'几何元素 {i} 无效: 缺少类型')

        # 验证特定类型的几何元素
        element_type = element.get('type')
        if element_type == 'circle':
            center = element.get('center', {})
            if not center or not isinstance(center, dict):
                errors.append(f'圆形元素 {i} 无效: 缺少中心点')
            else:
                if not isinstance(center.get('x'), (int, float)):
                    errors.append(f'圆形元素 {i} 无效: 中心点X坐标不是数字')
                if not isinstance(center.get('y'), (int, float)):
                    errors.append(f'圆形元素 {i} 无效: 中心点Y坐标不是数字')
            if isinstance(element.get('radius'), (int, float)) and element['radius'] <= 0:
                errors.append(f'圆形元素 {i} 无效: 半径必须大于0')
        elif element_type == 'line':
            start = element.get('start', {})
            if not start or not isinstance(start, dict):
                errors.append(f'线元素 {i} 无效: 缺少起点')
            else:
                if not isinstance(start.get('x'), (int, float)):
                    errors.append(f'线元素 {i} 无效: 起点X坐标不是数字')
                if not isinstance(start.get('y'), (int, float)):
                    errors.append(f'线元素 {i} 无效: 起点Y坐标不是数字')
            end = element.get('end', {})
            if not end or not isinstance(end, dict):
                errors.append(f'线元素 {i} 无效: 缺少终点')
            else:
                if not isinstance(end.get('x'), (int, float)):
                    errors.append(f'线元素 {i} 无效: 终点X坐标不是数字')
                if not isinstance(end.get('y'), (int, float)):
                    errors.append(f'线元素 {i} 无效: 终点Y坐标不是数字')
        elif element_type == 'rectangle':
            if isinstance(element.get('width'), (int, float)) and element['width'] <= 0:
                errors.append(f'矩形元素 {i} 无效: 宽度必须大于0')
            if isinstance(element.get('height'), (int, float)) and element['height'] <= 0:
                errors.append(f'矩形元素 {i} 无效: 高度必须大于0')
        elif element_type == 'thread':
            if isinstance(element.get('diameter'), (int, float)) and element['diameter'] <= 0:
                errors.append(f'螺纹元素 {i} 无效: 直径必须大于0')
            if isinstance(element.get('pitch'), (int, float)) and element['pitch'] <= 0:
                errors.append(f'螺纹元素 {i} 无效: 螺距必须大于0')
        else:
            if element_type:  # 只有当类型存在时才添加警告
                warnings.append(f'未知的几何元素类型: {element_type}')

    return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}


def validate_machining_parameters(features: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    验证加工参数的合理性
    
    Args:
        features: 特征列表
        
    Returns:
        验证结果
    """
    if not isinstance(features, list):
        return {'valid': False, 'errors': ['特征列表必须是列表']}

    errors = []
    warnings = []

    for i, feature in enumerate(features):
        if not feature or not isinstance(feature, dict):
            continue

        # 检查加工参数是否合理
        params = feature.get('parameters', {})

        # 检查进给率
        feed_rate = params.get('feed_rate')
        if isinstance(feed_rate, (int, float)):
            if feed_rate <= 0:
                errors.append(f'特征 {i} 的进给率必须大于0')
            elif feed_rate > 2000:
                warnings.append(f'特征 {i} 的进给率({feed_rate})可能过高')

        # 检查主轴转速
        spindle_speed = params.get('spindle_speed')
        if isinstance(spindle_speed, (int, float)):
            if spindle_speed <= 0:
                errors.append(f'特征 {i} 的主轴转速必须大于0')
            elif spindle_speed > 10000:
                warnings.append(f'特征 {i} 的主轴转速({spindle_speed})可能过高')

        # 检查深度参数
        depth = params.get('depth')
        if isinstance(depth, (int, float)) and depth <= 0:
            errors.append(f'特征 {i} 的深度必须大于0')

    return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}


def validate_gcode_syntax(gcode_lines: List[str]) -> Dict[str, Any]:
    """
    验证G代码语法
    
    Args:
        gcode_lines: G代码行列表
        
    Returns:
        验证结果
    """
    if not isinstance(gcode_lines, list):
        return {'valid': False, 'errors': ['G代码行必须是列表']}

    errors = []
    warnings = []
    g_codes: Set[str] = set()
    m_codes: Set[str] = set()

    # 预编译正则表达式以提高性能
    g_pattern = re.compile(r'G(\d+\.?\d*)', re.IGNORECASE)
    m_pattern = re.compile(r'M(\d+\.?\d*)', re.IGNORECASE)
    g_start_pattern = re.compile(r'^G\d+(\.\d+)?', re.IGNORECASE)
    m_start_pattern = re.compile(r'^M\d+(\.\d+)?', re.IGNORECASE)

    for i, line in enumerate(gcode_lines):
        if not isinstance(line, str):
            continue

        # 提取G代码和M代码
        g_matches = g_pattern.findall(line)
        for g in g_matches:
            g_codes.add(f'G{g}'.upper())

        m_matches = m_pattern.findall(line)
        for m in m_matches:
            m_codes.add(f'M{m}'.upper())

        # 检查语法错误
        upper_line = line.upper()
        if upper_line.lstrip().startswith('G'):
            if not g_start_pattern.match(line.lstrip()):
                warnings.append(f'G代码行 {i}: G代码格式可能不正确 - "{line}"')

        if upper_line.lstrip().startswith('M'):
            if not m_start_pattern.match(line.lstrip()):
                warnings.append(f'G代码行 {i}: M代码格式可能不正确 - "{line}"')

        # 检查常见的错误模式
        if 'G0' in upper_line and 'F' in upper_line:
            warnings.append(f'G代码行 {i}: G00快速移动不应包含进给率F - "{line}"')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'g_codes': list(g_codes),
        'm_codes': list(m_codes)
    }


def validate_gcode_safety(gcode_lines: List[str]) -> Dict[str, Any]:
    """
    验证G代码的运动安全性和逻辑性
    
    Args:
        gcode_lines: G代码行列表
        
    Returns:
        验证结果
    """
    if not isinstance(gcode_lines, list):
        return {'valid': False, 'errors': ['G代码行必须是列表']}

    errors = []
    warnings = []
    current_x, current_y, current_z = 0.0, 0.0, 0.0
    current_feed_rate = 0.0
    is_rapid_move = False
    is_modal_gcode = {}

    for i, original_line in enumerate(gcode_lines):
        line = original_line.upper().strip()
        if not line or line.startswith(';'):  # 跳过注释行
            continue

        # 解析坐标值
        x_match = re.search(r'X\s*(-?\d+\.?\d*)', line)
        y_match = re.search(r'Y\s*(-?\d+\.?\d*)', line)
        z_match = re.search(r'Z\s*(-?\d+\.?\d*)', line)
        f_match = re.search(r'F\s*(\d+\.?\d*)', line)

        # 检查G代码
        g_matches = re.findall(r'G\s*(\d+\.?\d*)', line)
        for g in g_matches:
            g_num = float(g)
            if g_num == 0:  # 快速移动
                is_rapid_move = True
            elif g_num == 1:  # 直线插补
                is_rapid_move = False
            elif g_num in [2, 3]:  # 顺时针/逆时针圆弧插补
                is_rapid_move = False
            elif g_num in [17, 18, 19]:  # 平面选择
                pass
            elif g_num == 20:  # 英制单位
                warnings.append(f'G代码行 {i}: 使用英制单位可能与系统设置冲突')
            elif g_num == 21:  # 公制单位
                # 这是推荐的单位
                pass
            elif g_num == 90:  # 绝对坐标
                is_modal_gcode['absolute'] = True
            elif g_num == 91:  # 增量坐标
                is_modal_gcode['absolute'] = False

        # 检查坐标值的合理性
        if x_match:
            x_val = float(x_match.group(1))
            if abs(x_val) > 1000:  # 假设最大工作范围为1000mm
                errors.append(f'G代码行 {i}: X坐标值{x_val}超出安全范围')
            else:
                current_x = x_val
        if y_match:
            y_val = float(y_match.group(1))
            if abs(y_val) > 1000:
                errors.append(f'G代码行 {i}: Y坐标值{y_val}超出安全范围')
            else:
                current_y = y_val
        if z_match:
            z_val = float(z_match.group(1))
            if z_val > 200 or z_val < -200:  # 假设Z轴范围为-200到200mm
                errors.append(f'G代码行 {i}: Z坐标值{z_val}超出安全范围')
            else:
                current_z = z_val

        # 检查进给率
        if f_match:
            f_val = float(f_match.group(1))
            if f_val <= 0:
                errors.append(f'G代码行 {i}: 进给率F必须大于0')
            elif f_val > 5000:
                warnings.append(f'G代码行 {i}: 进给率F{f_val}可能过高')
            else:
                current_feed_rate = f_val

        # 检查非移动G代码后直接移动的情况
        if 'M03' in line and i < len(gcode_lines) - 1:
            # 检查主轴启动后是否合理设置了参数
            if current_feed_rate == 0:
                warnings.append(f'G代码行 {i}: 主轴启动后应设置合适的进给率')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'final_position': {'x': current_x, 'y': current_y, 'z': current_z}
    }


def detect_collisions(gcode_lines: List[str], workpiece_dimensions: Dict[str, float] = None, tool_diameter: float = 6) -> Dict[str, Any]:
    """
    碰撞检测算法
    
    Args:
        gcode_lines: G代码行列表
        workpiece_dimensions: 工件尺寸
        tool_diameter: 刀具直径
        
    Returns:
        碰撞检测结果
    """
    if workpiece_dimensions is None:
        workpiece_dimensions = {'x': 200, 'y': 200, 'z': 100}
    
    if not isinstance(gcode_lines, list):
        return {'has_collisions': True, 'errors': ['G代码行必须是列表']}

    collisions = []
    current_x, current_y, current_z = 0.0, 0.0, 0.0  # 当前工具位置
    previous_x, previous_y, previous_z = 0.0, 0.0, 0.0  # 前一位置
    is_rapid_move = False  # 是否为快速移动
    is_cutting = False  # 是否在切削

    # 工件边界
    workpiece_bounds = {
        'min_x': -workpiece_dimensions['x'] / 2,
        'max_x': workpiece_dimensions['x'] / 2,
        'min_y': -workpiece_dimensions['y'] / 2,
        'max_y': workpiece_dimensions['y'] / 2,
        'min_z': 0,  # 假设工件顶部为Z=0
        'max_z': workpiece_dimensions['z']
    }

    # 刀具半径
    tool_radius = tool_diameter / 2

    for i, original_line in enumerate(gcode_lines):
        line = original_line.upper().strip()
        if not line or line.startswith(';'):  # 跳过注释行
            continue

        # 保存当前位置作为前一位置
        previous_x, previous_y, previous_z = current_x, current_y, current_z

        # 检查G代码
        g_matches = re.findall(r'G\s*(\d+\.?\d*)', line)
        for g in g_matches:
            g_num = float(g)
            if g_num == 0:  # 快速移动
                is_rapid_move = True
                is_cutting = False
            elif g_num in [1, 2, 3]:  # 直线插补或圆弧插补
                is_rapid_move = False
                is_cutting = True

        # 解析坐标值
        x_match = re.search(r'X\s*(-?\d+\.?\d*)', line)
        y_match = re.search(r'Y\s*(-?\d+\.?\d*)', line)
        z_match = re.search(r'Z\s*(-?\d+\.?\d*)', line)

        if x_match:
            current_x = float(x_match.group(1))
        if y_match:
            current_y = float(y_match.group(1))
        if z_match:
            current_z = float(z_match.group(1))

        # 检查是否在工件边界内
        if is_cutting:
            # 检查当前位置是否在工件边界内
            if (current_x < workpiece_bounds['min_x'] or current_x > workpiece_bounds['max_x'] or
                current_y < workpiece_bounds['min_y'] or current_y > workpiece_bounds['max_y'] or
                current_z < workpiece_bounds['min_z'] - tool_radius or current_z > workpiece_bounds['max_z'] + tool_radius):
                collisions.append({
                    'type': 'boundary_violation',
                    'description': f'在G代码行 {i}，刀具位置 ({current_x}, {current_y}, {current_z}) 超出工件边界',
                    'line': i,
                    'position': {'x': current_x, 'y': current_y, 'z': current_z}
                })

            # 检查快速移动时的安全高度
            if is_rapid_move and current_z < workpiece_bounds['max_z'] - 5:  # 假设安全高度为工件顶部上方5mm
                collisions.append({
                    'type': 'rapid_move_collision',
                    'description': f'在G代码行 {i}，快速移动高度({current_z})过低，可能与工件碰撞',
                    'line': i,
                    'position': {'x': current_x, 'y': current_y, 'z': current_z}
                })

            # 检查刀具与工件的潜在碰撞
            # 通过检查移动路径是否穿过工件内部
            if is_rapid_move:
                # 对于快速移动，检查路径是否穿过工件
                path_check = check_path_collision(
                    previous_x, previous_y, previous_z,
                    current_x, current_y, current_z,
                    workpiece_bounds, tool_radius
                )
                if path_check['collision']:
                    collisions.append({
                        'type': 'rapid_path_collision',
                        'description': f'在G代码行 {i}，快速移动路径从({previous_x}, {previous_y}, {previous_z})到({current_x}, {current_y}, {current_z})可能与工件碰撞',
                        'line': i,
                        'start': {'x': previous_x, 'y': previous_y, 'z': previous_z},
                        'end': {'x': current_x, 'y': current_y, 'z': current_z}
                    })

        # 检查Z轴极限位置
        if current_z < -50:  # 假设Z轴下限为-50mm
            collisions.append({
                'type': 'z_limit_exceeded',
                'description': f'在G代码行 {i}，Z轴位置({current_z})超出下限，可能导致刀具与工作台碰撞',
                'line': i,
                'position': {'x': current_x, 'y': current_y, 'z': current_z}
            })

        # 检查是否在安全起始位置
        if i == 0 and is_cutting and current_z > -5:  # 如果第一个指令就是切削且不在安全高度
            collisions.append({
                'type': 'unsafe_start',
                'description': f'在G代码行 {i}，起始位置({current_x}, {current_y}, {current_z})不安全，应先移动到安全高度再开始切削',
                'line': i,
                'position': {'x': current_x, 'y': current_y, 'z': current_z}
            })

    return {
        'has_collisions': len(collisions) > 0,
        'collisions': collisions,
        'workpiece_bounds': workpiece_bounds,
        'tool_radius': tool_radius
    }


def check_path_collision(start_x: float, start_y: float, start_z: float,
                        end_x: float, end_y: float, end_z: float,
                        workpiece_bounds: Dict[str, float], tool_radius: float) -> Dict[str, bool]:
    """
    辅助函数：检查移动路径是否与工件碰撞
    
    Args:
        start_x, start_y, start_z: 起始位置
        end_x, end_y, end_z: 结束位置
        workpiece_bounds: 工件边界
        tool_radius: 刀具半径
        
    Returns:
        碰撞检测结果
    """
    # 简化的路径碰撞检测
    # 这里使用线性插值检查路径上的几个点
    steps = 10  # 将路径分为10个点进行检查
    for i in range(1, steps + 1):
        t = i / steps
        x = start_x + (end_x - start_x) * t
        y = start_y + (end_y - start_y) * t
        z = start_z + (end_z - start_z) * t

        # 检查该点是否在工件内部（考虑刀具半径）
        if (x >= workpiece_bounds['min_x'] - tool_radius and x <= workpiece_bounds['max_x'] + tool_radius and
            y >= workpiece_bounds['min_y'] - tool_radius and y <= workpiece_bounds['max_y'] + tool_radius and
            z >= workpiece_bounds['min_z'] - tool_radius and z <= workpiece_bounds['max_z'] + tool_radius):
            return {'collision': True, 'point': {'x': x, 'y': y, 'z': z}}

    return {'collision': False}


if __name__ == "__main__":
    # 测试代码
    test_gcode = [
        "G21 (毫米编程)",
        "G40 (刀具半径补偿取消)",
        "G49 (刀具长度补偿取消)",
        "G80 (取消固定循环)",
        "G90 (绝对编程)",
        "G54 (工件坐标系1)",
        "G0 X0. Y0. S500 M03 (主轴正转，500转/分钟)",
        "G0 X10 Y10",
        "G1 Z-5 F100",
        "G1 X20 Y20",
        "G0 Z100",
        "M05 (主轴停止)",
        "M30 (程序结束)"
    ]
    
    print("G代码语法验证:", validate_gcode_syntax(test_gcode))
    print("G代码安全验证:", validate_gcode_safety(test_gcode))
    print("碰撞检测:", detect_collisions(test_gcode))
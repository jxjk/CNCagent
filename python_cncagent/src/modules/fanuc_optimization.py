"""
FANUC NC程序优化模块
实现FANUC标准的NC程序优化功能，包括简化编程格式、进给计算优化等
"""
from typing import List, Dict


def optimize_drilling_cycle(hole_positions: List[tuple], drilling_depth: float, feed_rate: float = 100) -> List[str]:
    """
    优化钻孔循环，使用简化编程格式提高效率
    
    Args:
        hole_positions: 孔位置列表 [(x1, y1), (x2, y2), ...]
        drilling_depth: 钻孔深度
        feed_rate: 进给率
    
    Returns:
        优化的G代码列表
    """
    gcode = []
    
    if not hole_positions:
        return gcode
    
    # 第一个孔使用完整G代码
    first_x, first_y = hole_positions[0]
    gcode.append(f"G83 X{first_x:.3f} Y{first_y:.3f} Z{-drilling_depth} R2 Q1 F{feed_rate} (DEEP HOLE DRILLING CYCLE)")
    
    # 后续孔仅使用X、Y坐标（简化编程格式）
    for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
        gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (DRILLING {i}: X{center_x:.1f},Y{center_y:.1f})")
    
    return gcode


def optimize_tapping_cycle(hole_positions: List[tuple], tapping_depth: float, spindle_speed: float, thread_type: str) -> List[str]:
    """
    优化攻丝循环，使用简化编程格式并确保F=S*螺距的正确计算
    
    Args:
        hole_positions: 孔位置列表 [(x1, y1), (x2, y2), ...]
        tapping_depth: 攻丝深度
        spindle_speed: 主轴转速
        thread_type: 螺纹类型 (如 "M10", "M6" 等)
    
    Returns:
        优化的G代码列表
    """
    gcode = []
    
    if not hole_positions:
        return gcode
    
    # 根据螺纹类型确定螺距
    thread_pitch = get_thread_pitch(thread_type)
    
    # 计算攻丝进给 F = S * 螺距
    tapping_feed = spindle_speed * thread_pitch
    # 确保进给率不低于1
    tapping_feed = max(tapping_feed, 1.0)
    
    # 第一个孔使用完整G代码
    first_x, first_y = hole_positions[0]
    gcode.append(f"G84 X{first_x:.3f} Y{first_y:.3f} Z{-tapping_depth} R2 F{tapping_feed:.1f} (TAPPING 1: X{first_x:.1f},Y{first_y:.1f} - {thread_type} THREAD)")
    
    # 后续孔仅使用X、Y坐标（简化编程格式）
    for i, (center_x, center_y) in enumerate(hole_positions[1:], 2):
        gcode.append(f"X{center_x:.3f} Y{center_y:.3f} (TAPPING {i}: X{center_x:.1f},Y{center_y:.1f} - {thread_type} THREAD)")
    
    return gcode


def get_thread_pitch(thread_type: str) -> float:
    """
    根据螺纹类型获取标准螺距
    
    Args:
        thread_type: 螺纹类型 (如 "M10", "M6" 等)
    
    Returns:
        螺距值（mm）
    """
    thread_pitch_map = {
        "M3": 0.5,
        "M4": 0.7,
        "M5": 0.8,
        "M6": 1.0,
        "M8": 1.25,
        "M10": 1.5,
        "M12": 1.75
    }
    
    # 提取螺纹规格（如"M10"中的"10"）
    if thread_type.startswith("M"):
        try:
            size = thread_type[1:]  # 获取M后面的数字
            if size in ["3", "4", "5", "6", "8", "10", "12"]:
                return thread_pitch_map.get(f"M{size}", 1.5)  # 默认M10螺距
            else:
                # 对于其他M系列螺纹，按比例估算
                size_num = int(size)
                if size_num < 5:
                    return 0.5  # 小螺纹螺距较小
                elif size_num < 10:
                    return 1.0  # 中等螺纹螺距中等
                else:
                    return 1.5  # 大螺纹螺距较大
        except ValueError:
            return 1.5  # 无法解析时使用默认值
    else:
        return 1.5  # 非标准格式使用默认值


def optimize_milling_path(features: List[Dict], depth: float, feed_rate: float) -> List[str]:
    """
    优化铣削路径，提高加工效率
    
    Args:
        features: 特征列表
        depth: 铣削深度
        feed_rate: 进给率
    
    Returns:
        优化的G代码列表
    """
    gcode = []
    
    for feature in features:
        gcode.append("")
        gcode.append(f"(MILLING OPERATION - {feature['shape'].upper()})")
        
        if feature["shape"] == "circle":
            # 圆形铣削 - 使用圆弧插补
            center_x, center_y = feature["center"]
            radius = feature.get("radius", 10)
            
            # 快速移动到圆的起始点
            start_x = center_x - radius
            gcode.append(f"G00 X{start_x:.3f} Y{center_y:.3f} (MOVE TO CIRCULAR ARC START POINT)")
            gcode.append(f"G01 Z{-depth/2:.3f} F{feed_rate/2} (INITIAL CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
            # 如果需要更深的加工，进行第二次切削
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} (CONTINUE CUTTING)")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} (CLOCKWISE CIRCULAR MILLING)")
            
        elif feature["shape"] in ["rectangle", "square"]:
            # 矩形铣削
            center_x, center_y = feature["center"]
            length, width = feature["dimensions"]
            
            half_length = length / 2
            half_width = width / 2
            
            # 移动到矩形起点
            start_x = center_x - half_length
            start_y = center_y - half_width
            gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO RECTANGLE START POINT)")
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} (INITIAL CUTTING)")
            
            # 铣削矩形轮廓
            gcode.append(f"G01 X{start_x + length:.3f} F{feed_rate} (MILL X DIRECTION EDGE)")
            gcode.append(f"G01 Y{start_y + width:.3f} (MILL Y DIRECTION EDGE)")
            gcode.append(f"G01 X{start_x:.3f} (MILL X DIRECTION EDGE)")
            gcode.append(f"G01 Y{start_y:.3f} (MILL Y DIRECTION EDGE)")
            
        elif feature["shape"] == "triangle":
            # 三角形铣削
            vertices = feature.get("vertices", [])
            if len(vertices) >= 3:
                start_x, start_y = vertices[0]
                gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} (MOVE TO TRIANGLE START POINT)")
                gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} (INITIAL CUTTING)")
                
                for i in range(1, len(vertices)):
                    x, y = vertices[i]
                    gcode.append(f"G01 X{x:.3f} Y{y:.3f} F{feed_rate} (MILL TRIANGLE EDGE)")
                
                # 闭合三角形
                x, y = vertices[0]
                gcode.append(f"G01 X{x:.3f} Y{y:.3f} (CLOSE TRIANGLE)")
    
    return gcode


def add_fanuc_comments(gcode_lines: List[str], operation_type: str) -> List[str]:
    """
    为G代码添加符合FANUC标准的注释
    
    Args:
        gcode_lines: G代码行列表
        operation_type: 操作类型
    
    Returns:
        带注释的G代码行列表
    """
    enhanced_gcode = []
    
    # 添加操作类型注释
    enhanced_gcode.append(f"({operation_type})")
    
    for line in gcode_lines:
        enhanced_gcode.append(line)
    
    return enhanced_gcode
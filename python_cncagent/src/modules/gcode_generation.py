"""
FANUC NC程序生成模块
根据识别的特征和用户描述生成符合FANUC标准的G代码
"""
from typing import List, Dict
import math


def generate_fanuc_nc(features: List[Dict], description_analysis: Dict, scale: float = 1.0) -> str:
    """
    根据识别特征和用户描述生成FANUC NC程序
    
    Args:
        features (list): 识别出的几何特征列表
        description_analysis (dict): 用户描述分析结果
        scale (float): 比例尺因子
    
    Returns:
        str: 生成的NC程序代码
    """
    gcode = []
    
    # 添加程序头
    gcode.append("O0001 ; 程序号")
    gcode.append("G21 ; 毫米单位")
    gcode.append("G90 ; 绝对坐标")
    gcode.append("G40 ; 取消刀具半径补偿")
    gcode.append("G49 ; 取消刀具长度补偿")
    gcode.append("G80 ; 取消固定循环")
    gcode.append("")
    
    # 设置初始安全高度
    gcode.append("G00 Z50 ; 快速移动到安全高度")
    
    # 根据加工类型设置主轴和进给
    processing_type = description_analysis.get("processing_type", "general")
    tool_required = description_analysis.get("tool_required", "general_tool")
    
    # 选择刀具
    tool_number = _get_tool_number(tool_required)
    gcode.append(f"T{tool_number} M06 ; 选择刀具T{tool_number}")
    
    # 设置主轴转速 - 安全处理None值
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
        spindle_speed = 1000  # 默认值
    else:
        spindle_speed = float(spindle_speed)
    
    gcode.append(f"M03 S{int(spindle_speed)} ; 主轴正转，速度{int(spindle_speed)} RPM")
    gcode.append("G04 P1000 ; 延时1秒，等待主轴达到设定转速")
    gcode.append("")
    
    # 根据加工类型生成G代码
    if processing_type == "drilling":
        gcode.extend(_generate_drilling_code(features, description_analysis))
    elif processing_type == "milling":
        gcode.extend(_generate_milling_code(features, description_analysis))
    elif processing_type == "turning":
        gcode.extend(_generate_turning_code(features, description_analysis))
    else:
        # 默认使用铣削代码
        gcode.extend(_generate_milling_code(features, description_analysis))
    
    # 添加程序结束
    gcode.append("")
    gcode.append("M05 ; 主轴停止")
    gcode.append("G00 Z100 ; 抬刀到安全高度")
    gcode.append("G00 X0 Y0 ; 返回原点")
    gcode.append("M30 ; 程序结束")
    
    return "\n".join(gcode)


def _get_tool_number(tool_type: str) -> int:
    """根据刀具类型返回刀具编号"""
    tool_mapping = {
        "drill_bit": 1,
        "end_mill": 2,
        "cutting_tool": 3,
        "grinding_wheel": 4,
        "general_tool": 5
    }
    
    return tool_mapping.get(tool_type, 5)


def _generate_drilling_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成钻孔加工代码"""
    gcode = []
    
    # 设置钻孔循环参数 - 安全处理None值
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 10  # 默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = 100  # 默认值
    else:
        feed_rate = float(feed_rate)
    
    gcode.append(f"G99 G83 Z{-depth} R2 F{feed_rate} ; 深孔钻循环")
    
    # 为每个圆形特征生成钻孔点
    for feature in features:
        if feature["shape"] in ["circle", "square", "rectangle"]:
            center_x, center_y = feature["center"]
            gcode.append(f"G83 X{center_x:.3f} Y{center_y:.3f} Z{-depth} R2 F{feed_rate} ; 钻孔")
    
    gcode.append("G80 ; 取消固定循环")
    return gcode


def _generate_milling_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成铣削加工代码"""
    gcode = []
    
    # 设置铣削参数 - 安全处理None值
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 5  # 默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = 200  # 默认值
    else:
        feed_rate = float(feed_rate)
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
        spindle_speed = 1000  # 默认值
    else:
        spindle_speed = float(spindle_speed)
    
    # 为每个特征生成铣削代码
    for feature in features:
        gcode.append("")
        gcode.append(f"; 加工{feature['shape']}")
        
        if feature["shape"] == "circle":
            # 圆形铣削
            center_x, center_y = feature["center"]
            radius = feature.get("radius", 10)
            
            # 快速移动到圆的起始点
            start_x = center_x - radius
            gcode.append(f"G00 X{start_x:.3f} Y{center_y:.3f} ; 移动到圆弧起点")
            gcode.append(f"G01 Z{-depth/2:.3f} F{feed_rate/2} ; 下刀")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} ; 顺时针铣圆")
            
            # 如果需要更深的加工，进行第二次切削
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} ; 继续下刀")
            gcode.append(f"G02 X{start_x:.3f} Y{center_y:.3f} I{radius:.3f} J0 F{feed_rate} ; 顺时针铣圆")
            
        elif feature["shape"] in ["rectangle", "square"]:
            # 矩形铣削
            center_x, center_y = feature["center"]
            length, width = feature["dimensions"]
            
            half_length = length / 2
            half_width = width / 2
            
            # 移动到矩形起点
            start_x = center_x - half_length
            start_y = center_y - half_width
            gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} ; 移动到矩形起点")
            gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} ; 下刀")
            
            # 铣削矩形轮廓
            gcode.append(f"G01 X{start_x + length:.3f} F{feed_rate} ; 铣X方向边")
            gcode.append(f"G01 Y{start_y + width:.3f} ; 铣Y方向边")
            gcode.append(f"G01 X{start_x:.3f} ; 铣X方向边")
            gcode.append(f"G01 Y{start_y:.3f} ; 铣Y方向边")
            
        elif feature["shape"] == "triangle":
            # 三角形铣削
            vertices = feature.get("vertices", [])
            if len(vertices) >= 3:
                start_x, start_y = vertices[0]
                gcode.append(f"G00 X{start_x:.3f} Y{start_y:.3f} ; 移动到三角形起点")
                gcode.append(f"G01 Z{-depth:.3f} F{feed_rate/2} ; 下刀")
                
                for i in range(1, len(vertices)):
                    x, y = vertices[i]
                    gcode.append(f"G01 X{x:.3f} Y{y:.3f} F{feed_rate} ; 铣三角形边")
                
                # 闭合三角形
                x, y = vertices[0]
                gcode.append(f"G01 X{x:.3f} Y{y:.3f} ; 闭合三角形")
    
    return gcode


def _generate_turning_code(features: List[Dict], description_analysis: Dict) -> List[str]:
    """生成车削加工代码"""
    gcode = []
    
    # 设置车削参数 - 安全处理None值
    depth = description_analysis.get("depth")
    if depth is None or not isinstance(depth, (int, float)):
        depth = 2  # 默认值
    else:
        depth = float(depth)
    
    feed_rate = description_analysis.get("feed_rate")
    if feed_rate is None or not isinstance(feed_rate, (int, float)):
        feed_rate = 100  # 默认值
    else:
        feed_rate = float(feed_rate)
    
    spindle_speed = description_analysis.get("spindle_speed")
    if spindle_speed is None or not isinstance(spindle_speed, (int, float)):
        spindle_speed = 800  # 默认值
    else:
        spindle_speed = float(spindle_speed)
    
    gcode.append(f"M03 S{int(spindle_speed)} ; 设置主轴转速")
    
    # 为每个特征生成车削代码
    for feature in features:
        gcode.append("")
        gcode.append(f"; 车削{feature['shape']}")
        
        if feature["shape"] in ["rectangle", "square"]:
            # 假设矩形表示需要车削的外径
            _, _, width, height = feature["bounding_box"]
            diameter = max(width, height)  # 假设最大尺寸为直径
            
            # 粗车循环 (G71)
            gcode.append(f"G71 U2 R1 ; 粗车循环，每次切深2mm")
            gcode.append(f"G71 P10 Q20 U{diameter/10:.3f} W0.5 F{feed_rate/2} ; 粗车外径")
            gcode.append("N10 G00 X0 Z0")
            gcode.append(f"N20 G01 X{diameter} Z0 F{feed_rate/2}")
            
            # 精车循环 (G70)
            gcode.append("G70 P10 Q20 ; 精车循环")
    
    return gcode


def validate_nc_code(nc_code: str) -> List[str]:
    """
    验证生成的NC代码的有效性
    
    Args:
        nc_code (str): 生成的NC代码
    
    Returns:
        list: 验证错误列表，如果无错误则返回空列表
    """
    errors = []
    lines = nc_code.split('\n')
    
    # 检查是否存在必要的G代码指令
    has_program_end = any('M30' in line or 'M02' in line for line in lines)
    if not has_program_end:
        errors.append("缺少程序结束指令 (M30 或 M02)")
    
    has_units = any('G21' in line or 'G20' in line for line in lines)
    if not has_units:
        errors.append("缺少单位设定指令 (G21 或 G20)")
    
    has_coordinate_mode = any('G90' in line or 'G91' in line for line in lines)
    if not has_coordinate_mode:
        errors.append("缺少坐标模式设定指令 (G90 或 G91)")
    
    return errors

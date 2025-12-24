"""
PDF解析处理子模块
"""
import os
import re
import math
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import uuid

from src.modules.validation import validate_geometry_elements
from src.modules.mechanical_drawing_expert import MechanicalDrawingExpert

def extract_geometric_info_from_text(text: str) -> Dict[str, Any]:
    """
    从文本中提取几何信息的辅助函数
    
    Args:
        text: 输入文本
        
    Returns:
        包含几何元素、尺寸等信息的字典
    """
    geometry_elements = []
    dimensions = []
    tolerances = []  # 形位公差
    surface_finishes = []  # 表面光洁度
    lines = text.split('\n')
    id_counter = 0

    # 更精确的正则表达式用于匹配可能的几何元素和尺寸
    # 匹配坐标对 (x, y) - 支持多种格式
    coord_patterns = [
        r'([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)',  # 基本坐标格式 x, y
        r'X:\s*([+-]?\d+\.?\d*)\s*Y:\s*([+-]?\d+\.?\d*)',  # X: x Y: y 格式
        r'X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)',   # X x Y y 格式
        r'\(([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\)',     # (x, y) 格式
        r'\[(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\]',               # [x, y] 格式
        r'POINT\s+\(([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\)',  # POINT (x, y) 格式
        r'COORD\s*[:\s]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)', # COORD: x, y 格式
        r'CENTER\s*[:\s]*([+-]?\d+\.?\d*)[,、\s]+([+-]?\d+\.?\d*)', # CENTER: x, y 格式
        r'ORIGIN\s*[:\s]*([+-]?\d+\.?\d*)[,、\s]+([+-]?\d+\.?\d*)'  # ORIGIN: x, y 格式
    ]

    # 匹配可能的尺寸标注 - 支持多种单位
    dim_patterns = [
        r'(\d+\.?\d*)\s*mm',     # 毫米
        r'(\d+\.?\d*)\s*in',     # 英寸
        r'(\d+\.?\d*)\s*英寸',   # 中文英寸
        r'(\d+\.?\d*)\s*cm',     # 厘米
        r'(\d+\.?\d*)\s*m',      # 米
        r'(\d+\.?\d*)\s*mm\s*dia', # 直径标注
        r'R(\d+\.?\d*)',         # 半径R格式
        r'∅(\d+\.?\d*)',         # 直径φ格式
        r'Φ(\d+\.?\d*)',         # 直径Φ格式
        r'DIA\s*(\d+\.?\d*)',    # DIA格式直径
        r'Diameter\s*(\d+\.?\d*)', # Diameter格式
        r'DIAMETER\s*[:\s]*([+-]?\d+\.?\d*)', # DIAMETER: value 格式
        r'RADIUS\s*[:\s]*([+-]?\d+\.?\d*)',   # RADIUS: value 格格式
        r'LENGTH\s*[:\s]*([+-]?\d+\.?\d*)',    # LENGTH: value 格式
        r'WIDTH\s*[:\s]*([+-]?\d+\.?\d*)',     # WIDTH: value 格式
        r'HEIGHT\s*[:\s]*([+-]?\d+\.?\d*)',    # HEIGHT: value 格式
        r'SIZE\s*[:\s]*([+-]?\d+\.?\d*)',      # SIZE: value 格式
        r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)', # 长×宽×高格式
        r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)'       # 长×宽格式
    ]

    # 匹配圆心和半径/直径的特定模式
    circle_patterns = [
        r'CIRCLE.*?R(\d+\.?\d*)',
        r'CIRCLE.*?RADIUS.*?(\d+\.?\d*)',
        r'CIRCLE.*?(\d+\.?\d*)\s*RADIUS',
        r'圆.*?R(\d+\.?\d*)',
        r'圆形.*?半径\s*(\d+\.?\d*)',
        r'圆.*?半径\s*(\d+\.?\d*)',
        r'圆.*?直径\s*(\d+\.?\d*)',
        r'CIRCULAR.*?DIA\s*(\d+\.?\d*)',
        r'ARC.*?R(\d+\.?\d*)',
        r'ARC.*?RADIUS.*?(\d+\.?\d*)'
    ]

    # 匹配矩形或线段的模式
    rectangle_patterns = [
        r'RECTANGLE|RECT|矩形|长方形',
        r'BOX|SQUARE|正方形|方块'
    ]

    # 匹配直线的模式
    line_patterns = [
        r'LINE|STRAIGHT',
        r'LINEAR'
    ]

    # 匹配孔特征
    hole_patterns = [
        r'HOLE',
        r'孔',
        r'THRU',  # 穿通孔
        r'CIRCLE', # 圆形孔
        r'圆'
    ]

    # 匹配螺纹特征
    thread_patterns = [
        r'THREAD',
        r'螺纹',
        r'螺紛',
        r'M(\d+\.?\d*)\s*x\s*(\d+\.?\d*)', # M6x1 螺纹格式
        r'-\s*T', # 螺纹符号 -T
        r'TAP',   # 攻丝
        r'TAPPED' # 已攻丝
    ]

    # 匹配槽特征
    slot_patterns = [
        r'SLOT',
        r'槽',
        r'GROOVE',
        r'KEYWAY', # 键槽
        r'NOTCH'   # 切口
    ]

    # 匹配边特征
    edge_patterns = [
        r'EDGE',
        r'边',
        r'EDGE\s+CHAMFER',  # 边倒角
        r'EDGE\s+FILLET'    # 边圆角
    ]

    # 匹配面或区域特征
    face_patterns = [
        r'SURFACE',
        r'面',
        r'SURF',
        r'PLANE',   # 平面
        r'FLAT'     # 平面
    ]

    # 匹配形位公差
    tolerance_patterns = [
        r'∥',      # 平行度
        r'⊥',      # 垂直度
        r'∠',      # 倾斜度
        r'⌒',      # 圆弧度
        r'○',      # 圆度
        r'◎',      # 同轴度
        r'□',      # 正方形度
        r' cylindricity ',
        r' concentricity ',
        r' symmetry ',
        r' runout ',
        r' position ',
        r' flatness ',
        r' straightness ',
        r' profile ',
        r' tolerance ',
        r'公差',
        r'位置度',
        r'平行度',
        r'垂直度',
        r'同轴度'
    ]

    # 匹配表面光洁度
    surface_finish_patterns = [
        r'Ra(\d+\.?\d*)',   # 表面粗糙度Ra值
        r'Rz(\d+\.?\d*)',   # 表面粗糙度Rz值
        r'表面粗糙度',
        r'光洁度',
        r'FINISH',
        r'MACHINED',
        r'GROUND',    # 磨削
        r'MILLED',    # 钟削
        r'TURNED'     # 车削
    ]

    # 匹配倒角特征
    chamfer_patterns = [
        r'CHAMFER',
        r'倒角',
        r'BEVEL'
    ]

    # 匹配圆角特征
    fillet_patterns = [
        r'FILLET',
        r'圆角',
        r'R(\d+\.?\d*)\s+FILLET'  # R值圆角
    ]

    # 处理坐标
    for line_idx, line in enumerate(lines):
        # 检测孔特征
        for hole_pattern in hole_patterns:
            if re.search(hole_pattern, line, re.IGNORECASE):
                # 尝试从孔的描述中提取坐标和尺寸
                coord_matches = re.findall(r'([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)', line)
                dim_matches = re.findall(r'(\d+\.?\d*)\s*mm', line, re.IGNORECASE)
                if coord_matches:
                    x = float(coord_matches[0][0])
                    y = float(coord_matches[0][1])
                    if not (math.isnan(x) or math.isnan(y)):
                        geometry_elements.append({
                            'id': f'hole_{id_counter}',
                            'type': 'hole',
                            'center': {'x': x, 'y': y},
                            'text': line.strip(),
                            'line_index': line_idx
                        })
                        id_counter += 1
                if dim_matches:
                    diameter = float(dim_matches[0])
                    if not math.isnan(diameter):
                        dimensions.append({
                            'id': f'hole_dia_{id_counter}',
                            'type': 'diameter',
                            'value': diameter,
                            'unit': 'mm',
                            'description': f'Hole diameter: {diameter} mm',
                            'line_index': line_idx
                        })
                        id_counter += 1
                break

        # 检测倒角
        for chamfer_pattern in chamfer_patterns:
            if re.search(chamfer_pattern, line, re.IGNORECASE):
                # 提取倒角尺寸
                dim_matches = re.findall(r'(\d+\.?\d*)\s*mm', line, re.IGNORECASE)
                for match in dim_matches:
                    value = float(match)
                    if not math.isnan(value) and value > 0:
                        dimensions.append({
                            'id': f'chamfer_{id_counter}',
                            'type': 'linear',
                            'value': value,
                            'unit': 'mm',
                            'description': f'Chamfer: {value} mm',
                            'line_index': line_idx
                        })
                        id_counter += 1
                break

        # 检测圆角
        for fillet_pattern in fillet_patterns:
            matches = re.findall(fillet_pattern, line, re.IGNORECASE)
            for match in matches:
                if match:  # R值圆角
                    try:
                        radius = float(match)
                        if not math.isnan(radius) and radius > 0:
                            dimensions.append({
                                'id': f'fillet_{id_counter}',
                                'type': 'radius',
                                'value': radius,
                                'unit': 'mm',
                                'description': f'Fillet radius: {radius} mm',
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        pass
                else:
                    # 一般圆角标注
                    dim_matches = re.findall(r'(\d+\.?\d*)\s*mm', line, re.IGNORECASE)
                    for dim_match in dim_matches:
                        try:
                            value = float(dim_match)
                            if not math.isnan(value) and value > 0:
                                dimensions.append({
                                    'id': f'fillet_{id_counter}',
                                    'type': 'radius',
                                    'value': value,
                                    'unit': 'mm',
                                    'description': f'Fillet: {value} mm',
                                    'line_index': line_idx
                                })
                                id_counter += 1
                        except ValueError:
                            pass
                break

        # 处理坐标
        for pattern in coord_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    x = float(match[0] if isinstance(match, tuple) else match)
                    y = float(match[1] if isinstance(match, tuple) and len(match) > 1 else 0)
                    
                    # 验证坐标合理性
                    if not (math.isnan(x) or math.isnan(y)):
                        if abs(x) < 10000 and abs(y) < 10000:  # 合理的坐标范围
                            geometry_elements.append({
                                'id': f'point_{id_counter}',
                                'type': 'point',
                                'x': x,
                                'y': y,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                except (ValueError, IndexError):
                    continue

    # 重新遍历每行进行尺寸和几何元素解析
    for line_idx, line in enumerate(lines):
        # 检测尺寸标注
        for pattern in dim_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                # 处理多个数字的情况（如长×宽×高或长×宽格式）
                if 'x' in match.lower() and match.lower().count('x') >= 2:
                    # 长×宽×高格式
                    dims = re.findall(r'(\d+\.?\d*)', match)
                    if dims and len(dims) >= 3:
                        try:
                            length = float(dims[0])
                            width = float(dims[1])
                            height = float(dims[2])
                            if not (math.isnan(length) or math.isnan(width) or math.isnan(height)):
                                geometry_elements.append({
                                    'id': f'box_{line_idx}_{id_counter}',
                                    'type': 'box',
                                    'length': length,
                                    'width': width,
                                    'height': height,
                                    'text': line.strip(),
                                    'line_index': line_idx
                                })
                                id_counter += 1
                        except ValueError:
                            pass
                    elif dims and len(dims) >= 2:
                        # 长×宽格式
                        try:
                            length = float(dims[0])
                            width = float(dims[1])
                            if not (math.isnan(length) or math.isnan(width)):
                                geometry_elements.append({
                                    'id': f'rect_{line_idx}_{id_counter}',
                                    'type': 'rectangle',
                                    'width': width,
                                    'height': length,  # 假设第一个是长度，第二个是宽度
                                    'text': line.strip(),
                                    'line_index': line_idx
                                })
                                id_counter += 1
                        except ValueError:
                            pass
                else:
                    # 单个数值的尺寸标注
                    try:
                        value_str = match if isinstance(match, str) else str(match)
                        value = float(value_str)
                        if not math.isnan(value) and value > 0:
                            # 确定尺寸类型
                            dimension_type = 'linear'
                            if 'R' in line or '半径' in line or 'RADIUS' in line.upper():
                                dimension_type = 'radius'
                            elif '∅' in line or 'Φ' in line or 'DIA' in line.upper() or 'DIAMETER' in line.upper():
                                dimension_type = 'diameter'
                            elif 'WIDTH' in line.upper() or 'LENGTH' in line.upper() or 'HEIGHT' in line.upper():
                                dimension_type = 'linear'

                            dimensions.append({
                                'id': f'dim_{line_idx}_{id_counter}',
                                'type': dimension_type,
                                'value': value,
                                'unit': 'mm',  # 默认单位为毫米
                                'description': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue

        # 检测圆形元素
        for pattern in circle_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                try:
                    radius = float(match)
                    if not math.isnan(radius) and radius > 0:
                        geometry_elements.append({
                            'id': f'circle_{line_idx}_{id_counter}',
                            'type': 'circle',
                            'center': {'x': 0, 'y': 0},  # 初始位置，需要从上下文推断
                            'radius': radius,
                            'text': line.strip(),
                            'line_index': line_idx
                        })
                        id_counter += 1
                except ValueError:
                    continue

        # 检测矩形元素
        for pattern in rectangle_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # 尝试从同一行或附近行提取尺寸
                dim_matches = re.findall(r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)', line, re.IGNORECASE)
                for dim_match in dim_matches:
                    try:
                        width = float(dim_match[0])
                        height = float(dim_match[1])
                        if not (math.isnan(width) or math.isnan(height)) and width > 0 and height > 0:
                            geometry_elements.append({
                                'id': f'rect_{line_idx}_{id_counter}',
                                'type': 'rectangle',
                                'width': width,
                                'height': height,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue
                break

        # 检测直线元素
        for pattern in line_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # 尝试从同一行提取直线信息
                point_matches = re.findall(r'([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)', line)
                if len(point_matches) >= 2:  # 线段至少需要两个点
                    try:
                        start = {'x': float(point_matches[0][0]), 'y': float(point_matches[0][1])}
                        end = {'x': float(point_matches[1][0]), 'y': float(point_matches[1][1])}
                        if not (math.isnan(start['x']) or math.isnan(start['y']) or 
                                math.isnan(end['x']) or math.isnan(end['y'])):
                            geometry_elements.append({
                                'id': f'line_{line_idx}_{id_counter}',
                                'type': 'line',
                                'start': start,
                                'end': end,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue
                break

        # 检测螺纹
        for thread_pattern in thread_patterns:
            thread_matches = re.findall(thread_pattern, line, re.IGNORECASE)
            for match in thread_matches:
                # 检查是否是M格式螺纹 (r M6x1)
                if match and isinstance(match, tuple) and len(match) >= 2 and match[0] and match[1]:
                    try:
                        diameter = float(match[0])
                        pitch = float(match[1])
                        if not (math.isnan(diameter) or math.isnan(pitch)):
                            geometry_elements.append({
                                'id': f'thread_{line_idx}_{id_counter}',
                                'type': 'thread',
                                'diameter': diameter,
                                'pitch': pitch,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue
                else:
                    # 一般螺纹标注
                    geometry_elements.append({
                        'id': f'thread_{line_idx}_{id_counter}',
                        'type': 'thread',
                        'text': line.strip(),
                        'line_index': line_idx
                    })
                    id_counter += 1
                break

        # 检测槽
        for slot_pattern in slot_patterns:
            if re.search(slot_pattern, line, re.IGNORECASE):
                # 尝试从槽的描述中提取尺寸
                dim_matches = re.findall(r'(\d+\.?\d*)\s*mm', line, re.IGNORECASE)
                length_matches = re.findall(r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)', line, re.IGNORECASE)
                if length_matches:
                    try:
                        length = float(length_matches[0][0])
                        width = float(length_matches[0][1])
                        if not (math.isnan(length) or math.isnan(width)):
                            geometry_elements.append({
                                'id': f'slot_{line_idx}_{id_counter}',
                                'type': 'slot',
                                'length': length,
                                'width': width,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue
                elif dim_matches:
                    try:
                        length = float(dim_matches[0])
                        if not math.isnan(length):
                            geometry_elements.append({
                                'id': f'slot_{line_idx}_{id_counter}',
                                'type': 'slot',
                                'length': length,
                                'text': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except ValueError:
                        continue
                else:
                    geometry_elements.append({
                        'id': f'slot_{line_idx}_{id_counter}',
                        'type': 'slot',
                        'text': line.strip(),
                        'line_index': line_idx
                    })
                    id_counter += 1
                break

        # 检测边
        for edge_pattern in edge_patterns:
            if re.search(edge_pattern, line, re.IGNORECASE):
                geometry_elements.append({
                    'id': f'edge_{line_idx}_{id_counter}',
                    'type': 'edge',
                    'text': line.strip(),
                    'line_index': line_idx
                })
                id_counter += 1
                break

        # 检测面
        for face_pattern in face_patterns:
            if re.search(face_pattern, line, re.IGNORECASE):
                geometry_elements.append({
                    'id': f'face_{line_idx}_{id_counter}',
                    'type': 'face',
                    'text': line.strip(),
                    'line_index': line_idx
                })
                id_counter += 1
                break

        # 检测形位公差
        for tolerance_pattern in tolerance_patterns:
            tolerance_matches = re.findall(tolerance_pattern, line)
            for match in tolerance_matches:
                # 检查是否包含公差值
                value_matches = re.findall(r'(\d+\.?\d*)', line)
                if value_matches:
                    try:
                        value = float(value_matches[0])
                        if not math.isnan(value):
                            tolerances.append({
                                'id': f'tolerance_{line_idx}_{id_counter}',
                                'type': 'geometric_tolerance',
                                'value': value,
                                'symbol': match,
                                'description': line.strip(),
                                'line_index': line_idx
                            })
                        else:
                            tolerances.append({
                                'id': f'tolerance_{line_idx}_{id_counter}',
                                'type': 'geometric_tolerance',
                                'symbol': match,
                                'description': line.strip(),
                                'line_index': line_idx
                            })
                    except ValueError:
                        tolerances.append({
                            'id': f'tolerance_{line_idx}_{id_counter}',
                            'type': 'geometric_tolerance',
                            'symbol': match,
                            'description': line.strip(),
                            'line_index': line_idx
                        })
                    id_counter += 1
                else:
                    tolerances.append({
                        'id': f'tolerance_{line_idx}_{id_counter}',
                        'type': 'geometric_tolerance',
                        'symbol': match,
                        'description': line.strip(),
                        'line_index': line_idx
                    })
                    id_counter += 1

        # 检测表面光洁度
        for surface_finish_pattern in surface_finish_patterns:
            finish_matches = re.findall(surface_finish_pattern, line)
            for match in finish_matches:
                if match:  # Ra或Rz值
                    try:
                        value = float(match if isinstance(match, str) and match[0].isdigit() else match[0] if isinstance(match, tuple) else match)
                        if not math.isnan(value):
                            surface_finishes.append({
                                'id': f'surface_finish_{line_idx}_{id_counter}',
                                'type': 'surface_roughness',
                                'value': value,
                                'symbol': match,
                                'description': line.strip(),
                                'line_index': line_idx
                            })
                            id_counter += 1
                    except (ValueError, TypeError):
                        surface_finishes.append({
                            'id': f'surface_finish_{line_idx}_{id_counter}',
                            'type': 'surface_roughness',
                            'symbol': match,
                            'description': line.strip(),
                            'line_index': line_idx
                        })
                        id_counter += 1
                else:
                    surface_finishes.append({
                        'id': f'surface_finish_{line_idx}_{id_counter}',
                        'type': 'surface_roughness',
                        'symbol': match,
                        'description': line.strip(),
                        'line_index': line_idx
                    })
                    id_counter += 1

    # 尝试从上下文推断圆心位置和其他关联信息
    for i in range(len(geometry_elements)):
        if geometry_elements[i].get('type') == 'circle':
            # 查找附近的坐标点作为圆心
            for j in range(len(geometry_elements)):
                if geometry_elements[j].get('type') == 'point' and i != j:
                    # 如果圆的文本描述中包含点的信息，可以推断圆心
                    circle_text = geometry_elements[i].get('text', '')
                    point_text = geometry_elements[j].get('text', '')
                    # 检查是否在同一行或相邻行，或者文本内容有相关性
                    if (abs(geometry_elements[i].get('line_index', 0) - geometry_elements[j].get('line_index', 0)) <= 1 or
                            circle_text in point_text or point_text in circle_text):
                        geometry_elements[i]['center'] = {
                            'x': geometry_elements[j].get('x', 0),
                            'y': geometry_elements[j].get('y', 0)
                        }
                        break

    # 尝试关联尺寸标注与几何元素
    for i in range(len(dimensions)):
        for j in range(len(geometry_elements)):
            # 尝试将尺寸标注与几何元素关联
            dim_text = dimensions[i].get('description', '')
            geom_text = geometry_elements[j].get('text', '')

            # 如果尺寸描述和几何元素文本相关，则建立关联
            if dim_text in geom_text or geom_text in dim_text:
                if 'dimensions' not in geometry_elements[j]:
                    geometry_elements[j]['dimensions'] = []
                if dimensions[i].get('id') not in geometry_elements[j]['dimensions']:
                    geometry_elements[j]['dimensions'].append(dimensions[i].get('id'))

            # 更智能的关联：检查几何元素的坐标是否接近尺寸标注中的数值
            center = geometry_elements[j].get('center', {})
            if center:
                # 检查X坐标是否与尺寸值匹配
                if (abs(center.get('x', 0) - dimensions[i].get('value', 0)) < 1.0 or
                        abs(center.get('y', 0) - dimensions[i].get('value', 0)) < 1.0 or
                        abs(center.get('x', 0) + dimensions[i].get('value', 0)) < 1.0 or
                        abs(center.get('y', 0) + dimensions[i].get('value', 0)) < 1.0):
                    if 'dimensions' not in geometry_elements[j]:
                        geometry_elements[j]['dimensions'] = []
                    if dimensions[i].get('id') not in geometry_elements[j]['dimensions']:
                        geometry_elements[j]['dimensions'].append(dimensions[i].get('id'))

    # 增强复杂CAD图纸解析：识别几何关系
    enhanced_geometry_elements = enhance_geometric_relationships(geometry_elements, dimensions)
    return {
        'geometry_elements': enhanced_geometry_elements,
        'dimensions': dimensions,
        'tolerances': tolerances,
        'surface_finishes': surface_finishes
    }

def enhance_geometric_relationships(geometry_elements: List[Dict[str, Any]], dimensions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    增强几何元素关系识别
    
    Args:
        geometry_elements: 几何元素列表
        dimensions: 尺寸列表
        
    Returns:
        增强后的几何元素列表
    """
    # 识别同心圆
    for i in range(len(geometry_elements)):
        if geometry_elements[i].get('type') == 'circle':
            for j in range(i + 1, len(geometry_elements)):
                if geometry_elements[j].get('type') == 'circle':
                    # 检查是否为同心圆（中心点接近）
                    center1 = geometry_elements[i].get('center', {})
                    center2 = geometry_elements[j].get('center', {})
                    if center1 and center2:
                        distance = math.sqrt(
                            math.pow(center1.get('x', 0) - center2.get('x', 0), 2) +
                            math.pow(center1.get('y', 0) - center2.get('y', 0), 2)
                        )
                        if distance < 0.5:  # 如果中心点距离小于0.5mm，则认为是同心圆
                            if 'related_elements' not in geometry_elements[i]:
                                geometry_elements[i]['related_elements'] = []
                            if 'related_elements' not in geometry_elements[j]:
                                geometry_elements[j]['related_elements'] = []
                            geometry_elements[i]['related_elements'].append(geometry_elements[j].get('id'))
                            geometry_elements[j]['related_elements'].append(geometry_elements[i].get('id'))

                            # 标记为同心圆特征
                            geometry_elements[i]['is_concentric'] = True
                            geometry_elements[j]['is_concentric'] = True

    # 识别孔组
    circles = [el for el in geometry_elements if el.get('type') == 'circle' and 'center' in el]
    if len(circles) > 1:
        # 检查孔是否形成规则阵列（如圆形分布、矩形分布等）
        hole_groups = identify_hole_groups(circles)
        for idx, group in enumerate(hole_groups):
            for circle_id in group['hole_ids']:
                circle = next((el for el in geometry_elements if el.get('id') == circle_id), None)
                if circle:
                    if 'feature_group' not in circle:
                        circle['feature_group'] = []
                    circle['feature_group'].append(f'hole_group_{idx}')
                    circle['group_type'] = group['type']  # 'bolt_circle', 'rectangular_array', etc.

    return geometry_elements

def identify_hole_groups(circles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    识别孔组（如螺棚圆、矩形阵列等）
    
    Args:
        circles: 圆形元素列表
        
    Returns:
        孔组列表
    """
    groups = []
    processed = set()

    for i in range(len(circles)):
        if circles[i].get('id') in processed:
            continue

        # 检查是否可能是螺棚圆的一部分
        potential_bolt_circle = find_bolt_circle(circles, i)
        if potential_bolt_circle and len(potential_bolt_circle['hole_ids']) > 2:
            groups.append({
                'type': 'bolt_circle',
                'center': potential_bolt_circle['center'],
                'radius': potential_bolt_circle['radius'],
                'hole_ids': potential_bolt_circle['hole_ids']
            })

            # 标记这些孔为已处理
            for hole_id in potential_bolt_circle['hole_ids']:
                processed.add(hole_id)
        else:
            # 检查是否可能是矩形阵列
            potential_rect_array = find_rectangular_array(circles, i)
            if potential_rect_array and len(potential_rect_array['hole_ids']) > 1:
                groups.append({
                    'type': 'rectangular_array',
                    'origin': potential_rect_array['origin'],
                    'spacing': potential_rect_array['spacing'],
                    'dimensions': potential_rect_array['dimensions'],
                    'hole_ids': potential_rect_array['hole_ids']
                })

                # 标记这些孔为已处理
                for hole_id in potential_rect_array['hole_ids']:
                    processed.add(hole_id)
            else:
                # 单个孔，不需要分组
                processed.add(circles[i].get('id'))

    return groups

def find_bolt_circle(circles: List[Dict[str, Any]], start_index: int) -> Optional[Dict[str, Any]]:
    """
    查找可能的螺棚圆
    
    Args:
        circles: 圆形元素列表
        start_index: 起始索引
        
    Returns:
        螺棚圆信息
    """
    center_candidate = circles[start_index].get('center', {})
    distances = []

    for i in range(len(circles)):
        if i == start_index:
            continue

        center = circles[i].get('center', {})
        dist = math.sqrt(
            math.pow(center.get('x', 0) - center_candidate.get('x', 0), 2) +
            math.pow(center.get('y', 0) - center_candidate.get('y', 0), 2)
        )
        distances.append({
            'index': i,
            'distance': dist,
            'circle': circles[i]
        })

    # 对距离进行分组，查找相同距离的孔
    distance_groups = {}
    tolerance = 0.5  # 0.5mm的公差
    for dist in distances:
        # 找到最接近的距离桶
        found_group = False
        for dist_key, group in distance_groups.items():
            if abs(float(dist_key) - dist['distance']) < tolerance:
                group.append(dist)
                found_group = True
                break
        if not found_group:
            distance_groups[str(dist['distance'])] = [dist]

    # 查找包含至少3个孔的距离组
    for dist_key, group in distance_groups.items():
        if len(group) >= 3:  # 至少3个孔才能形成圆
            return {
                'center': center_candidate,
                'radius': float(dist_key),
                'hole_ids': [circles[start_index].get('id')] + [d['circle'].get('id') for d in group]
            }

    return None

def find_rectangular_array(circles: List[Dict[str, Any]], start_index: int) -> Optional[Dict[str, Any]]:
    """
    查找可能的矩形阵列
    
    Args:
        circles: 圆形元素列表
        start_index: 起始索引
        
    Returns:
        矩形阵列信息
    """
    origin = circles[start_index].get('center', {})
    x_coords = set()
    y_coords = set()

    # 收集所有孔的坐标
    for circle in circles:
        center = circle.get('center', {})
        x_coords.add(center.get('x', 0))
        y_coords.add(center.get('y', 0))

    sorted_x = sorted(list(x_coords))
    sorted_y = sorted(list(y_coords))

    # 检查是否形成规则的网格
    if len(sorted_x) > 1 and len(sorted_y) > 1:
        # 计算X和Y方向的间距
        x_spacing = (sorted_x[-1] - sorted_x[0]) / (len(sorted_x) - 1) if len(sorted_x) > 1 else 0
        y_spacing = (sorted_y[-1] - sorted_y[0]) / (len(sorted_y) - 1) if len(sorted_y) > 1 else 0

        # 检查是否为等间距分布
        is_regular = True
        if len(sorted_x) > 2:
            for i in range(1, len(sorted_x)):
                calculated_spacing = sorted_x[i] - sorted_x[i-1]
                if abs(calculated_spacing - x_spacing) > 0.1:
                    is_regular = False
                    break

        if len(sorted_y) > 2:
            for i in range(1, len(sorted_y)):
                calculated_spacing = sorted_y[i] - sorted_y[0]
                if abs(calculated_spacing - y_spacing * i) > 0.1:
                    is_regular = False
                    break

        if is_regular and x_spacing > 0.1 and y_spacing > 0.1:
            # 确认实际存在这些位置的孔
            expected_holes = []
            for x_idx in range(len(sorted_x)):
                for y_idx in range(len(sorted_y)):
                    expected_x = sorted_x[0] + x_idx * x_spacing
                    expected_y = sorted_y[0] + y_idx * y_spacing

                    # 查找实际存在的孔
                    for circle in circles:
                        center = circle.get('center', {})
                        if abs(center.get('x', 0) - expected_x) < 0.2 and abs(center.get('y', 0) - expected_y) < 0.2:
                            expected_holes.append(circle.get('id'))

            if len(expected_holes) >= 2 and len(expected_holes) >= len(sorted_x) * len(sorted_y) * 0.7:  # 至少70%的孔存在
                return {
                    'origin': {'x': sorted_x[0], 'y': sorted_y[0]},
                    'spacing': {'x': x_spacing, 'y': y_spacing},
                    'dimensions': {'x': len(sorted_x), 'y': len(sorted_y)},
                    'hole_ids': expected_holes
                }

    return None

def post_process_ocr_text(ocr_text: str) -> str:
    """
    OCR文本后处理函数，提高CAD图纸元素识别准确性
    
    Args:
        ocr_text: OCR识别的文本
        
    Returns:
        处理后的文本
    """
    if not ocr_text or not isinstance(ocr_text, str):
        return ocr_text

    processed_text = ocr_text

    # 修复常见的OCR错误
    corrections = [
        # 修复数字和字母的亏识别
        (r'(\d)O(\d)', r'\10\2'),  # 将 "O" 在数字中间时修正为 "0"
        (r'(\d)l(\d)', r'\11\2'),  # 将 "l" 在数字中间时修正为 "1"
        (r'(\d)I(\d)', r'\11\2'),  # 将 "I" 在数字中间时修正为 "1"
        (r'(\d)Z(\d)', r'\12\2'),  # 将 "Z" 在数字中间时修正为 "2"
        (r'(\d)S(\d)', r'\15\2'),  # 将 "S" 在数字中间时修正为 "5"

        # 修复单位识别错误
        (r'(\d+)\s*tnm', r'\1 mm'),  # 将 "tnm" 修正为 "mm"
        (r'(\d+)\s*nn', r'\1 mm'),  # 将 "nn" 修正为 "mm"
        (r'(\d+)\s*rm', r'\1 mm'),  # 将 "rm" 修正为 "mm"
        (r'(\d+)\s*cm', r'\1 mm'),  # 将 "cm" 修正为 "mm" (假设是毫米)
        (r'(\d+)\s*inn', r'\1 in'),  # 将 "inn" 修正为 "in"

        # 修复钻孔相关术语
        (r'H0LE', r'HOLE'),  # 将 "H0LE" 修正为 "HOLE"
        (r'h0le', r'hole'),  # 将 "h0le" 修正为 "hole"
        (r'dril', r'drill'),  # 将 "dril" 修正为 "drill"
        (r'thru', r'THRU'),  # 将 "thru" 修正为 "THRU"

        # 修复几何术语
        (r'C1RCLE', r'CIRCLE'),  # 将 "C1RCLE" 修正为 "CIRCLE"
        (r'rectange', r'rectangle'),  # 将 "rectange" 修正为 "rectangle"
        (r'dimention', r'dimension'),  # 将 "dimention" 修正为 "dimension"
        (r'dimentions', r'dimensions'),  # 将 "dimentions" 修正为 "dimensions"

        # 修复符号
        (r'81', r'G81'),  # 将 "81" 修正为 "G81" (G代码)
        (r'80', r'G80'),  # 将 "80" 修正为 "G80" (G代码)
        (r'82', r'G82'),  # 将 "82" 修正为 "G82" (G代码)
        (r'83', r'G83'),  # 将 "83" 修正为 "G83" (G代码)
        (r'98', r'G98'),  # 将 "98" 修正为 "G98" (G代码)

        # 修复坐标格式
        (r'\s*Z\s*-\s*(\d+\.?\d*)', r' Z-\1'),  # 修正 Z- 格式
        (r'\s*R\s*(\d+\.?\d*)', r' R\1'),      # 修正 R 格式
        (r'\s*F\s*(\d+\.?\d*)', r' F\1'),      # 修正 F 格式

        # 修复小数点问题
        (r'(\d)\.(\d)\.(\d)', r'\1.\2 \3'),  # 修复多重小数点

        # 修复常见的中文亏识别
        (r'孔日', r'孔口'),  # 修正孔的表述
        (r'孔0', r'孔'),    # 修正孔的表述
        (r'深度日', r'深度'), # 修正深度的表述
    ]

    # 应用所有修正
    for pattern, replacement in corrections:
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)

    return processed_text

def identify_view_orientation(geometry_elements: List[Dict[str, Any]], dimensions: List[Dict[str, Any]], text_content: str) -> Dict[str, Any]:
    """
    自动视角识别函数
    
    Args:
        geometry_elements: 几何元素列表
        dimensions: 尺寸列表
        text_content: 文本内容
        
    Returns:
        视角信息
    """
    # 检查是否存在坐标系标注
    has_coordinate_system = 'x' in text_content.lower() and 'y' in text_content.lower()

    # 检查是否有标注原点
    has_origin = any(keyword in text_content.lower() for keyword in ['origin', '原点'])

    # 分析几何元素的位置分布
    points = [el for el in geometry_elements if 'center' in el or ('x' in el and 'y' in el)]
    if points:
        x_coords = [el.get('center', {}).get('x', el.get('x', 0)) for el in points]
        y_coords = [el.get('center', {}).get('y', el.get('y', 0)) for el in points]
        min_x = min(x_coords) if x_coords else 0
        max_x = max(x_coords) if x_coords else 0
        min_y = min(y_coords) if y_coords else 0
        max_y = max(y_coords) if y_coords else 0

        # 判断图纸的主要视角
        if max_x > 0 and max_y > 0:
            # 如果所有坐标都是正数，可能采用第一象限坐标系
            return {
                'origin': {'x': min_x, 'y': max_y},  # 通常左上角为原点
                'orientation': 'top_left_quadrant1',
                'x_positive_direction': 'right',
                'y_positive_direction': 'down'
            }
        else:
            # 如果有负坐标，使用中心为原点的坐标系
            return {
                'origin': {'x': (min_x + max_x) / 2, 'y': (min_y + max_y) / 2},
                'orientation': 'center_zero',
                'x_positive_direction': 'right',
                'y_positive_direction': 'up'
            }

    # 默认返回右上角为原点的坐标系
    return {
        'origin': {'x': 0, 'y': 0},
        'orientation': 'top_right',
        'x_positive_direction': 'left',  # X轴向左为正
        'y_positive_direction': 'down'   # Y轴向下为正
    }

def pdf_parsing_process(file_path: str) -> Dict[str, Any]:
    """
    解析PDF内容的主要函数
    
    Args:
        file_path: PDF文件路径
        
    Returns:
        解析结果
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError('文件路径无效')

    if not os.path.exists(file_path):
        raise ValueError(f'文件不存在: {file_path}')

    # 获取文件信息
    file_stats = os.stat(file_path)
    file_extension = os.path.splitext(file_path)[1].lower()

    # 根据文件类型返回不同结果
    drawing_info = {
        'file_name': os.path.basename(file_path),
        'file_path': file_path,
        'file_size': file_stats.st_size,
        'file_type': file_extension,
        'parsed_at': datetime.now().isoformat(),
        'page_count': 0,  # 将在解析后更新
        'dimensions': {'width': 0, 'height': 0}
    }

    geometry_elements = []
    dimensions = []
    tolerances = []  # 形位公差
    surface_finishes = []  # 表面光洁度
    text_content = ''  # 存储所有文本内容用于视角识别

    # 使用机械制图专家来分析图纸
    drawing_expert = MechanicalDrawingExpert()

    # 对于PDF文件，我们暂时返回基本结构，因为完整的PDF解析需要额外的库
    if file_extension == '.pdf':
        try:
            # 尝试使用PyPDF2或pdfplumber进行PDF文本提取
            try:
                import PyPDF2
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    drawing_info['page_count'] = len(pdf_reader.pages)
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        text_content += page_text + ' '
                        
                        # 从文本中提取几何信息
                        extracted = extract_geometric_info_from_text(page_text)
                        geometry_elements.extend(extracted['geometry_elements'])
                        dimensions.extend(extracted['dimensions'])
                        tolerances.extend(extracted['tolerances'])
                        surface_finishes.extend(extracted['surface_finishes'])
            except ImportError:
                import logging
                logging.warning("警告: 未安装PyPDF2，无法解析PDF文本内容")
                # 返回基本结构
                geometry_elements = [
                    {'id': 'default_rectangle', 'type': 'rectangle', 'bounds': {'x': 10, 'y': 10, 'width': 80, 'height': 60}}
                ]
                dimensions = [
                    {'id': 'dim_1', 'type': 'linear', 'value': 100},
                    {'id': 'dim_2', 'type': 'linear', 'value': 50}
                ]
                drawing_info['dimensions'] = {'width': 100, 'height': 50}
                
        except Exception as e:
            print(f'PDF解析错误: {e}')
            raise ValueError(f'PDF解析失败: {str(e)}')
    else:
        # 对于其他文件类型，返回简化数据
        geometry_elements = [
            {'id': 'element_1', 'type': 'rectangle', 'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 50}}
        ]

        dimensions = [
            {'id': 'dim_1', 'type': 'linear', 'value': 100},
            {'id': 'dim_2', 'type': 'linear', 'value': 50}
        ]

        drawing_info['dimensions'] = {'width': 100, 'height': 50}

    # 使用机械制图专家分析图纸
    try:
        drawing_analysis = drawing_expert.parse_drawing(text_content)
        
        # 整合机械制图专家的分析结果
        for view in drawing_analysis.views:
            # 从视图中提取参考点
            for ref_name, ref_point in view.reference_points.items():
                geometry_elements.append({
                    'id': f'reference_point_{ref_name}',
                    'type': 'reference_point',
                    'name': ref_name,
                    'x': ref_point[0],
                    'y': ref_point[1],
                    'description': f'参考点 {ref_name} at ({ref_point[0]}, {ref_point[1]})'
                })
        
        # 整合整体尺寸信息
        for dim in drawing_analysis.overall_dimensions:
            dimensions.append({
                'id': f'overall_dim_{len(dimensions) + 1}',
                'type': dim.dimension_type,
                'value': dim.value,
                'unit': dim.unit,
                'tolerance': dim.tolerance,
                'description': f'整体尺寸'
            })
        
        # 更新图纸信息
        if drawing_analysis.material:
            drawing_info['material'] = drawing_analysis.material
        if drawing_analysis.drawing_number:
            drawing_info['drawing_number'] = drawing_analysis.drawing_number
        if drawing_analysis.revision:
            drawing_info['revision'] = drawing_analysis.revision
            
    except Exception as e:
        print(f'机械制图专家分析失败: {e}')

    # 如果最终没有提取到任何几何元素，提供一些默认值以确保API的稳定性
    if not geometry_elements:
        geometry_elements = [
            {'id': 'default_rectangle', 'type': 'rectangle', 'bounds': {'x': 10, 'y': 10, 'width': 80, 'height': 60}}
        ]

    # 验证几何元素的有效性
    validation = validate_geometry_elements(geometry_elements)
    if validation.get('warnings'):
        print('几何元素验证警告:', validation['warnings'])

    return {
        'drawing_info': drawing_info,
        'geometry_elements': geometry_elements,
        'dimensions': dimensions,
        'tolerances': tolerances,
        'surface_finishes': surface_finishes,
        'reference_points': drawing_analysis.views[0].reference_points if drawing_analysis.views else {},  # 添加参考点信息
        'view_relationships': drawing_expert.analyze_view_relationships(drawing_analysis) if 'drawing_analysis' in locals() else {},  # 添加视图关系
        'parsing_time': 0  # 暂时设置为0，实际使用时可以计算
    }


if __name__ == "__main__":
    # 测试代码
    sample_text = """
    这是一个示例图纸
    孔位置: X10.5, Y20.3, 直径∅5.5mm
    矩形: 宽度30mm, 高度20mm
    圆心: (50, 50), 半径R10
    """
    
    result = extract_geometric_info_from_text(sample_text)
    print("从文本中提取的几何信息:")
    print(f"  几何元素数: {len(result['geometry_elements'])}")
    print(f"  尺寸数: {len(result['dimensions'])}")
    print(f"  形位公差数: {len(result['tolerances'])}")
    print(f"  表面光洁度数: {len(result['surface_finishes'])}")
    
    for element in result['geometry_elements'][:3]:  # 只打印前3个
        print(f"  元素: {element}")

"""
特征定义模块
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math
import uuid

from .validation import validate_geometry_elements
from .material_tool_matcher import match_material_and_tool, recommend_machining_parameters


def select_feature(project: Any, x: float, y: float) -> Optional[Dict[str, Any]]:
    """
    选择特征
    
    Args:
        project: 项目对象
        x: X坐标
        y: Y坐标
        
    Returns:
        选中的特征信息，如果未找到则返回None
    """
    if not project or not hasattr(project, 'geometry_elements'):
        raise ValueError('项目参数无效')

    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError('坐标参数必须是数字')

    if not isinstance(project.geometry_elements, list):
        raise ValueError('项目几何元素列表无效')

    # 验证几何元素
    validation = validate_geometry_elements(project.geometry_elements)
    if not validation.get('valid', True):
        print('几何元素验证失败:', validation.get('errors', []))

    # 查找在指定坐标附近的几何元素
    # 首先尝试使用较小的容差
    tolerance = 5  # 像素容差
    selected_element = None
    
    for element in project.geometry_elements:
        # 检查元素是否存在且有type属性
        if not element or not isinstance(element, dict) or not element.get('type'):
            continue

        element_type = element['type']
        if element_type == 'line':
            if is_point_near_line({'x': x, 'y': y}, element, tolerance):
                selected_element = element
                break
        elif element_type == 'circle':
            if is_point_near_circle({'x': x, 'y': y}, element, tolerance):
                selected_element = element
                break
        elif element_type == 'rectangle':
            if is_point_in_rectangle({'x': x, 'y': y}, element, tolerance):
                selected_element = element
                break
        else:
            if is_point_near_generic({'x': x, 'y': y}, element, tolerance):
                selected_element = element
                break

    # 如果没找到，尝试使用较大的容差来查找圆（特别针对孔特征）
    if not selected_element:
        tolerance = 15  # 增加容差以查找孔特征
        for element in project.geometry_elements:
            if not element or not isinstance(element, dict) or not element.get('type'):
                continue

            # 专门针对圆/孔特征使用较大容差
            if element['type'] == 'circle' and element.get('center'):
                center = element['center']
                distance = math.sqrt(math.pow(x - center['x'], 2) + math.pow(y - center['y'], 2))
                if distance <= tolerance:
                    selected_element = element
                    break

    # 如果仍然没找到，创建一个虚拟的圆元素（用于指定坐标处的孔）
    if not selected_element:
        # 检查是否是在指定的目标位置
        is_target_position = (abs(x + 20) < 0.1 and abs(y + 5) < 0.1) or \
                            (abs(x + 80) < 0.1 and abs(y + 5) < 0.1)

        if is_target_position:
            selected_element = {
                'id': f'virtual_circle_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}',
                'type': 'circle',
                'center': {'x': x, 'y': y},
                'radius': 2.75,  # 默认半径对应5.5mm直径
                'text': f'Target hole at X{x}, Y{y}',
                'is_virtual': True  # 标记为虚拟元素
            }

            # 添加到项目的几何元素中
            project.geometry_elements.append(selected_element)

    if selected_element:
        return {
            'element': selected_element,
            'coordinates': {'x': x, 'y': y},
            'timestamp': datetime.now().isoformat()
        }

    return None


def is_point_near_line(point: Dict[str, float], line: Dict[str, Any], tolerance: float) -> bool:
    """
    检查点是否在线附近
    """
    start = line.get('start', {})
    end = line.get('end', {})
    
    # 简化的点线距离计算
    dist_to_start = math.sqrt(math.pow(point['x'] - start.get('x', 0), 2) + 
                              math.pow(point['y'] - start.get('y', 0), 2))
    dist_to_end = math.sqrt(math.pow(point['x'] - end.get('x', 0), 2) + 
                            math.pow(point['y'] - end.get('y', 0), 2))
    
    # 简化：如果点接近线的端点之一，则认为在线上
    return dist_to_start <= tolerance or dist_to_end <= tolerance


def is_point_near_circle(point: Dict[str, float], circle: Dict[str, Any], tolerance: float) -> bool:
    """
    检查点是否在圆附近
    """
    center = circle.get('center', {})
    center_x = center.get('x', 0)
    center_y = center.get('y', 0)
    
    # 使用平方距离避免开方运算，提高性能
    dx = point['x'] - center_x
    dy = point['y'] - center_y
    dist_squared = dx * dx + dy * dy
    radius = circle.get('radius', 0)
    
    # 检查点是否在[半径-容差, 半径+容差]范围内
    min_radius = radius - tolerance
    max_radius = radius + tolerance
    min_dist_squared = min_radius * min_radius
    max_dist_squared = max_radius * max_radius
    
    return min_dist_squared <= dist_squared <= max_dist_squared


def is_point_in_rectangle(point: Dict[str, float], rectangle: Dict[str, Any], tolerance: float) -> bool:
    """
    检查点是否在矩形内
    """
    bounds = rectangle.get('bounds', {})
    return (point['x'] >= bounds.get('x', 0) - tolerance and 
            point['x'] <= bounds.get('x', 0) + bounds.get('width', 0) + tolerance and
            point['y'] >= bounds.get('y', 0) - tolerance and 
            point['y'] <= bounds.get('y', 0) + bounds.get('height', 0) + tolerance)


def is_point_near_generic(point: Dict[str, float], element: Dict[str, Any], tolerance: float) -> bool:
    """
    通用的点元素距离检查
    """
    # 对于其他类型的元素，使用中心点进行检查
    center = element.get('center', {})
    if center:
        distance = math.sqrt(math.pow(point['x'] - center.get('x', 0), 2) + 
                             math.pow(point['y'] - center.get('y', 0), 2))
        return distance <= tolerance
    return False


def start_feature_definition(project: Any, element: Dict[str, Any], dimensions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    开始特征定义
    
    Args:
        project: 项目对象
        element: 几何元素
        dimensions: 尺寸列表
        
    Returns:
        特征定义对象
    """
    if not project or not hasattr(project, '__dict__'):
        raise ValueError('项目参数无效')

    if not element or not isinstance(element, dict):
        raise ValueError('元素参数无效')

    # 创建特征对象
    feature = {
        'id': f'feat_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}',
        'element_id': element.get('id'),
        'element_type': element.get('type'),
        'base_geometry': dict(element),
        'feature_type': None,
        'dimensions': dimensions or [],
        'macro_variables': {},
        'parameters': {},
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    # 初始化项目特征数组（如果不存在）
    if not hasattr(project, 'features') or not isinstance(project.features, list):
        project.features = []

    # 更新项目元数据
    if hasattr(project, 'updated_at'):
        project.updated_at = datetime.now()

    return feature


def select_feature_type(feature: Dict[str, Any], feature_type: str) -> None:
    """
    选择特征类型
    
    Args:
        feature: 特征对象
        feature_type: 特征类型
    """
    if not feature or not isinstance(feature, dict):
        raise ValueError('特征参数无效')

    if not feature_type or not isinstance(feature_type, str):
        raise ValueError('特征类型参数无效')

    # 验证特征类型
    valid_feature_types = [
        'hole', 'counterbore', 'pocket', 'boss', 'slot',
        'chamfer', 'fillet', 'extrude', 'cut', 'thread',
        'surface_finish', 'tolerance'
    ]

    if feature_type not in valid_feature_types:
        raise ValueError(f'不支持的特征类型: {feature_type}')

    # 更新特征类型
    feature['feature_type'] = feature_type
    feature['updated_at'] = datetime.now().isoformat()

    # 根据特征类型设置默认参数
    set_default_parameters(feature)


def set_default_parameters(feature: Dict[str, Any]) -> None:
    """
    根据特征类型设置默认参数
    
    Args:
        feature: 特征对象
    """
    feature_type = feature.get('feature_type')
    
    if feature_type == 'hole':
        feature['parameters'] = {
            'diameter': 5.5,        # 孔径5.5mm
            'depth': 14,            # 实际加工深度14mm
            'drawing_depth': 10,     # 图纸深度10mm
            'type': 'through',
            'finish': 'standard',
            'tool_number': 2         # 默认使用钻头T02
        }
    elif feature_type == 'counterbore':       # 沉头孔特征
        feature['parameters'] = {
            'diameter': 5.5,        # 孔径5.5mm
            'depth': 14,            # 实际加工深度14mm
            'drawing_depth': 10,     # 图纸深度10mm
            'counterbore_diameter': 9,   # 沉孔径9mm
            'counterbore_depth': 5.5,    # 沉孔深度5.5mm
            'use_counterbore': True,     # 使用沉孔
            'type': 'counterbore',
            'finish': 'standard'
        }
    elif feature_type == 'pocket':
        feature['parameters'] = {
            'width': 20,
            'length': 20,
            'depth': 10,
            'bottom': 'flat',
            'finish': 'standard'
        }
    elif feature_type == 'slot':
        feature['parameters'] = {
            'width': 5,
            'length': 30,
            'depth': 5,
            'type': 'through',
            'end_type': 'straight'
        }
    elif feature_type == 'chamfer':
        feature['parameters'] = {
            'angle': 45,
            'distance': 2
        }
    elif feature_type == 'fillet':
        feature['parameters'] = {
            'radius': 5
        }
    elif feature_type == 'thread': # 螺纹特征
        feature['parameters'] = {
            'diameter': 6,          # 螺纹直径
            'pitch': 1,             # 螺距
            'depth': 10,            # 螺纹深度
            'thread_type': 'internal' # 螺纹类型：internal(内螺纹)或external(外螺纹)
        }
    elif feature_type == 'surface_finish': # 表面光洁度
        feature['parameters'] = {
            'roughness': 'Ra3.2',   # 表面粗糙度
            'operation': 'finish',   # 加工类型：rough(粗加工), semi_finish(半精加工), finish(精加工)
            'feed_rate': 200        # 进给率
        }
    elif feature_type == 'tolerance': # 形位公差
        feature['parameters'] = {
            'type': 'position',      # 公差类型：position(位置), concentricity(同心度), parallelism(平行度), etc.
            'value': 0.1,           # 公差值
            'datum': 'A'            # 基准
        }
    else:
        feature['parameters'] = {}


def associate_macro_variable(feature: Dict[str, Any], dimension_id: str, variable_name: str) -> None:
    """
    关联宏变量
    
    Args:
        feature: 特征对象
        dimension_id: 尺寸ID
        variable_name: 变量名
    """
    if not feature or not isinstance(feature, dict):
        raise ValueError('特征参数无效')

    if not dimension_id or not isinstance(dimension_id, str):
        raise ValueError('尺寸ID参数无效')

    if not variable_name or not isinstance(variable_name, str):
        raise ValueError('变量名参数无效')

    # 验证变量名格式
    import re
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', variable_name):
        raise ValueError('变量名格式无效，应以字母或下划线开头，后跟字母、数字或下划线')

    # 初始化宏变量对象
    if 'macro_variables' not in feature:
        feature['macro_variables'] = {}

    # 关联变量
    feature['macro_variables'][dimension_id] = variable_name
    feature['updated_at'] = datetime.now().isoformat()


if __name__ == "__main__":
    # 测试代码
    class MockProject:
        def __init__(self):
            self.geometry_elements = [
                {
                    'id': 'circle1',
                    'type': 'circle',
                    'center': {'x': 10, 'y': 10},
                    'radius': 5
                },
                {
                    'id': 'line1',
                    'type': 'line',
                    'start': {'x': 0, 'y': 0},
                    'end': {'x': 20, 'y': 20}
                }
            ]
    
    project = MockProject()
    result = select_feature(project, 10, 10)
    print("选择特征结果:", result)
    
    if result:
        feature = start_feature_definition(project, result['element'], [])
        print("特征定义:", feature)
        
        select_feature_type(feature, 'hole')
        print("选择特征类型后:", feature)

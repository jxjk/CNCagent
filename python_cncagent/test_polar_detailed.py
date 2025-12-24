"""
检查完整的极坐标G代码生成
"""
import sys
import os
import math
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system, extract_highest_y_center_point
from src.modules.gcode_generation import generate_fanuc_nc

# 模拟用户场景 - 包含极坐标要求
mock_features = [
    {'shape': 'circle', 'center': (1063.0, 86.0), 'radius': 8.0, 'circularity': 0.9, 'confidence': 0.88, 'area': 200, 'bounding_box': (1055, 78, 16, 16), 'contour': [], 'aspect_ratio': 1.0},
    {'shape': 'circle', 'center': (969.0, 116.0), 'radius': 11.0, 'circularity': 0.9, 'confidence': 0.9, 'area': 380, 'bounding_box': (958, 105, 22, 22), 'contour': [], 'aspect_ratio': 1.0},  # 相对于基准(1063,86)的(-94, 30)
    {'shape': 'circle', 'center': (1063.0, 176.0), 'radius': 11.0, 'circularity': 0.88, 'confidence': 0.85, 'area': 380, 'bounding_box': (1052, 165, 22, 22), 'contour': [], 'aspect_ratio': 1.0},  # 相对于基准(0, 90)
    {'shape': 'circle', 'center': (1063.0, 296.0), 'radius': 11.0, 'circularity': 0.92, 'confidence': 0.88, 'area': 380, 'bounding_box': (1052, 285, 22, 22), 'contour': [], 'aspect_ratio': 1.0}  # 相对于基准(0, 210)
]

# 应用坐标系统调整
origin = extract_highest_y_center_point(mock_features)
adjusted_features = adjust_coordinate_system(mock_features, (0, 0), 'highest_y')

# 识别沉孔特征
user_description = '加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。极坐标标注位置X94.0Y-30.0 Y90.0 Y210.0。'
result_features = identify_counterbore_features(adjusted_features, user_description, '')

print('沉孔特征位置:')
for f in result_features:
    if f['shape'] == 'counterbore':
        print(f'  {f["center"]}')

# 生成G代码
description_analysis = {
    'processing_type': 'counterbore',
    'description': user_description,
    'depth': 20.0,
    'tool_required': 'counterbore_tool'
}

gcode = generate_fanuc_nc(result_features, description_analysis)

# 计算预期的极坐标值来验证
base_x, base_y = 0.0, 0.0  # 参考点
positions = [f['center'] for f in result_features if f['shape'] == 'counterbore']
print(f'\n参考点: ({base_x}, {base_y})')
for i, (x, y) in enumerate(positions):
    dx = x - base_x
    dy = y - base_y
    radius = math.sqrt(dx*dx + dy*dy)
    angle = math.degrees(math.atan2(dy, dx))
    print(f'孔{i+1}: ({x:.1f}, {y:.1f}) -> R{radius:.1f}, 角度{angle:.1f}°')

print('\n完整G代码中的极坐标相关部分:')
for i, line in enumerate(gcode.split('\n')):
    if 'G16' in line or 'G15' in line or ('X' in line and 'Y' in line and ('R' in line or 'ANGLE' in line)):
        print(f'{i+1:3d}: {line}')
    elif 'PILOT DRILLING' in line or 'DRILLING' in line or 'COUNTERBORE' in line:
        if 'X' in line and 'Y' in line:
            print(f'{i+1:3d}: {line}')

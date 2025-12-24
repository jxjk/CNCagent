"""
最终验证脚本
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system, extract_highest_y_center_point
from src.modules.gcode_generation import generate_fanuc_nc

# 模拟用户场景
mock_features = [
    {"shape": "circle", "center": (1063.0, 86.0), "radius": 8.0, "circularity": 0.9, "confidence": 0.88, "area": 200, "bounding_box": (1055, 78, 16, 16), "contour": [], "aspect_ratio": 1.0},
    {"shape": "circle", "center": (940.0, 116.0), "radius": 11.0, "circularity": 0.9, "confidence": 0.9, "area": 380, "bounding_box": (929, 105, 22, 22), "contour": [], "aspect_ratio": 1.0},
    {"shape": "circle", "center": (1063.0, 176.0), "radius": 11.0, "circularity": 0.88, "confidence": 0.85, "area": 380, "bounding_box": (1052, 165, 22, 22), "contour": [], "aspect_ratio": 1.0},
    {"shape": "circle", "center": (1063.0, 296.0), "radius": 11.0, "circularity": 0.92, "confidence": 0.88, "area": 380, "bounding_box": (1052, 285, 22, 22), "contour": [], "aspect_ratio": 1.0}
]

print('坐标变换前特征:')
for i, f in enumerate(mock_features):
    print(f'  特征{i+1}: {f["shape"]} at {f["center"]}')

# 应用坐标系统调整
origin = extract_highest_y_center_point(mock_features)
print(f'\n坐标原点: {origin}')

adjusted_features = adjust_coordinate_system(mock_features, (0, 0), "highest_y")

print('\n坐标变换后特征:')
for i, f in enumerate(adjusted_features):
    print(f'  特征{i+1}: {f["shape"]} at {f["center"]}')

# 识别沉孔特征
user_description = '加工3个φ22深20底孔φ14.5贯通的沉孔特征'
result_features = identify_counterbore_features(adjusted_features, user_description, '')

counterbore_count = len([f for f in result_features if f["shape"] == "counterbore"])
print(f'\n识别到的沉孔特征数量: {counterbore_count}')

for feature in result_features:
    if feature["shape"] == "counterbore":
        print(f'  沉孔: 位置{feature["center"]}, 直径{feature["outer_diameter"]}')

# 生成G代码
description_analysis = {
    "processing_type": "counterbore",
    "description": user_description,
    "depth": 20.0,
    "tool_required": "counterbore_tool"
}

gcode = generate_fanuc_nc(result_features, description_analysis)

print('\nG代码中相关行:')
for line in gcode.split('\n'):
    if 'COUNTERBORE PROCESS' in line or ('HOLE' in line and 'POSITION' in line) or 'φ22.0' in line:
        print(f'  {line}')
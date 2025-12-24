"""
生成最终测试的NC输出文件
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_counterbore_features, adjust_coordinate_system, extract_highest_y_center_point
from src.modules.gcode_generation import generate_fanuc_nc

# 模拟用户场景
mock_features = [
    {'shape': 'circle', 'center': (1063.0, 86.0), 'radius': 8.0, 'circularity': 0.9, 'confidence': 0.88, 'area': 200, 'bounding_box': (1055, 78, 16, 16), 'contour': [], 'aspect_ratio': 1.0},
    {'shape': 'circle', 'center': (940.0, 116.0), 'radius': 11.0, 'circularity': 0.9, 'confidence': 0.9, 'area': 380, 'bounding_box': (929, 105, 22, 22), 'contour': [], 'aspect_ratio': 1.0},
    {'shape': 'circle', 'center': (1063.0, 176.0), 'radius': 11.0, 'circularity': 0.88, 'confidence': 0.85, 'area': 380, 'bounding_box': (1052, 165, 22, 22), 'contour': [], 'aspect_ratio': 1.0},
    {'shape': 'circle', 'center': (1063.0, 296.0), 'radius': 11.0, 'circularity': 0.92, 'confidence': 0.88, 'area': 380, 'bounding_box': (1052, 285, 22, 22), 'contour': [], 'aspect_ratio': 1.0}
]

# 应用坐标系统调整
origin = extract_highest_y_center_point(mock_features)
adjusted_features = adjust_coordinate_system(mock_features, (0, 0), 'highest_y')

# 识别沉孔特征
user_description = '加工3个φ22深20底孔φ14.5贯通的沉孔特征'
result_features = identify_counterbore_features(adjusted_features, user_description, '')

# 生成G代码
description_analysis = {
    'processing_type': 'counterbore',
    'description': user_description,
    'depth': 20.0,
    'tool_required': 'counterbore_tool'
}

gcode = generate_fanuc_nc(result_features, description_analysis)

# 写入NC文件
with open('final_test_output.nc', 'w', encoding='utf-8') as f:
    f.write(gcode)

print('NC程序已生成: final_test_output.nc')
print('输出前20行预览:')
for i, line in enumerate(gcode.split('\n')[:20]):
    print(f'{i+1:2d}: {line}')

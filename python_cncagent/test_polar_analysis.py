import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

# 测试极坐标识别功能
user_description = '沉孔加工，极坐标X94.0 Y-30.，X94.0 Y90.，X94.0 Y210.，φ22深20，φ14.5贯通底孔'

# 分析用户描述
description_analysis = analyze_user_description(user_description)
print('分析结果:')
print('  加工类型:', description_analysis['processing_type'])
print('  深度:', description_analysis['depth'])
print('  孔位置:', description_analysis['hole_positions'])
print('  描述:', description_analysis['description'])

# 手动设置为沉孔类型
description_analysis['processing_type'] = 'counterbore'

# 创建模拟的沉孔特征
features = [
    {
        'shape': 'counterbore',
        'center': (94.0, -30.0),  # 极坐标位置
        'outer_radius': 11,  # φ22mm沉孔
        'inner_radius': 7.25,  # φ14.5mm底孔
        'outer_diameter': 22.0,
        'inner_diameter': 14.5,
        'depth': 20.0,  # 沉孔深度20mm
        'contour': [],
        'bounding_box': (83, -41, 22, 22),
        'area': 380,
        'confidence': 0.9,
        'aspect_ratio': 1.0
    },
    {
        'shape': 'counterbore',
        'center': (94.0, 90.0),  # 极坐标位置
        'outer_radius': 11,  # φ22mm沉孔
        'inner_radius': 7.25,  # φ14.5mm底孔
        'outer_diameter': 22.0,
        'inner_diameter': 14.5,
        'depth': 20.0,  # 沉孔深度20mm
        'contour': [],
        'bounding_box': (83, 79, 22, 22),
        'area': 380,
        'confidence': 0.9,
        'aspect_ratio': 1.0
    },
    {
        'shape': 'counterbore',
        'center': (94.0, 210.0),  # 极坐标位置
        'outer_radius': 11,  # φ22mm沉孔
        'inner_radius': 7.25,  # φ14.5mm底孔
        'outer_diameter': 22.0,
        'inner_diameter': 14.5,
        'depth': 20.0,  # 沉孔深度20mm
        'contour': [],
        'bounding_box': (83, 199, 22, 22),
        'area': 380,
        'confidence': 0.9,
        'aspect_ratio': 1.0
    }
]

# 生成NC代码
nc_program = generate_fanuc_nc(features, description_analysis)
print('\n生成的NC程序:')
print('-' * 50)
print(nc_program)
print('-' * 50)

# 保存生成的NC程序
with open("test_polar_coordinate_output.nc", "w", encoding="utf-8") as f:
    f.write(nc_program)
print("\nNC程序已保存到: test_polar_coordinate_output.nc")
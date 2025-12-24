import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

# 用户需求：加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用极坐标位置X94.0Y-30. X94.0Y90. X94.0Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。

user_description = '加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0Y-30. X94.0Y90. X94.0Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视视图φ234的圆的圆心最高点。作为Fanuc加工中心程序专家给出NC代码。'

# 分析用户描述
description_analysis = analyze_user_description(user_description)
print('分析结果:')
print('  加工类型:', description_analysis["processing_type"])
print('  深度:', description_analysis["depth"])
print('  孔位置:', description_analysis["hole_positions"])
print('  描述:', description_analysis["description"])

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
with open("test_deepseek_comparison.nc", "w", encoding="utf-8") as f:
    f.write(nc_program)
print("\nNC程序已保存到: test_deepseek_comparison.nc")
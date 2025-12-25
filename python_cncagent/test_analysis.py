import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.modules.material_tool_matcher import analyze_user_description

# Test the user description analysis
user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0Y-30. X94.0Y90. X94.0Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"

print("Analyzing user description:")
print(f"Input: {user_description}")
print()

result = analyze_user_description(user_description)
print("Result:")
for key, value in result.items():
    print(f"  {key}: {value}")
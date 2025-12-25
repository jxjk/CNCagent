"""
测试优化后的AI提示词对目标描述的解析效果
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.ai_driven_generator import AIDrivenCNCGenerator
from src.modules.material_tool_matcher import analyze_user_description

def test_optimized_prompt():
    """测试优化后的提示词效果"""
    print("测试优化后的AI提示词对沉孔加工描述的解析效果")
    print("="*60)
    
    # 目标用户描述
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0Y-30. X94.0Y90. X94.0Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
    
    print(f"用户描述: {user_description}")
    print()
    
    # 测试AI驱动的解析
    print("1. AI驱动解析结果:")
    ai_generator = AIDrivenCNCGenerator()
    requirements = ai_generator.parse_user_requirements(user_description)
    
    print(f"   加工类型: {requirements.processing_type}")
    print(f"   加工深度: {requirements.depth}")
    print(f"   孔位置: {requirements.hole_positions}")
    print(f"   刀具直径: {requirements.tool_diameters}")
    print(f"   材料: {requirements.material}")
    print(f"   特殊要求: {requirements.special_requirements}")
    print()
    
    # 测试规则匹配解析
    print("2. 规则匹配解析结果:")
    analysis_result = analyze_user_description(user_description)
    
    print(f"   加工类型: {analysis_result.get('processing_type', 'N/A')}")
    print(f"   刀具要求: {analysis_result.get('tool_required', 'N/A')}")
    print(f"   深度: {analysis_result.get('depth', 'N/A')}")
    print(f"   进给率: {analysis_result.get('feed_rate', 'N/A')}")
    print(f"   主轴转速: {analysis_result.get('spindle_speed', 'N/A')}")
    print(f"   材料: {analysis_result.get('material', 'N/A')}")
    print(f"   精度: {analysis_result.get('precision', 'N/A')}")
    print(f"   孔位置: {analysis_result.get('hole_positions', 'N/A')}")
    print(f"   参考点: {analysis_result.get('reference_points', 'N/A')}")
    print(f"   孔数量: {analysis_result.get('hole_count', 'N/A')}")
    
    # 检查是否提取到沉孔的内外径
    if 'outer_diameter' in analysis_result:
        print(f"   沉孔外径: {analysis_result['outer_diameter']}")
    if 'inner_diameter' in analysis_result:
        print(f"   沉孔内径: {analysis_result['inner_diameter']}")
    
    print()
    print("3. 解析准确性评估:")
    
    # 评估解析结果
    expected_processing_type = 'counterbore'
    expected_hole_count = 3
    expected_outer_diameter = 22.0
    expected_inner_diameter = 14.5
    expected_depth = 20.0
    expected_positions = [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    
    ai_processing_type = requirements.processing_type
    rule_processing_type = analysis_result.get('processing_type', '')
    
    print(f"   AI解析加工类型正确: {ai_processing_type == expected_processing_type}")
    print(f"   规则解析加工类型正确: {rule_processing_type == expected_processing_type}")
    print(f"   孔数量正确: {analysis_result.get('hole_count', 0) == expected_hole_count}")
    
    # 检查内外径
    has_outer_diameter = 'outer_diameter' in analysis_result and analysis_result['outer_diameter'] == expected_outer_diameter
    has_inner_diameter = 'inner_diameter' in analysis_result and analysis_result['inner_diameter'] == expected_inner_diameter
    print(f"   沉孔外径正确: {has_outer_diameter}")
    print(f"   沉孔内径正确: {has_inner_diameter}")
    
    print(f"   沉孔深度正确: {analysis_result.get('depth', 0) == expected_depth}")
    
    # 检查孔位置
    hole_positions = analysis_result.get('hole_positions', [])
    positions_correct = len(hole_positions) == len(expected_positions)
    for i, pos in enumerate(hole_positions):
        if i < len(expected_positions):
            expected_pos = expected_positions[i]
            pos_correct = abs(pos[0] - expected_pos[0]) < 0.1 and abs(pos[1] - expected_pos[1]) < 0.1
            positions_correct = positions_correct and pos_correct
    
    print(f"   孔位置正确: {positions_correct}")
    
    print()
    print("测试完成!")

if __name__ == "__main__":
    test_optimized_prompt()
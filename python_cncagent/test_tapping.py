"""
测试螺纹孔加工功能
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_tapping_process():
    """测试螺纹孔加工流程"""
    print("开始测试螺纹孔加工功能...")
    
    # 创建模拟特征数据 - 圆形特征代表需要加工螺纹孔的位置
    features = [
        {
            "shape": "circle",
            "center": (100.0, 100.0),  # X=100, Y=100
            "radius": 5.0,
            "dimensions": (10.0, 10.0),
            "area": 78.5,
            "contour": np.array([[[95, 95]], [[105, 95]], [[105, 105]], [[95, 105]]]),
            "bounding_box": (95, 95, 10, 10)
        },
        {
            "shape": "circle",
            "center": (200.0, 150.0),  # X=200, Y=150
            "radius": 5.0,
            "dimensions": (10.0, 10.0),
            "area": 78.5,
            "contour": np.array([[[195, 145]], [[205, 145]], [[205, 155]], [[195, 155]]]),
            "bounding_box": (195, 145, 10, 10)
        }
    ]
    
    # 用户描述：要求进行M10螺纹加工，深度14mm
    user_description = "M10螺纹加工，深度为贯穿14mm左右。长边与X轴平行，原点为正视图的左下角。考虑用点孔、钻孔、攻丝3把刀加工。"
    print(f"用户描述: {user_description}")
    
    try:
        print("\n正在分析用户描述...")
        description_analysis = analyze_user_description(user_description)
        print(f"分析结果: {description_analysis}")
        
        print("\n正在生成NC程序...")
        nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
        print("\n生成的NC程序:")
        print("="*50)
        print(nc_program)
        print("="*50)
        
        # 检查生成的NC程序是否包含螺纹加工的关键步骤
        lines = nc_program.split('\n')
        has_center_drilling = any('T1' in line and ('点孔' in line or 'center' in line.lower()) for line in lines)
        has_drilling = any('T2' in line and ('钻孔' in line or 'drill' in line.lower()) for line in lines)
        has_tapping = any('T3' in line and ('攻丝' in line or 'tapping' in line.lower()) for line in lines)
        has_hole_positions = any('X' in line and 'Y' in line and ('点孔' in line or '钻孔' in line or '攻丝' in line) for line in lines)
        
        print(f"\n验证结果:")
        print(f"  - 包含点孔工艺: {has_center_drilling}")
        print(f"  - 包含钻孔工艺: {has_drilling}")
        print(f"  - 包含攻丝工艺: {has_tapping}")
        print(f"  - 包含孔位置信息: {has_hole_positions}")
        
        # 额外检查是否包含三个步骤的标记
        step1_count = nc_program.count("--- 第一步")
        step2_count = nc_program.count("--- 第二步")
        step3_count = nc_program.count("--- 第三步")
        print(f"  - 包含第一步（点孔）: {step1_count > 0}")
        print(f"  - 包含第二步（钻孔）: {step2_count > 0}")
        print(f"  - 包含第三步（攻丝）: {step3_count > 0}")
        print(f"  - 总共 {step1_count + step2_count + step3_count}/3 个加工步骤")
        
        # 检查是否包含所有孔的位置信息
        hole_count = len(features)
        position_count = 0
        for feature in features:
            center_x, center_y = feature["center"]
            # 检查每个孔的位置是否在代码中被多次提及（对应三个加工步骤）
            pos_mentions = nc_program.count(f"X{center_x:.1f}") + nc_program.count(f"X{center_x:.3f}")
            if pos_mentions >= 3:  # 每个孔应该在三个步骤中都出现
                position_count += 1
        print(f"  - 所有 {hole_count} 个孔的位置信息都包含在内: {position_count == hole_count}")
        
        # 保存生成的NC程序到文件
        output_path = "test_output.nc"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(nc_program)
        print(f"\nNC程序已保存到: {output_path}")
            
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tapping_process()
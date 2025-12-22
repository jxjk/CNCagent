"""
最终验证测试 - 模拟用户实际使用场景
"""
import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.feature_definition import identify_features
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description

def test_complete_workflow():
    """测试完整的CNC Agent工作流程"""
    print("开始完整工作流程测试...")
    print("="*60)
    
    # 1. 模拟从图像中识别特征
    print("1. 测试特征识别...")
    # 创建一个模拟图像，包含几个圆形（代表需要加工的孔）
    img = np.zeros((300, 300), dtype=np.uint8)
    # 添加几个圆形特征
    cv2 = __import__('cv2')
    cv2.circle(img, (100, 100), 10, 255, -1)  # 圆形1
    cv2.circle(img, (200, 150), 12, 255, -1)  # 圆形2
    cv2.circle(img, (150, 200), 8, 255, -1)   # 圆形3
    
    features = identify_features(img)
    print(f"   ✅ 识别到 {len(features)} 个特征")
    for i, feature in enumerate(features):
        print(f"     特征 {i+1}: {feature['shape']}, 中心({feature['center'][0]:.1f}, {feature['center'][1]:.1f}), 置信度{feature['confidence']:.2f}")
    
    # 2. 分析用户描述
    print("\n2. 测试用户描述分析...")
    user_description = "M10螺纹加工，深度为贯穿14mm左右。长边与X轴平行，原点为正视图的左下角。考虑用点孔、钻孔、攻丝3把刀加工。"
    description_analysis = analyze_user_description(user_description)
    print(f"   ✅ 用户描述分析完成")
    print(f"     加工类型: {description_analysis['processing_type']}")
    print(f"     深度: {description_analysis['depth']}")
    print(f"     刀具: {description_analysis['tool_required']}")
    
    # 3. 生成NC代码
    print("\n3. 测试NC代码生成...")
    nc_program = generate_fanuc_nc(features, description_analysis, scale=1.0)
    print("   ✅ NC代码生成完成")
    
    # 4. 验证生成的代码是否符合要求
    print("\n4. 验证生成的NC代码...")
    lines = nc_program.split('\n')
    
    # 检查关键元素
    has_program_start = any('O0001' in line for line in lines)
    has_units = any('G21' in line for line in lines)
    has_absolute_coord = any('G90' in line for line in lines)
    has_program_end = any('M30' in line for line in lines)
    
    # 检查三步工艺
    has_t1_tapping = any('T1' in line and '点孔' in line for line in lines)
    has_t2_drilling = any('T2' in line and '钻孔' in line for line in lines) 
    has_t3_tapping = any('T3' in line and '攻丝' in line for line in lines)
    
    # 检查孔位置是否在所有步骤中都出现
    hole_positions_mentioned = 0
    for feature in features:
        center_x, center_y = feature['center']
        # 计算该孔位置在代码中被提及的次数（应该在3个步骤中都出现）
        pos_mentions = sum(1 for line in lines if f"X{center_x:.3f}" in line or f"Y{center_y:.3f}" in line)
        if pos_mentions >= 3:  # 每个孔应该在三个步骤中都出现
            hole_positions_mentioned += 1
    
    print(f"   ✅ 包含程序开始标记: {has_program_start}")
    print(f"   ✅ 包含单位设定 (G21): {has_units}")
    print(f"   ✅ 包含绝对坐标设定 (G90): {has_absolute_coord}")
    print(f"   ✅ 包含程序结束标记 (M30): {has_program_end}")
    print(f"   ✅ 包含点孔工艺 (T1): {has_t1_tapping}")
    print(f"   ✅ 包含钻孔工艺 (T2): {has_t2_drilling}")
    print(f"   ✅ 包含攻丝工艺 (T3): {has_t3_tapping}")
    print(f"   ✅ 所有 {len(features)} 个孔都在三个步骤中被加工: {hole_positions_mentioned == len(features)}")
    print(f"   ✅ 代码总行数: {len(lines)}")
    
    # 5. 检查关键螺纹加工指令
    has_g84_tapping = any('G84' in line for line in lines)  # 攻丝循环
    has_m04_reverse = any('M04' in line for line in lines)  # 主轴反转（攻丝后退刀）
    print(f"   ✅ 包含攻丝循环指令 (G84): {has_g84_tapping}")
    print(f"   ✅ 包含主轴反转指令 (M04): {has_m04_reverse}")
    
    print("\n"+"="*60)
    print("完整工作流程测试结果:")
    
    all_checks = [
        has_program_start, has_units, has_absolute_coord, has_program_end,
        has_t1_tapping, has_t2_drilling, has_t3_tapping,
        hole_positions_mentioned == len(features),
        has_g84_tapping, has_m04_reverse
    ]
    
    if all(all_checks):
        print("🎉 完整工作流程测试通过！所有功能正常工作。")
        print("\n实现的功能：")
        print("- ✅ 几何特征识别（圆形孔位检测）")
        print("- ✅ 用户描述理解（螺纹加工需求）")
        print("- ✅ 三步螺纹加工工艺（点孔→钻孔→攻丝）")
        print("- ✅ 多刀具管理（T1中心钻，T2钻头，T3丝锥）")
        print("- ✅ 孔位置精确定位（所有孔在三个步骤中都被加工）")
        print("- ✅ 完整的FANUC G代码生成")
        print("- ✅ 安全操作（加工后抬刀、主轴停止）")
        print("- ✅ 螺纹加工专用指令（G84攻丝循环，M04主轴反转）")
    else:
        failed_checks = [i for i, check in enumerate(all_checks) if not check]
        print(f"⚠️  测试未完全通过，{len(failed_checks)} 项检查失败")
        # 这里可以根据失败的检查项提供更详细的反馈
        
    print("\n生成的NC程序示例（前20行）:")
    print("-"*40)
    for i, line in enumerate(lines[:20]):
        print(line)
        if i == 19 and len(lines) > 20:
            print("...")
    print("-"*40)
    
    # 保存完整的NC程序到文件
    with open("final_test_output.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    print(f"\n完整NC程序已保存到: final_test_output.nc")
    print(f"程序总行数: {len(lines)} 行")
    
    return all(all_checks)

def main():
    """运行最终验证测试"""
    try:
        import cv2  # 确保需要的库可用
        success = test_complete_workflow()
        return success
    except ImportError:
        print("缺少必要的依赖库cv2，无法运行完整测试")
        print("请运行: pip install opencv-python")
        return False

if __name__ == "__main__":
    main()

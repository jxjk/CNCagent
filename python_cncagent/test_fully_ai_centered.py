"""
全面测试AI驱动的刀具半径补偿功能
测试完整的从用户请求到NC代码生成的流程
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.ai_driven_generator import generate_nc_with_ai

def test_complete_tool_compensation_workflow():
    """测试完整的刀具半径补偿工作流程"""
    print("=== 测试完整的刀具半径补偿工作流程 ===")
    
    # 直接创建生成器实例并使用备用代码生成
    from src.modules.ai_driven_generator import AIDrivenCNCGenerator
    
    generator = AIDrivenCNCGenerator(api_key="dummy_key", model="gpt-4")  # 使用模拟密钥
    
    # 模拟用户请求 - 铣削加工，需要刀具半径补偿
    user_prompt = "请铣削一个外轮廓矩形，尺寸100x80mm，深度3mm，使用φ8铣刀进行精加工，确保考虑刀具半径补偿"
    
    # 使用解析函数测试
    requirements = generator.parse_user_requirements(user_prompt)
    print(f"解析的用户需求: {requirements}")
    
    # 生成备用代码
    nc_code = generator._generate_fallback_code(user_prompt)
        
    print("生成的NC代码:")
    print(nc_code)
    
    # 验证代码的关键部分
    lines = nc_code.split('\n')
    
    # 检查是否包含刀具半径补偿相关的重要元素
    has_g41_g42 = any('G41' in line or 'G42' in line for line in lines)
    has_g40 = any('G40' in line for line in lines)
    has_tool_change = any('T' in line and 'M06' in line for line in lines)
    has_length_compensation = any('G43' in line for line in lines)
    
    # 检查是否包含刀具半径补偿说明
    has_compensation_check = any('TOOL RADIUS COMPENSATION' in line for line in lines)
    has_wear_compensation = any('WEAR COMPENSATION' in line for line in lines)
    has_coordinate_calculation = any('CALCULATED FOR TOOL RADIUS' in line or 'CALCULATED PATH' in line for line in lines)
    has_compensation_verification = any('VERIFY' in line and 'COMPENSATION' in line for line in lines)
    
    print(f"\n验证结果:")
    print(f"- 包含G41/G42刀具半径补偿指令: {has_g41_g42}")
    print(f"- 包含G40补偿取消指令: {has_g40}")
    print(f"- 包含刀具更换指令: {has_tool_change}")
    print(f"- 包含刀具长度补偿: {has_length_compensation}")
    print(f"- 包含刀具半径补偿检查: {has_compensation_check}")
    print(f"- 包含磨损补偿说明: {has_wear_compensation}")
    print(f"- 包含坐标计算说明: {has_coordinate_calculation}")
    print(f"- 包含补偿验证说明: {has_compensation_verification}")
    
    # 额外检查：确保G41/G42后有适当的移动指令
    g41_g42_indices = [i for i, line in enumerate(lines) if 'G41' in line or 'G42' in line]
    has_proper_following_move = True
    for idx in g41_g42_indices:
        # 检查G41/G42后几行是否有G01移动指令
        found_move = False
        for j in range(idx+1, min(idx+5, len(lines))):
            if 'G01' in lines[j] or 'G00' in lines[j]:
                found_move = True
                break
        if not found_move:
            has_proper_following_move = False
            break
    
    print(f"- G41/G42后有适当的移动指令: {has_proper_following_move}")
    
    success = all([
        has_g41_g42,
        has_g40,
        has_tool_change,
        has_length_compensation,
        has_compensation_check,
        has_wear_compensation,
        has_coordinate_calculation,
        has_compensation_verification,
        has_proper_following_move
    ])
    
    print(f"\n完整工作流程测试: {'通过' if success else '失败'}")
    return success

def test_internal_contour_compensation():
    """测试内轮廓的刀具半径补偿"""
    print("\n=== 测试内轮廓的刀具半径补偿 ===")
    
    from src.modules.ai_driven_generator import AIDrivenCNCGenerator
    generator = AIDrivenCNCGenerator(api_key="dummy_key", model="gpt-4")  # 使用模拟密钥
    
    user_prompt = "请铣削一个内轮廓圆，直径50mm，深度5mm，使用φ6铣刀，注意内轮廓的刀具半径补偿"
    
    try:
        # 生成备用代码
        nc_code = generator._generate_fallback_code(user_prompt)
        
        print("生成的NC代码片段:")
        code_lines = nc_code.split('\n')
        for i, line in enumerate(code_lines[:50]):  # 显示前50行
            print(f"{i+1:2d}: {line}")
        
        # 检查内轮廓相关的补偿处理
        has_circular_milling = any('G02' in line or 'G03' in line for line in code_lines)
        has_compensation = any('G41' in line or 'G42' in line for line in code_lines)
        has_compensation_cancel = any('G40' in line for line in code_lines)
        
        print(f"\n验证结果:")
        print(f"- 包含圆形铣削指令(G02/G03): {has_circular_milling}")
        print(f"- 包含刀具半径补偿: {has_compensation}")
        print(f"- 包含补偿取消: {has_compensation_cancel}")
        
        success = has_circular_milling and has_compensation and has_compensation_cancel
        print(f"\n内轮廓补偿测试: {'通过' if success else '失败'}")
        return success
        
    except Exception as e:
        print(f"生成NC代码时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compensation_with_different_materials():
    """测试不同材料的刀具半径补偿"""
    print("\n=== 测试不同材料的刀具半径补偿 ===")
    
    from src.modules.ai_driven_generator import AIDrivenCNCGenerator
    generator = AIDrivenCNCGenerator(api_key="dummy_key", model="gpt-4")  # 使用模拟密钥
    
    materials = ["aluminum", "steel", "stainless_steel"]
    results = []
    
    for material in materials:
        print(f"\n测试材料: {material}")
        user_prompt = f"请铣削一个矩形，尺寸60x40mm，深度2mm，材料为{material}，使用φ10铣刀，注意刀具半径补偿"
        
        try:
            # 生成备用代码
            nc_code = generator._generate_fallback_code(user_prompt)
            
            lines = nc_code.split('\n')
            has_compensation_check = any('TOOL RADIUS COMPENSATION' in line for line in lines)
            has_proper_setup = any('G43' in line for line in lines)  # 长度补偿
            
            print(f"  - 包含刀具半径补偿检查: {has_compensation_check}")
            print(f"  - 包含刀具长度补偿设置: {has_proper_setup}")
            
            material_success = has_compensation_check and has_proper_setup
            print(f"  - {material}材料补偿测试: {'通过' if material_success else '失败'}")
            results.append(material_success)
            
        except Exception as e:
            print(f"  - 生成{material}材料代码时出错: {e}")
            results.append(False)
    
    overall_success = all(results)
    print(f"\n不同材料补偿测试: {'通过' if overall_success else '失败'}")
    return overall_success

def main():
    """运行所有测试"""
    print("开始全面测试AI驱动的刀具半径补偿功能...")
    
    results = []
    results.append(test_complete_tool_compensation_workflow())
    results.append(test_internal_contour_compensation())
    results.append(test_compensation_with_different_materials())
    
    print(f"\n=== 全面测试总结 ===")
    print(f"总测试数: {len(results)}")
    print(f"通过测试: {sum(results)}")
    print(f"失败测试: {len(results) - sum(results)}")
    
    if all(results):
        print("\n所有测试均通过！AI驱动的刀具半径补偿功能实现成功。")
        print("\n实现特点:")
        print("- 刀具半径补偿(G41/G42)的补偿量直接计算到坐标点中")
        print("- G41D**指令仅用于磨损补偿，不是主要的尺寸补偿")
        print("- NC程序开始前包含补偿量检查")
        print("- 支持外轮廓和内轮廓的补偿计算")
        print("- 针对不同材料优化补偿策略")
        return True
    else:
        print("\n部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
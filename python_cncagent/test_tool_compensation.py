"""
测试刀具半径补偿功能
验证AI驱动的代码生成是否正确处理刀具半径补偿
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.ai_driven_generator import AIDrivenCNCGenerator
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.prompt_builder import prompt_builder


def test_tool_radius_compensation_in_milling():
    """测试铣削中的刀具半径补偿"""
    print("=== 测试铣削中的刀具半径补偿 ===")
    
    # 模拟特征数据 - 矩形特征
    features = [
        {
            "shape": "rectangle",
            "center": [50.0, 50.0],
            "dimensions": [40.0, 30.0],
            "confidence": 0.95
        }
    ]
    
    # 描述分析结果
    description_analysis = {
        "processing_type": "milling",
        "tool_diameter": 10.0,  # 10mm铣刀
        "depth": 5.0,
        "material": "aluminum"
    }
    
    # 生成NC代码
    nc_code = generate_fanuc_nc(features, description_analysis)
    
    print("生成的NC代码片段:")
    print("\n".join(nc_code.split('\n')[:50]))  # 显示前50行
    
    # 验证代码中是否包含刀具半径补偿相关指令
    has_g41_g42 = bool(re.search(r'G4[12]', nc_code))
    has_g40 = 'G40' in nc_code
    has_tool_compensation_check = 'TOOL RADIUS COMPENSATION' in nc_code
    has_wear_compensation_note = 'WEAR COMPENSATION' in nc_code
    
    print(f"\n验证结果:")
    print(f"- 包含G41/G42刀具半径补偿指令: {has_g41_g42}")
    print(f"- 包含G40补偿取消指令: {has_g40}")
    print(f"- 包含刀具半径补偿检查说明: {has_tool_compensation_check}")
    print(f"- 包含磨损补偿说明: {has_wear_compensation_note}")
    
    # 检查是否正确计算补偿到坐标点
    has_calculated_path = 'CALCULATED FOR TOOL RADIUS' in nc_code or 'CALCULATED PATH' in nc_code
    print(f"- 包含计算路径说明: {has_calculated_path}")
    
    success = all([
        has_g41_g42,
        has_g40,
        has_tool_compensation_check,
        has_wear_compensation_note,
        has_calculated_path
    ])
    
    print(f"\n铣削刀具半径补偿测试: {'通过' if success else '失败'}")
    return success


def test_ai_prompt_includes_compensation():
    """测试AI提示词是否包含刀具半径补偿信息"""
    print("\n=== 测试AI提示词中的刀具半径补偿 ===")
    
    # 构建提示词
    prompt = prompt_builder.build_optimized_prompt(
        user_description="请铣削一个矩形，尺寸100x50mm，深度5mm",
        material="aluminum",
        precision_requirement="General"
    )
    
    # 检查提示词中是否包含刀具半径补偿相关信息
    has_compensation_info = '刀具半径补偿' in prompt or 'tool radius compensation' in prompt
    has_coordinate_calculation = '计算到坐标点' in prompt or 'coordinate' in prompt
    has_wear_compensation = '磨损补偿' in prompt or 'wear' in prompt
    
    print(f"提示词长度: {len(prompt)} 字符")
    print(f"- 包含刀具半径补偿信息: {has_compensation_info}")
    print(f"- 包含坐标计算信息: {has_coordinate_calculation}")
    print(f"- 包含磨损补偿信息: {has_wear_compensation}")
    
    success = all([has_compensation_info, has_coordinate_calculation, has_wear_compensation])
    print(f"\nAI提示词刀具半径补偿测试: {'通过' if success else '失败'}")
    
    return success


def test_ai_driven_generator_with_compensation():
    """测试AI驱动生成器中的刀具半径补偿"""
    print("\n=== 测试AI驱动生成器中的刀具半径补偿 ===")
    
    # 创建生成器实例
    generator = AIDrivenCNCGenerator()
    
    # 测试铣削请求
    user_prompt = "请铣削一个矩形，尺寸100x50mm，深度5mm，使用φ10铣刀进行精加工"
    nc_code = generator._generate_fallback_code(user_prompt)
    
    # 检查生成的代码是否包含刀具半径补偿检查
    has_compensation_check = 'TOOL RADIUS COMPENSATION' in nc_code
    has_verify_compensation = 'VERIFY' in nc_code and 'COMPENSATION' in nc_code
    has_wear_compensation = 'WEAR COMPENSATION' in nc_code
    
    print(f"生成的NC代码片段:")
    print("\n".join(nc_code.split('\n')[:30]))  # 显示前30行
    
    print(f"\n验证结果:")
    print(f"- 包含刀具半径补偿检查: {has_compensation_check}")
    print(f"- 包含补偿验证说明: {has_verify_compensation}")
    print(f"- 包含磨损补偿说明: {has_wear_compensation}")
    
    success = all([has_compensation_check, has_verify_compensation, has_wear_compensation])
    print(f"\nAI驱动生成器刀具半径补偿测试: {'通过' if success else '失败'}")
    
    return success


def main():
    """运行所有测试"""
    print("开始测试刀具半径补偿功能...")
    
    results = []
    results.append(test_tool_radius_compensation_in_milling())
    results.append(test_ai_prompt_includes_compensation())
    results.append(test_ai_driven_generator_with_compensation())
    
    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {len(results)}")
    print(f"通过测试: {sum(results)}")
    print(f"失败测试: {len(results) - sum(results)}")
    
    if all(results):
        print("所有测试均通过！刀具半径补偿功能实现成功。")
        return True
    else:
        print("部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
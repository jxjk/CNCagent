"""
测试切削工艺优化功能
验证新添加的切削参数优化和刀具路径优化功能
"""
import sys
import os
# 添加项目路径以导入模块
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.modules.cutting_optimization import cutting_optimizer
from src.modules.material_tool_matcher import _extract_workpiece_dimensions, analyze_user_description
from src.modules.gcode_generation import generate_fanuc_nc

def test_cutting_optimization():
    """测试切削工艺优化功能"""
    print("=== 测试切削工艺优化功能 ===")
    
    # 测试1: 铣削参数优化
    print("\n1. 测试铣削参数优化:")
    params = cutting_optimizer.calculate_optimal_cutting_parameters(
        material="aluminum",
        tool_type="face_mill",
        tool_diameter=63.0,  # φ63面铣刀
        workpiece_dimensions=(400, 300, 50),  # 长400, 宽300, 高50
        operation_type="face_milling"
    )
    print(f"   材料: aluminum")
    print(f"   刀具: φ{params['tool_properties']['max_rpm']}面铣刀")
    print(f"   优化后参数:")
    print(f"   - 主轴转速: {params['spindle_speed']} rpm")
    print(f"   - 进给速度: {params['feed_rate']} mm/min")
    print(f"   - 切削深度: {params['depth_of_cut']} mm")
    print(f"   - 步距: {params['stepover']} mm")
    
    # 验证参数
    errors = cutting_optimizer.validate_cutting_parameters(
        params, 63.0, (400, 300, 50)
    )
    if errors:
        print(f"   参数验证错误: {errors}")
    else:
        print(f"   参数验证: 通过")
    
    # 测试2: 钻孔参数优化
    print("\n2. 测试钻孔参数优化:")
    params = cutting_optimizer.calculate_optimal_cutting_parameters(
        material="aluminum",
        tool_type="drill_bit",
        tool_diameter=12.0,  # φ12钻头
        workpiece_dimensions=(400, 300, 50),
        operation_type="drilling"
    )
    print(f"   材料: aluminum")
    print(f"   刀具: φ{params['tool_properties']['max_rpm']}钻头")
    print(f"   优化后参数:")
    print(f"   - 主轴转速: {params['spindle_speed']} rpm")
    print(f"   - 进给速度: {params['feed_rate']} mm/min")
    
    # 测试3: 刀具路径优化
    print("\n3. 测试刀具路径优化:")
    toolpath = cutting_optimizer.optimize_toolpath(
        feature_type="rectangle",
        feature_dimensions=(400, 300),  # 长400, 宽300
        tool_diameter=63.0,
        workpiece_dimensions=(400, 300, 50)
    )
    print(f"   特征类型: rectangle")
    print(f"   特征尺寸: 400x300")
    print(f"   刀具直径: 63.0")
    print(f"   生成路径段数: {len(toolpath)}")
    if toolpath:
        print(f"   第一段路径: {toolpath[0]}")

def test_workpiece_dimensions_extraction():
    """测试工件尺寸提取功能"""
    print("\n=== 测试工件尺寸提取功能 ===")
    
    # 测试各种工件尺寸描述格式
    test_cases = [
        "用加工中心铣削上平面尺寸长400宽300深2毫米。在工件中心钻个φ12的孔。注意",
        "工件尺寸400X300X20mm",
        "加工长宽高400X300X15",
        "平面尺寸800*600",
        "长500宽400厚度10",
    ]
    
    for i, description in enumerate(test_cases, 1):
        print(f"\n{i}. 测试描述: {description}")
        dimensions = _extract_workpiece_dimensions(description)
        if dimensions:
            print(f"   提取的尺寸: {dimensions}")
        else:
            print(f"   提取的尺寸: 未找到")

def test_full_workflow():
    """测试完整工作流程"""
    print("\n=== 测试完整工作流程 ===")
    
    # 模拟用户描述
    user_description = "用加工中心铣削上平面尺寸长400宽300深2毫米。在工件中心钻个φ12的孔。G54原点在工件中心毛坯上平面。材料为铝"
    
    print(f"用户描述: {user_description}")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    print(f"分析结果: {description_analysis}")
    
    # 检查是否提取到工件尺寸
    if "workpiece_dimensions" in description_analysis:
        print(f"工件尺寸: {description_analysis['workpiece_dimensions']}")
    else:
        print("未提取到工件尺寸")
    
    # 检查是否提取到材料信息
    if "material" in description_analysis:
        print(f"材料: {description_analysis['material']}")
    else:
        print("未提取到材料信息")

def test_gcode_with_optimization():
    """测试带优化功能的G代码生成"""
    print("\n=== 测试带优化功能的G代码生成 ===")
    
    # 创建一个模拟的矩形特征
    features = [{
        "shape": "rectangle",
        "center": (0, 0),  # G54原点在工件中心
        "dimensions": (400, 300),  # 长400, 宽300
        "length": 400,
        "width": 300
    }, {
        "shape": "circle",
        "center": (0, 0),  # 工件中心钻孔
        "dimensions": (12,),  # φ12的孔
        "radius": 6
    }]
    
    # 用户描述包含工件尺寸和材料信息
    description_analysis = {
        "processing_type": "milling",
        "tool_required": "end_mill",
        "depth": 2,
        "material": "aluminum",
        "workpiece_dimensions": (400, 300, 50),  # 长400, 宽300, 高50
        "tool_diameter": 63.0,  # 使用φ63面铣刀
        "description": "用加工中心铣削上平面尺寸长400宽300深2毫米。在工件中心钻个φ12的孔。G54原点在工件中心毛坯上平面。"
    }
    
    try:
        nc_code = generate_fanuc_nc(features, description_analysis)
        print("成功生成G代码，前20行:")
        lines = nc_code.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"  {line}")
        if len(lines) > 20:
            print(f"  ... (共{len(lines)}行)")
    except Exception as e:
        print(f"生成G代码时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试CNC Agent的切削工艺优化功能...")
    
    test_cutting_optimization()
    test_workpiece_dimensions_extraction()
    test_full_workflow()
    test_gcode_with_optimization()
    
    print("\n=== 测试完成 ===")

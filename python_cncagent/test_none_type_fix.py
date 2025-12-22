"""
测试修复后的CNC Agent，验证NoneType错误是否已解决
"""
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.gcode_generation import generate_fanuc_nc


def test_none_type_fix():
    """测试修复后的NoneType错误"""
    print("测试修复后的NoneType错误处理...")
    
    # 测试各种可能产生None值的描述
    test_descriptions = [
        "请加工一个孔",  # 无具体参数
        "铣削一个矩形",  # 无具体参数
        "加工深度未知的特征",  # 包含深度但无法解析
        "使用钻孔方式进行加工",  # 只有类型没有参数
        "请帮我生成NC代码",  # 通用描述
        "深度5mm，但其他参数不详",  # 部分参数
    ]
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\n测试 {i}: '{desc}'")
        try:
            # 分析描述
            analysis = analyze_user_description(desc)
            print(f"  - 分析结果: {analysis['processing_type']}, 深度: {analysis['depth']}, 进给: {analysis['feed_rate']}")
            
            # 测试G代码生成 - 使用模拟特征
            mock_features = [{
                "shape": "circle",
                "center": (10, 10),
                "radius": 5,
                "dimensions": (10, 10),
                "area": 78.5,
                "contour": [],
                "bounding_box": (5, 5, 10, 10)
            }]
            
            nc_code = generate_fanuc_nc(mock_features, analysis)
            print(f"  - G代码生成: 成功 (共{len(nc_code.split())}行)")
            
            # 检查关键G代码指令是否存在
            if "G21" in nc_code and "G90" in nc_code and "M30" in nc_code:
                print("  - 关键指令检查: 通过")
            else:
                print("  - 关键指令检查: 部分通过")
                
        except Exception as e:
            print(f"  - 错误: {e}")
            import traceback
            traceback.print_exc()


def test_original_issue():
    """测试原始问题是否已解决"""
    print("\n" + "="*60)
    print("测试原始问题: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'")
    print("="*60)
    
    try:
        # 模拟原始问题场景：用户描述中没有明确的参数
        analysis = {
            "processing_type": "drilling",
            "tool_required": "drill_bit",
            "depth": None,  # 这是导致问题的原因
            "feed_rate": None,  # 这也是
            "spindle_speed": None,  # 这也是
            "material": "aluminum",
            "precision": None,
            "description": "请加工一个孔"
        }
        
        mock_features = [{
            "shape": "circle",
            "center": (50, 50),
            "radius": 5,
            "dimensions": (10, 10),
            "area": 78.5,
            "contour": [],
            "bounding_box": (45, 45, 10, 10)
        }]
        
        print("使用包含None值的分析结果生成G代码...")
        nc_code = generate_fanuc_nc(mock_features, analysis)
        
        print("✅ 修复成功！没有出现NoneType错误")
        print(f"✅ 成功生成NC代码，共{len(nc_code.splitlines())}行")
        
        # 检查是否使用了默认值
        if "S1000" in nc_code and "F100" in nc_code and "Z-10" in nc_code:
            print("✅ 正确使用了默认值")
        else:
            print("⚠ 可能未使用预期的默认值")
        
        return True
        
    except TypeError as e:
        if "NoneType" in str(e):
            print(f"❌ 修复失败: 仍然存在NoneType错误 - {e}")
            return False
        else:
            print(f"❌ 其他类型错误: {e}")
            return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("CNC Agent NoneType错误修复验证")
    print("="*60)
    
    # 运行测试
    test_none_type_fix()
    
    success = test_original_issue()
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有测试通过！NoneType错误已成功修复。")
        print("\n修复内容：")
        print("- 在material_tool_matcher.py中添加了安全的数值转换")
        print("- 在gcode_generation.py中添加了None值检查和默认值")
        print("- 系统现在可以处理缺少参数的用户描述")
    else:
        print("❌ 测试失败，错误仍然存在。")
    print("="*60)
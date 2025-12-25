"""
测试用户描述优先级
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.unified_generator import unified_generator

def test_user_priority():
    """测试用户描述的优先级"""
    print("测试用户描述优先级...")
    
    # 测试1: 沉孔加工描述
    print("\n测试1: 沉孔加工")
    description = "请加工3个φ22沉孔，深度20mm，材料为铝"
    nc_code = unified_generator.generate_from_description_only(description, "Aluminum")
    print("描述:", description)
    print("生成的NC代码包含沉孔加工步骤:", "COUNTERBORE" in nc_code.upper() or "沉孔" in nc_code)
    
    # 测试2: 钻孔加工描述
    print("\n测试2: 钻孔加工")
    description = "请钻5个φ10的孔，深度15mm"
    nc_code = unified_generator.generate_from_description_only(description, "Steel")
    print("描述:", description)
    print("生成的NC代码包含钻孔加工步骤:", "DRILL" in nc_code.upper())
    
    # 测试3: 矩形铣削描述
    print("\n测试3: 矩形铣削")
    description = "请铣削一个100mm x 50mm的矩形，深度5mm"
    nc_code = unified_generator.generate_from_description_only(description, "Aluminum")
    print("描述:", description)
    print("生成的NC代码包含铣削加工步骤:", "MILL" in nc_code.upper())
    
    # 测试4: 攻丝加工描述
    print("\n测试4: 攻丝加工")
    description = "请加工3个M10螺纹孔，深度14mm"
    nc_code = unified_generator.generate_from_description_only(description, "Aluminum")
    print("描述:", description)
    print("生成的NC代码包含攻丝加工步骤:", "TAPPING" in nc_code.upper() or "G84" in nc_code)

if __name__ == "__main__":
    test_user_priority()
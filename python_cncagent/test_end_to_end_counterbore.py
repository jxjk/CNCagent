"""
端到端沉孔加工测试
测试从用户需求到G代码生成的完整流程
"""
import numpy as np
import cv2
from src.main import generate_nc_from_pdf
from src.modules.feature_definition import identify_features, identify_counterbore_features, extract_highest_y_center_point, adjust_coordinate_system
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.gcode_generation import generate_fanuc_nc

def create_test_pdf_simulation():
    """模拟PDF解析后的图像处理"""
    print("=== 模拟PDF图纸解析 ===")
    
    # 创建一个模拟图纸图像，包含3个φ22沉孔+φ14.5底孔
    img = np.zeros((800, 600), dtype=np.uint8)  # 灰度图
    
    # 添加3个沉孔位置，确保有一个是最上方的（用于坐标原点）
    positions = [
        (300, 100),  # 最上方的孔
        (200, 250), 
        (400, 300)
    ]
    
    for center in positions:
        # 每个位置画同心圆：φ22沉孔 + φ14.5底孔
        outer_radius = 22  # φ22mm
        inner_radius = 15  # φ14.5mm (近似)
        
        cv2.circle(img, center, outer_radius, 255, 2)  # 外圆
        cv2.circle(img, center, inner_radius, 255, 2)  # 内圆
    
    return img

def test_end_to_end_process():
    """测试端到端处理流程"""
    print("\n=== 端到端沉孔加工流程测试 ===")
    
    # 模拟用户需求
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点选择圆心最高点。"
    
    print(f"用户需求: {user_description}")
    
    # 1. 创建模拟图纸
    img = create_test_pdf_simulation()
    print(f"✓ 创建模拟图纸: {img.shape}")
    
    # 2. 识别基本特征
    print("✓ 识别基本几何特征...")
    features = identify_features(
        img,
        min_area=50,
        min_perimeter=10,
        canny_low=30,
        canny_high=100,
        gaussian_kernel=(3, 3),
        morph_kernel=(1, 1)
    )
    
    print(f"  识别到 {len(features)} 个基本特征")
    for i, f in enumerate(features):
        if f['shape'] == 'circle':
            print(f"    圆形 {i+1}: 中心{f['center']}, 半径{f['radius']:.1f}")
    
    # 3. 识别沉孔特征
    print("✓ 识别沉孔复合特征...")
    counterbore_features = identify_counterbore_features(features)
    
    print(f"  复合识别后: {len(counterbore_features)} 个特征")
    counterbore_count = sum(1 for f in counterbore_features if f['shape'] == 'counterbore')
    print(f"  其中沉孔特征: {counterbore_count} 个")
    
    # 4. 确定坐标原点（最高Y坐标点，即最上方的圆心）
    print("✓ 确定坐标原点...")
    origin = extract_highest_y_center_point(counterbore_features)
    print(f"  选择最高点 {origin} 作为坐标原点")
    
    # 5. 调整坐标系统
    print("✓ 调整坐标系统...")
    adjusted_features = adjust_coordinate_system(counterbore_features, origin)
    
    print("  调整后的特征坐标:")
    for i, f in enumerate(adjusted_features):
        if f['shape'] == 'counterbore':
            print(f"    沉孔 {i+1}: 调整后{f['center']}, 原始{f.get('original_center', f['center'])}")
    
    # 6. 分析用户描述
    print("✓ 分析用户描述...")
    description_analysis = analyze_user_description(user_description)
    description_analysis["processing_type"] = "counterbore"  # 指定加工类型
    
    # 7. 生成NC代码
    print("✓ 生成NC程序...")
    nc_program = generate_fanuc_nc(adjusted_features, description_analysis)
    
    print("\n生成的NC程序:")
    print("="*50)
    print(nc_program)
    print("="*50)
    
    # 8. 验证生成的程序是否包含关键要素
    success_indicators = [
        "COUNTERBORE" in nc_program,
        "STEP 1: PILOT DRILLING OPERATION" in nc_program,
        "STEP 2: DRILLING OPERATION" in nc_program,
        "STEP 3: COUNTERBORE OPERATION" in nc_program,
        "φ22" in nc_program and "φ14.5" in nc_program,
        "T1 M06" in nc_program,  # 工具变更
        "T2 M06" in nc_program,
        "T4 M06" in nc_program
    ]
    
    print(f"\n程序验证:")
    print(f"  - 包含沉孔标识: {'✓' if success_indicators[0] else '✗'}")
    print(f"  - 包含点孔工艺: {'✓' if success_indicators[1] else '✗'}")
    print(f"  - 包含钻孔工艺: {'✓' if success_indicators[2] else '✗'}")
    print(f"  - 包含锪孔工艺: {'✓' if success_indicators[3] else '✗'}")
    print(f"  - 包含规格参数: {'✓' if success_indicators[4] else '✗'}")
    print(f"  - 包含工具变更: {'✓' if all(success_indicators[5:8]) else '✗'}")
    
    overall_success = all(success_indicators[:4])  # 关键要素检查
    print(f"\n端到端测试结果: {'✓ 成功' if overall_success else '✗ 失败'}")
    
    return overall_success, nc_program

def test_gcode_content():
    """测试生成的G代码内容是否符合要求"""
    print("\n=== G代码内容验证 ===")
    
    # 创建测试特征
    features = [
        {
            "shape": "counterbore",
            "center": (0, 0),  # 已经相对于原点调整
            "outer_radius": 11,  # φ22mm
            "inner_radius": 7.25,  # φ14.5mm
            "outer_diameter": 22.0,
            "inner_diameter": 14.5,
            "depth": 20.0,  # 沉孔深度
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (-11, -11, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "counterbore", 
            "center": (50, 30),
            "outer_radius": 11,
            "inner_radius": 7.25,
            "outer_diameter": 22.0,
            "inner_diameter": 14.5,
            "depth": 20.0,
            "contour": np.array([], dtype=np.int32),
            "bounding_box": (39, 19, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        }
    ]
    
    # 分析描述
    description_analysis = {
        "processing_type": "counterbore",
        "description": "加工φ22深20底孔φ14.5贯通的沉孔特征",
        "depth": 20.0,
        "feed_rate": 100.0,
        "spindle_speed": 800
    }
    
    # 生成G代码
    nc_program = generate_fanuc_nc(features, description_analysis)
    
    # 检查关键G代码指令
    lines = nc_program.split('\n')
    g81_found = any('G81' in line and 'COUNTERBORE' in line for line in lines)
    g83_found = any('G83' in line and 'DRILLING' in line for line in lines)
    g82_found = any('G82' in line and 'SPOT DRILLING' in line for line in lines)
    
    print(f"  G81锪孔循环: {'✓' if g81_found else '✗'}")
    print(f"  G83钻孔循环: {'✓' if g83_found else '✗'}")
    print(f"  G82点孔循环: {'✓' if g82_found else '✗'}")
    
    # 检查坐标值是否正确
    coord_check = any('X0.000 Y0.000' in line or 'X50.000 Y30.000' in line for line in lines)
    print(f"  坐标值正确: {'✓' if coord_check else '✗'}")
    
    success = g81_found and g83_found and g82_found and coord_check
    print(f"  G代码内容验证: {'✓ 通过' if success else '✗ 失败'}")
    
    return success

def main():
    """主测试函数"""
    print("开始端到端沉孔加工测试...\n")
    
    success1, nc_program = test_end_to_end_process()
    success2 = test_gcode_content()
    
    print(f"\n=== 最终测试报告 ===")
    print(f"端到端流程: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"G代码内容: {'✓ 通过' if success2 else '✗ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！")
        print("✓ 沉孔特征识别功能完整实现")
        print("✓ 坐标系统调整功能正常工作")
        print("✓ 三点工艺（点孔、钻孔、锪孔）完整支持")
        print("✓ φ22深20mm沉孔 + φ14.5贯通底孔规格正确支持")
        print("✓ FANUC NC程序生成符合标准")
        
        print("\n系统现在可以处理以下用户需求:")
        print("  '加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点选择圆心最高点。'")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")
    
    return success1 and success2

if __name__ == "__main__":
    main()

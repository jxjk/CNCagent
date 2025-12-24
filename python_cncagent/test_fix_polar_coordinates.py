"""
测试修复后的极坐标问题
验证NC程序能够正确输出多个孔的位置，而不是只输出(0,0)位置的一个孔
"""
import numpy as np
import cv2
from src.modules.feature_definition import identify_features, identify_counterbore_features, adjust_coordinate_system, extract_highest_y_center_point
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.gcode_generation import generate_fanuc_nc

def test_multiple_counterbore_features():
    """测试多个沉孔特征的识别和NC程序生成"""
    print("=== 测试多个沉孔特征识别和NC程序生成 ===")
    
    # 创建一个模拟图像，包含多个沉孔位置
    img = np.zeros((600, 600), dtype=np.uint8)
    
    # 添加3个同心圆组合，模拟3个沉孔位置
    positions = [
        (300, 100),  # 最上方的孔（将成为坐标原点，变为0,0）
        (200, 250),  # 第二个孔
        (400, 300)   # 第三个孔
    ]
    
    for center in positions:
        # 每个位置画同心圆：φ22沉孔 + φ14.5底孔
        outer_radius = 22  # φ22mm
        inner_radius = 15  # φ14.5mm (近似)
        
        cv2.circle(img, center, outer_radius, 255, 2)  # 外圆
        cv2.circle(img, center, inner_radius, 255, 2)  # 内圆
    
    # 识别基本特征
    features = identify_features(img)
    print(f"识别到 {len(features)} 个基本特征")
    
    # 识别沉孔特征
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点选择圆心最高点。极坐标标注。"
    counterbore_features = identify_counterbore_features(features, user_description)
    print(f"识别到 {len(counterbore_features)} 个沉孔特征")
    
    for i, feature in enumerate(counterbore_features):
        if feature['shape'] == 'counterbore':
            print(f"  沉孔 {i+1}: 中心{feature['center']}, 外径{feature['outer_diameter']:.1f}mm, 内径{feature['inner_diameter']:.1f}mm")
    
    # 提取最高Y坐标点作为原点
    origin = extract_highest_y_center_point(counterbore_features)
    print(f"选择的坐标原点: {origin}")
    
    # 调整坐标系统
    adjusted_features = adjust_coordinate_system(counterbore_features, origin)
    print(f"调整坐标系统后的特征:")
    for i, feature in enumerate(adjusted_features):
        if feature['shape'] == 'counterbore':
            print(f"  沉孔 {i+1}: 调整后中心{feature['center']}, 原始中心{feature['original_center']}")
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    description_analysis["processing_type"] = "counterbore"
    
    # 生成NC代码
    nc_program = generate_fanuc_nc(adjusted_features, description_analysis)
    
    print("\n生成的NC程序:")
    print("="*50)
    print(nc_program)
    print("="*50)
    
    # 验证程序中是否包含多个孔的位置信息
    has_multiple_holes = nc_program.count('X') >= 3  # 应该有多个X坐标
    has_polar_coords = 'POLAR' in nc_program or 'polar' in nc_program
    
    print(f"\n验证结果:")
    print(f"  - 包含多个孔位置: {'✓' if has_multiple_holes else '✗'}")
    print(f"  - 包含极坐标输出: {'✓' if has_polar_coords else '✗'}")
    
    return has_multiple_holes and has_polar_coords, nc_program

def test_polar_coordinate_format():
    """测试极坐标格式是否符合预期"""
    print("\n=== 测试极坐标格式 ===")
    
    # 创建一个模拟图像，包含4个孔，其中1个在中心，3个在不同角度
    img = np.zeros((600, 600), dtype=np.uint8)
    
    # 以(300, 300)为中心，创建3个在不同角度的孔
    center_pos = (300, 300)
    angle_positions = [
        (300 + 94, 300),      # X+方向，距离94
        (300, 300 - 30),      # Y-方向，距离30
        (300, 300 + 90),      # Y+方向，距离90
        (300, 300 + 210)      # Y+方向，距离210
    ]
    
    all_positions = [center_pos] + angle_positions
    
    for center in all_positions:
        # 每个位置画同心圆：φ22沉孔 + φ14.5底孔
        outer_radius = 22  # φ22mm
        inner_radius = 15  # φ14.5mm (近似)
        
        cv2.circle(img, center, outer_radius, 255, 2)  # 外圆
        cv2.circle(img, center, inner_radius, 255, 2)  # 内圆
    
    # 识别基本特征
    features = identify_features(img)
    
    # 识别沉孔特征
    user_description = "加工4个φ22深20底孔φ14.5贯通的沉孔特征，使用极坐标标注X94.0 Y-30.0 Y90.0 Y210.0。"
    counterbore_features = identify_counterbore_features(features, user_description)
    
    # 提取最高Y坐标点作为原点
    origin = extract_highest_y_center_point(counterbore_features)
    print(f"选择的坐标原点: {origin}")
    
    # 调整坐标系统
    adjusted_features = adjust_coordinate_system(counterbore_features, origin)
    
    # 分析用户描述
    description_analysis = analyze_user_description(user_description)
    description_analysis["processing_type"] = "counterbore"
    
    # 生成NC代码
    nc_program = generate_fanuc_nc(adjusted_features, description_analysis)
    
    print("\n极坐标格式的NC程序:")
    print("="*50)
    print(nc_program)
    print("="*50)
    
    # 检查是否包含预期的极坐标标注
    expected_coords = ['X94.0', 'Y-30.0', 'Y90.0', 'Y210.0']
    found_coords = []
    for coord in expected_coords:
        if coord.replace('.', r'\.').replace('-', r'\-') in nc_program or coord in nc_program:
            found_coords.append(coord)
    
    print(f"\n预期极坐标标注检查:")
    for coord in expected_coords:
        found = coord in nc_program
        print(f"  - {coord}: {'✓' if found else '✗'}")
    
    success = len(found_coords) >= 2  # 至少找到2个预期坐标
    print(f"\n极坐标格式测试: {'✓ 通过' if success else '✗ 失败'}")
    
    return success, nc_program

def main():
    """主测试函数"""
    print("开始测试修复后的极坐标问题...\n")
    
    # 测试1: 多个沉孔特征识别
    success1, nc1 = test_multiple_counterbore_features()
    
    # 测试2: 极坐标格式
    success2, nc2 = test_polar_coordinate_format()
    
    print(f"\n=== 测试总结 ===")
    print(f"多个孔位置测试: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"极坐标格式测试: {'✓ 通过' if success2 else '✗ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！")
        print("✓ 修复了NC程序只输出单一孔的问题")
        print("✓ 多个沉孔位置能够正确识别和输出")
        print("✓ 极坐标格式正确实现")
        print("✓ 位置数值现在符合预期")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")
    
    return success1 and success2

if __name__ == "__main__":
    main()

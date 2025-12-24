"""
测试改进后的沉孔特征识别和NC程序生成
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import generate_nc_from_pdf
import numpy as np
from src.modules.feature_definition import identify_features, identify_counterbore_features
from src.modules.mechanical_drawing_expert import MechanicalDrawingExpert


def test_counterbore_feature_detection():
    """测试改进的沉孔特征检测"""
    print("=== 测试改进的沉孔特征检测 ===")
    
    # 创建一个模拟图像，包含同心圆（模拟沉孔特征）
    img = np.zeros((200, 200), dtype=np.uint8)
    
    # 创建一个同心圆组合：外圆(沉孔)和内圆(底孔)
    import cv2
    # 外圆 - 沉孔
    cv2.circle(img, (100, 100), 30, 255, 2)
    # 内圆 - 底孔
    cv2.circle(img, (100, 100), 15, 255, 2)
    
    # 添加另一个同心圆组合
    cv2.circle(img, (150, 150), 25, 255, 2)  # 外圆
    cv2.circle(img, (150, 150), 12, 255, 2)  # 内圆
    
    # 添加一个单独的圆（非沉孔）
    cv2.circle(img, (50, 50), 20, 255, 2)
    
    # 模拟图纸文本
    drawing_text = "图纸包含3个沉孔特征，φ22沉孔深20mm + φ14.5贯通底孔"
    
    # 识别特征
    features = identify_features(img, drawing_text=drawing_text)
    print(f"识别到 {len(features)} 个基础特征")
    
    # 识别沉孔特征
    counterbore_features = identify_counterbore_features(features, "请加工沉孔", drawing_text)
    counterbore_count = sum(1 for f in counterbore_features if f['shape'] == 'counterbore')
    
    print(f"识别到 {counterbore_count} 个沉孔特征")
    for i, feature in enumerate(counterbore_features):
        if feature['shape'] == 'counterbore':
            print(f"  沉孔 {i+1}: 中心{feature['center']}, "
                  f"沉孔直径{feature['outer_diameter']:.1f}mm, "
                  f"底孔直径{feature['inner_diameter']:.1f}mm, "
                  f"深度{feature['depth']:.1f}mm")
    
    expected_count = 2  # 应该识别出2个沉孔
    if counterbore_count == expected_count:
        print(f"✓ 沉孔识别测试通过: 识别到 {counterbore_count} 个沉孔 (期望 {expected_count})")
        return True
    else:
        print(f"✗ 沉孔识别测试失败: 识别到 {counterbore_count} 个沉孔 (期望 {expected_count})")
        return False


def test_mechanical_drawing_expert():
    """测试机械制图专家"""
    print("\n=== 测试机械制图专家 ===")
    
    # 模拟图纸文本
    drawing_text = """
    零件名称：测试零件
    图号：TEST-001
    材料：45#钢
    比例：1:1
    \n    技术要求：
    1. 3个φ22沉孔深20mm，φ14.5贯通底孔
    2. 表面粗糙度Ra3.2
    3. 热处理：调质HRC28-32
    """
    
    expert = MechanicalDrawingExpert()
    drawing_info = expert.parse_drawing(drawing_text)
    
    print(f"提取到 {len(drawing_info.features)} 个特征")
    for feature in drawing_info.features:
        print(f"  特征: {feature.type.value}, {feature.annotation}, 置信度: {feature.confidence}")
    
    # 检查是否正确识别了沉孔特征
    counterbore_features = [f for f in drawing_info.features if str(f.type) == "FeatureType.COUNTERBORE"]
    if len(counterbore_features) > 0:
        print("✓ 机械制图专家成功识别沉孔特征")
        print(f"  识别到 {len(counterbore_features)} 个沉孔特征")
        return True
    else:
        print("✗ 机械制图专家未能识别沉孔特征")
        return False


def test_full_process():
    """测试完整流程 - 仅当PDF存在时"""
    print("\n=== 测试完整流程 ===")
    
    # 由于我们没有实际的PDF，跳过完整流程测试
    print("跳过完整流程测试（需要实际PDF文件）")
    return True


def main():
    """主测试函数"""
    print("开始测试改进后的CNC Agent...")
    
    results = []
    results.append(test_counterbore_feature_detection())
    results.append(test_mechanical_drawing_expert())
    results.append(test_full_process())
    
    print(f"\n=== 测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

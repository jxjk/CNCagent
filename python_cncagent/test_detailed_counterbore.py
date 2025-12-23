"""
详细沉孔特征识别测试
验证同心圆的检测和识别
"""
import numpy as np
import cv2
from src.modules.feature_definition import identify_features, identify_counterbore_features

def create_precise_test_image():
    """创建精确的同心圆测试图像"""
    # 创建一个600x600的黑色图像
    img = np.zeros((600, 600), dtype=np.uint8)  # 灰度图
    
    # 在图像上创建精确的同心圆
    # 位置1: φ22沉孔 + φ14.5底孔
    center1 = (200, 200)
    outer_radius1 = 22  # φ22mm -> 22像素 (1mm=1px)
    inner_radius1 = 15  # φ14.5mm -> 15像素 (约值)
    
    # 画出清晰的圆环（使用粗线确保边缘检测能识别）
    cv2.circle(img, center1, outer_radius1, 255, 2)  # 外圆，线宽2
    cv2.circle(img, center1, inner_radius1, 255, 2)  # 内圆，线宽2
    
    # 位置2: 另一组同心圆
    center2 = (400, 300)
    cv2.circle(img, center2, outer_radius1, 255, 2)  # 外圆
    cv2.circle(img, center2, inner_radius1, 255, 2)  # 内圆
    
    # 位置3: 单独的圆（非沉孔）
    center3 = (100, 100)
    single_radius = 20  # 独立的圆
    cv2.circle(img, center3, single_radius, 255, 2)
    
    return img

def debug_feature_identification():
    """调试特征识别过程"""
    print("=== 调试特征识别过程 ===")
    
    # 创建测试图像
    img = create_precise_test_image()
    
    print(f"图像尺寸: {img.shape}")
    
    # 直接使用改进的参数识别特征
    features = identify_features(
        img, 
        min_area=50,        # 减小最小面积阈值
        min_perimeter=10,   # 减小最小周长阈值
        canny_low=30,       # 降低边缘检测阈值
        canny_high=100,     # 降低边缘检测阈值
        gaussian_kernel=(3, 3),  # 减小高斯模糊核
        morph_kernel=(1, 1)      # 减小形态学操作核
    )
    
    print(f"识别到 {len(features)} 个基本圆形特征:")
    for i, feature in enumerate(features):
        if feature['shape'] == 'circle':
            print(f"  特征 {i+1}: 中心{feature['center']}, 半径{feature['radius']:.1f}, 置信度{feature['confidence']:.2f}")
    
    # 应用沉孔特征识别
    counterbore_features = identify_counterbore_features(features)
    
    print(f"\n应用沉孔识别后，共有 {len(counterbore_features)} 个特征:")
    counterbore_count = 0
    circle_count = 0
    
    for i, feature in enumerate(counterbore_features):
        if feature['shape'] == 'counterbore':
            counterbore_count += 1
            print(f"  沉孔特征 {i+1}:")
            print(f"    中心: {feature['center']}")
            print(f"    沉孔直径: {feature['outer_diameter']:.1f}mm (半径{feature['outer_radius']:.1f})")
            print(f"    底孔直径: {feature['inner_diameter']:.1f}mm (半径{feature['inner_radius']:.1f})")
            print(f"    半径比: {feature['outer_radius']/feature['inner_radius']:.2f}")
        else:
            circle_count += 1
            print(f"  特征 {i+1}: {feature['shape']}, 中心{feature['center']}, 半径{feature.get('radius', 'N/A'):.1f}")
    
    print(f"\n统计:")
    print(f"  - 沉孔特征: {counterbore_count}")
    print(f"  - 其他圆形: {circle_count}")
    
    # 验证结果
    if counterbore_count >= 2:  # 至少应识别出2组同心圆作为沉孔
        print("✓ 沉孔特征识别成功")
        return True
    else:
        print("✗ 沉孔特征识别不足")
        return False

def test_specific_counterbore_scenario():
    """测试特定的沉孔场景：用户要求的φ22深20底孔φ14.5贯通"""
    print("\n=== 测试特定沉孔场景 ===")
    print("场景：加工3个φ22深20底孔φ14.5贯通的沉孔特征")
    
    # 创建模拟的3个沉孔特征
    features = [
        # 第1个沉孔
        {
            "shape": "circle",
            "center": (100, 100),
            "radius": 11,  # φ22/2
            "contour": np.array([[110, 100], [100, 110], [90, 100], [100, 90]], dtype=np.int32),
            "bounding_box": (89, 89, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (100, 100),  # 同心
            "radius": 7.25,  # φ14.5/2
            "contour": np.array([[107, 100], [100, 107], [93, 100], [100, 93]], dtype=np.int32),
            "bounding_box": (92.75, 92.75, 14.5, 14.5),
            "area": 167,
            "confidence": 0.8,
            "aspect_ratio": 1.0
        },
        # 第2个沉孔
        {
            "shape": "circle",
            "center": (200, 150),
            "radius": 11,  # φ22/2
            "contour": np.array([[210, 150], [200, 160], [190, 150], [200, 140]], dtype=np.int32),
            "bounding_box": (189, 139, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (200, 150),  # 同心
            "radius": 7.25,  # φ14.5/2
            "contour": np.array([[207, 150], [200, 157], [193, 150], [200, 143]], dtype=np.int32),
            "bounding_box": (192.75, 142.75, 14.5, 14.5),
            "area": 167,
            "confidence": 0.8,
            "aspect_ratio": 1.0
        },
        # 第3个沉孔
        {
            "shape": "circle",
            "center": (300, 200),
            "radius": 11,  # φ22/2
            "contour": np.array([[310, 200], [300, 210], [290, 200], [300, 190]], dtype=np.int32),
            "bounding_box": (289, 189, 22, 22),
            "area": 380,
            "confidence": 0.9,
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (300, 200),  # 同心
            "radius": 7.25,  # φ14.5/2
            "contour": np.array([[307, 200], [300, 207], [293, 200], [300, 193]], dtype=np.int32),
            "bounding_box": (292.75, 192.75, 14.5, 14.5),
            "area": 167,
            "confidence": 0.8,
            "aspect_ratio": 1.0
        }
    ]
    
    print(f"输入 {len(features)} 个圆形特征（3组同心圆）")
    
    # 应用沉孔识别
    result_features = identify_counterbore_features(features)
    
    print(f"输出 {len(result_features)} 个特征:")
    counterbore_count = 0
    for i, feature in enumerate(result_features):
        if feature['shape'] == 'counterbore':
            counterbore_count += 1
            print(f"  沉孔 {counterbore_count}: 中心{feature['center']}, "
                  f"沉孔φ{feature['outer_diameter']:.1f}, "
                  f"底孔φ{feature['inner_diameter']:.1f}, "
                  f"深度{feature['depth']:.1f}mm")
        else:
            print(f"  其他特征: {feature['shape']}, 中心{feature['center']}")
    
    print(f"\n识别结果: {counterbore_count} 个沉孔特征")
    
    if counterbore_count == 3:
        print("✓ 特定沉孔场景识别成功")
        return True
    else:
        print("✗ 特定沉孔场景识别失败")
        return False

def main():
    """主测试函数"""
    print("开始详细沉孔特征识别测试...\n")
    
    success1 = debug_feature_identification()
    success2 = test_specific_counterbore_scenario()
    
    print(f"\n=== 最终测试结果 ===")
    if success1 and success2:
        print("✓ 所有详细测试通过")
        print("✓ 同心圆识别算法优化成功")
        print("✓ 沉孔特征识别准确率达到要求")
    else:
        print("✗ 部分测试未通过，需要进一步优化")
        
    print("\n优化后的沉孔识别功能特点:")
    print("  - 更精确的同心圆匹配算法")
    print("  - 更宽松的半径比验证范围")
    print("  - 更小的位置容差确保准确匹配")


if __name__ == "__main__":
    main()

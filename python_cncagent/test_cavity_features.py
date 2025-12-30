"""
测试新优化的腔槽特征识别和处理功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.ai_driven_generator import AIDrivenCNCGenerator
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.mechanical_drawing_expert import analyze_drawing_features
from src.modules.geometric_reasoning_engine import geometric_reasoning_engine


def test_cavity_feature_recognition():
    """测试腔槽特征识别"""
    print("=== 测试腔槽特征识别 ===")
    
    user_prompt = "请铣削一个矩形腔，尺寸为30x20mm，深度为5mm，圆角R3，以腔中心为原点进行定位，材料为铝合金"
    
    # 测试描述分析
    analysis = analyze_user_description(user_prompt)
    
    print(f"用户请求: {user_prompt}")
    print(f"加工类型: {analysis['processing_type']}")
    print(f"腔槽特征: {analysis['cavity_features']}")
    print(f"圆角半径: {analysis['corner_radius']}")
    print(f"坐标系统: {analysis['coordinate_system']}")
    print(f"特征中心: {analysis['feature_center']}")
    print(f"加工面: {analysis['processing_sides']}")
    
    success = (
        analysis['processing_type'] in ['milling', 'pocket_milling'],
        len(analysis['cavity_features']) > 0,
        analysis['corner_radius'] is not None,
        analysis['coordinate_system'] == 'datum_based'
    )
    print(f"腔槽特征识别测试: {'通过' if all(success) else '失败'}")
    return all(success)


def test_coordinate_system_handling():
    """测试坐标系统处理"""
    print("\n=== 测试坐标系统处理 ===")
    
    user_prompt = "基于左下角基准点，向右30mm、向上20mm处加工一个25x15mm的矩形槽，深度6mm"
    
    analysis = analyze_user_description(user_prompt)
    
    print(f"用户请求: {user_prompt}")
    print(f"坐标系统: {analysis['coordinate_system']}")
    print(f"孔位置: {analysis['hole_positions']}")
    print(f"工件尺寸: {analysis['workpiece_dimensions']}")
    
    success = analysis['coordinate_system'] == 'relative'
    print(f"坐标系统处理测试: {'通过' if success else '失败'}")
    return success


def test_multi_face_processing():
    """测试多面加工识别"""
    print("\n=== 测试多面加工识别 ===")
    
    user_prompt = "双面加工：正面铣削定位孔，反面铣削沉头孔，材料为不锈钢"
    
    analysis = analyze_user_description(user_prompt)
    
    print(f"用户请求: {user_prompt}")
    print(f"加工面: {analysis['processing_sides']}")
    print(f"材料: {analysis['material']}")
    
    success = 'bottom' in analysis['processing_sides']
    print(f"多面加工识别测试: {'通过' if success else '失败'}")
    return success


def test_geometric_reasoning():
    """测试几何推理引擎（如果有图像）"""
    print("\n=== 测试几何推理引擎 ===")
    
    # 由于我们没有实际图像，我们测试引擎的可用性
    try:
        import numpy as np
        # 创建一个简单的测试图像（模拟腔槽特征）
        test_image = np.zeros((100, 100), dtype=np.uint8)
        # 在图像中心绘制一个矩形（模拟腔槽）
        cv2 = __import__('cv2')
        cv2.rectangle(test_image, (30, 30), (70, 70), 255, -1)  # 实心矩形
        cv2.rectangle(test_image, (35, 35), (65, 65), 0, -1)    # 中心挖空，形成类似槽的形状
        
        features = geometric_reasoning_engine.analyze_cavity_features(test_image)
        print(f"识别到 {len(features)} 个特征")
        for i, feature in enumerate(features):
            print(f"  特征{i+1}: {feature.shape_type}, 中心{feature.center}, 尺寸{feature.dimensions}")
        
        processing_analysis = geometric_reasoning_engine.analyze_processing_structure(features)
        print(f"单面加工特征: {len(processing_analysis['single_sided_features'])}")
        print(f"多面加工特征: {len(processing_analysis['multi_sided_features'])}")
        print(f"加工顺序: {processing_analysis['processing_sequence']}")
        print(f"夹紧建议: {processing_analysis['clamping_suggestions']}")
        
        success = len(features) > 0
        print(f"几何推理引擎测试: {'通过' if success else '失败'}")
        return success
        
    except ImportError:
        print("OpenCV未安装，跳过几何推理引擎测试")
        return True  # 不算失败，因为OpenCV是可选依赖
    except Exception as e:
        print(f"几何推理引擎测试出错: {e}")
        return False


def test_feature_integration():
    """测试特征集成到AI生成流程"""
    print("\n=== 测试特征集成到AI生成流程 ===")
    
    generator = AIDrivenCNCGenerator(api_key="dummy_key", model="gpt-4")
    
    user_prompt = "请铣削一个圆角矩形腔，尺寸50x30mm，深度8mm，圆角R5，腔中心坐标X100Y50，使用绝对坐标系统"
    
    requirements = generator.parse_user_requirements(user_prompt)
    
    print(f"用户请求: {user_prompt}")
    print(f"解析的加工类型: {requirements.processing_type}")
    print(f"特殊要求: {requirements.special_requirements}")
    print(f"工具直径: {requirements.tool_diameters}")
    
    # 检查是否正确识别了腔槽相关特征
    has_cavity_desc = any('RECTANGULAR_CAVITY' in req for req in requirements.special_requirements)
    has_corner_radius = any('CORNER_RADIUS' in req for req in requirements.special_requirements)
    has_datum_coord = any('DATUM_BASED_COORDINATE_SYSTEM' in req for req in requirements.special_requirements)
    
    print(f"识别矩形腔: {has_cavity_desc}")
    print(f"识别圆角: {has_corner_radius}")
    print(f"识别坐标系统: {has_datum_coord}")
    
    success = has_cavity_desc or has_corner_radius  # 至少识别出一个特征
    print(f"特征集成测试: {'通过' if success else '失败'}")
    return success


def main():
    """运行所有测试"""
    print("开始测试优化后的腔槽特征识别和处理功能...")
    
    results = []
    results.append(test_cavity_feature_recognition())
    results.append(test_coordinate_system_handling())
    results.append(test_multi_face_processing())
    results.append(test_geometric_reasoning())
    results.append(test_feature_integration())
    
    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {len(results)}")
    print(f"通过测试: {sum(results)}")
    print(f"失败测试: {len(results) - sum(results)}")
    
    if all(results):
        print("所有测试均通过！腔槽特征处理功能优化成功。")
        return True
    else:
        print("部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

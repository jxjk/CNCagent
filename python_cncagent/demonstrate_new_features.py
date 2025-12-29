"""
CNC Agent 新功能演示脚本

此脚本演示了新添加的功能：
1. 特征完整性评估
2. 3D模型处理（概念演示，需要安装相关库）
3. 改进的统一生成器
"""
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

def demonstrate_feature_completeness():
    """演示特征完整性评估功能"""
    print("="*60)
    print("演示1: 特征完整性评估功能")
    print("="*60)
    
    from src.modules.feature_completeness_evaluator import evaluate_feature_completeness, query_system
    
    # 场景1: 不完整的用户描述
    print("\n场景1: 不完整的用户描述")
    features = []  # 假设没有从图纸识别到特征
    user_description = "加工几个孔"
    
    report = evaluate_feature_completeness(features, user_description)
    
    print(f"用户描述: {user_description}")
    print(f"完整性等级: {report.level.value}")
    print(f"置信度: {report.confidence:.2f}")
    print(f"缺失信息: {', '.join(report.missing_info)}")
    print(f"系统建议: {'; '.join(report.recommendations[:2])}...")  # 只显示前两个建议
    
    # 生成查询问题
    queries = query_system.generate_queries_for_missing_info(
        report.missing_info, features, user_description
    )
    print(f"系统将询问: {len(queries)} 个问题来获取缺失信息")
    
    # 场景2: 较完整的描述
    print("\n场景2: 较完整的用户描述")
    features_with_data = [{
        "shape": "circle",
        "center": (100, 50),
        "dimensions": (22, 22),
        "area": 380.13,
        "confidence": 0.85
    }]
    user_description2 = "请加工3个φ22沉孔，深度20mm"
    
    report2 = evaluate_feature_completeness(features_with_data, user_description2)
    
    print(f"用户描述: {user_description2}")
    print(f"完整性等级: {report2.level.value}")
    print(f"置信度: {report2.confidence:.2f}")
    if report2.missing_info:
        print(f"仍缺失信息: {', '.join(report2.missing_info)}")
    else:
        print("信息完整，无需补充!")


def demonstrate_3d_model_processing():
    """演示3D模型处理概念"""
    print("\n"+"="*60)
    print("演示2: 3D模型处理功能")
    print("="*60)
    
    from src.modules.model_3d_processor import Model3DProcessor
    
    processor = Model3DProcessor()
    
    print("支持的3D模型格式:")
    for fmt in sorted(processor.SUPPORTED_FORMATS):
        print(f"  - {fmt}")
    
    print("\n3D模型处理流程:")
    print("1. 加载3D模型文件")
    print("2. 提取几何特征（顶点、面、体积等）")
    print("3. 检测几何基元（平面、圆柱面等）")
    print("4. 将3D信息转换为2D特征格式")
    print("5. 与PDF/图像信息融合生成NC代码")
    
    print("\n注意: 实际处理需要安装open3d或trimesh库")


def demonstrate_improved_unified_generator():
    """演示改进的统一生成器"""
    print("\n"+"="*60)
    print("演示3: 改进的统一生成器")
    print("="*60)
    
    from src.modules.unified_generator import UnifiedCNCGenerator
    import inspect
    
    generator = UnifiedCNCGenerator()
    
    # 显示新方法的签名
    sig = inspect.signature(generator.generate_cnc_program)
    print("generate_cnc_program方法参数:")
    for param_name, param in sig.parameters.items():
        default_val = param.default if param.default != inspect.Parameter.empty else "无默认值"
        print(f"  - {param_name}: {default_val}")
    
    print("\n主要改进:")
    print("1. 添加了model_3d_path参数 - 支持3D模型输入")
    print("2. 添加了enable_completeness_check参数 - 控制完整性检查")
    print("3. 集成特征完整性评估 - 自动检测和补充缺失信息")
    print("4. 支持PDF+3D模型混合输入 - 提高加工精度")


def demonstrate_workflow_integration():
    """演示工作流程集成"""
    print("\n"+"="*60)
    print("演示4: 完整工作流程集成")
    print("="*60)
    
    print("新工作流程:")
    print("1. 用户输入 (PDF/3D模型 + 用户描述)")
    print("2. 特征完整性评估")
    print("   ├─ 评估几何特征完整性")
    print("   ├─ 评估尺寸标注完整性") 
    print("   └─ 评估工艺要求完整性")
    print("3. 识别缺失信息并生成查询")
    print("4. 整合所有信息 (PDF + 3D + 用户补充)")
    print("5. AI模型生成NC代码")
    print("6. 输出结果和模拟报告")
    
    print("\n优势:")
    print("- 即使信息不完整也能生成高质量NC代码")
    print("- 支持多种输入格式，提高灵活性")
    print("- 智能提示用户补充关键信息")
    print("- 结合2D和3D信息，提高精度")


def main():
    """主函数"""
    print("CNC Agent 新功能演示")
    print("此脚本展示新添加的核心功能")
    
    demonstrate_feature_completeness()
    demonstrate_3d_model_processing()
    demonstrate_improved_unified_generator()
    demonstrate_workflow_integration()
    
    print("\n"+"="*60)
    print("演示完成!")
    print("新功能已成功集成到CNC Agent中")
    print("- 特征完整性评估")
    print("- 3D模型处理支持") 
    print("- 智能信息补充系统")
    print("- 改进的统一工作流程")
    print("="*60)


if __name__ == "__main__":
    main()
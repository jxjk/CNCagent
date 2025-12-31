import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def prepare_test_cases():
    """
    准备测试用例和评估标准
    """
    test_cases = {
        "pdf_parsing": {
            "name": "PDF解析能力测试",
            "description": "测试软件从PDF图纸中提取文本、图像和几何信息的能力",
            "test_items": [
                {
                    "id": "pdf_001",
                    "name": "文本提取准确性",
                    "description": "验证从PDF中提取的文本信息是否完整准确",
                    "evaluation_criteria": "提取的文本包含所有尺寸标注、材料信息、公差要求等关键信息",
                    "expected_result": "能够提取图纸中的所有文本内容，包括标题栏、注释、尺寸标注等"
                },
                {
                    "id": "pdf_002",
                    "name": "图像转换质量",
                    "description": "验证PDF转图像的分辨率和质量",
                    "evaluation_criteria": "转换后的图像清晰，能够识别几何特征",
                    "expected_result": "PDF页面成功转换为高分辨率图像，保持原始细节"
                },
                {
                    "id": "pdf_003",
                    "name": "多页处理能力",
                    "description": "验证处理多页PDF的能力",
                    "evaluation_criteria": "能够正确处理多页PDF中的所有页面",
                    "expected_result": "所有页面都被处理并提取信息"
                }
            ]
        },
        "feature_recognition": {
            "name": "几何特征识别测试",
            "description": "测试软件识别几何特征（圆形、矩形、多边形等）的能力",
            "test_items": [
                {
                    "id": "fr_001",
                    "name": "圆形特征识别",
                    "description": "测试识别圆形孔、圆形轮廓的能力",
                    "evaluation_criteria": "正确识别圆形，提取直径、位置等信息",
                    "expected_result": "能够准确识别圆形特征，包括直径、圆心坐标、置信度"
                },
                {
                    "id": "fr_002",
                    "name": "矩形特征识别",
                    "description": "测试识别矩形、方形等直角特征的能力",
                    "evaluation_criteria": "正确识别矩形，提取长宽、位置等信息",
                    "expected_result": "能够准确识别矩形特征，包括长宽、中心坐标、置信度"
                },
                {
                    "id": "fr_003",
                    "name": "复合特征识别",
                    "description": "测试识别沉孔（同心圆）等复合特征的能力",
                    "evaluation_criteria": "正确识别同心圆特征，判断是否为沉孔",
                    "expected_result": "能够识别沉孔特征（外径沉孔+内径底孔）并提取相关参数"
                },
                {
                    "id": "fr_004",
                    "name": "多边形识别",
                    "description": "测试识别三角形、六边形等多边形特征的能力",
                    "evaluation_criteria": "正确识别多边形类型和尺寸",
                    "expected_result": "能够识别并分类多边形特征"
                }
            ]
        },
        "ocr_ai_inference": {
            "name": "OCR和AI推理测试",
            "description": "测试软件结合OCR和AI模型理解图纸信息的能力",
            "test_items": [
                {
                    "id": "ocr_001",
                    "name": "OCR文字识别准确性",
                    "description": "测试从图像中识别文字的准确性",
                    "evaluation_criteria": "能够准确识别图纸上的文字，特别是尺寸标注",
                    "expected_result": "尺寸标注、材料信息、加工要求等文字准确识别"
                },
                {
                    "id": "ocr_002",
                    "name": "AI推理准确性",
                    "description": "测试AI模型对图纸信息的理解能力",
                    "evaluation_criteria": "能够正确理解用户的加工需求，并生成相应工艺规划",
                    "expected_result": "AI能够理解图纸和用户描述，并生成合理的加工工艺规划"
                },
                {
                    "id": "ocr_003",
                    "name": "多源信息融合",
                    "description": "测试融合OCR、图像、PDF文本信息的能力",
                    "evaluation_criteria": "能够整合多源信息进行综合推理",
                    "expected_result": "能够将来自不同源的信息统一分析，生成准确的特征理解"
                }
            ]
        },
        "ai_driven_generation": {
            "name": "AI驱动生成测试",
            "description": "测试AI优先生成NC代码的能力",
            "test_items": [
                {
                    "id": "ai_001",
                    "name": "AI模型调用",
                    "description": "测试调用大语言模型生成NC代码的能力",
                    "evaluation_criteria": "能够成功调用AI模型并获得合理的NC代码输出",
                    "expected_result": "AI模型返回有效的FANUC G代码"
                },
                {
                    "id": "ai_002",
                    "name": "提示词构建质量",
                    "description": "测试构建的提示词是否有效引导AI生成正确代码",
                    "evaluation_criteria": "提示词结构合理，包含足够的上下文信息",
                    "expected_result": "构建的提示词能够引导AI生成符合要求的NC代码"
                },
                {
                    "id": "ai_003",
                    "name": "工艺规划推理",
                    "description": "测试AI进行工艺规划的能力",
                    "evaluation_criteria": "AI能够根据图纸信息规划合理的加工顺序",
                    "expected_result": "生成合理的加工工艺，包括刀具选择、加工顺序、切削参数等"
                }
            ]
        },
        "coordinate_system": {
            "name": "坐标系统处理测试",
            "description": "测试软件处理多种坐标系统的能力",
            "test_items": [
                {
                    "id": "coord_001",
                    "name": "坐标原点选择",
                    "description": "测试选择不同坐标原点策略的能力",
                    "evaluation_criteria": "能够根据策略正确选择坐标原点",
                    "expected_result": "支持highest_y、lowest_y、center等多种坐标原点选择策略"
                },
                {
                    "id": "coord_002",
                    "name": "坐标转换准确性",
                    "description": "测试将特征坐标转换到选定原点的准确性",
                    "evaluation_criteria": "特征坐标正确转换为相对于新原点的坐标",
                    "expected_result": "所有特征坐标正确转换"
                }
            ]
        },
        "completeness_assessment": {
            "name": "特征完整性评估测试",
            "description": "测试软件评估图纸信息完整性的能力",
            "test_items": [
                {
                    "id": "ca_001",
                    "name": "缺失信息检测",
                    "description": "测试检测图纸中缺失关键信息的能力",
                    "evaluation_criteria": "能够识别缺失的尺寸、材料、加工要求等信息",
                    "expected_result": "能够识别图纸信息的完整性，并提示缺失内容"
                },
                {
                    "id": "ca_002",
                    "name": "补充建议生成",
                    "description": "测试生成补充信息建议的能力",
                    "evaluation_criteria": "能够生成合理的补充信息建议",
                    "expected_result": "为缺失信息提供合理的默认值或建议"
                }
            ]
        }
    }
    
    return test_cases

def print_evaluation_standards():
    """
    打印评估标准
    """
    standards = """
    CNC Agent二维PDF图纸理解能力评估标准
    
    1. 准确性指标
       - 几何特征识别准确率 >= 85%
       - OCR文字识别准确率 >= 90%
       - 尺寸提取准确率 >= 95%
       - 位置信息提取准确率 >= 90%
    
    2. 完整性指标
       - 图纸信息提取覆盖率 >= 90%
       - 关键特征识别率 >= 95%
       - 复合特征识别率 >= 80%
    
    3. AI推理能力指标
       - NC代码生成成功率 >= 90%
       - 工艺规划合理性评分 >= 4.0/5.0
       - 多源信息融合有效性 >= 85%
    
    4. 性能指标
       - PDF解析时间 <= 30秒 (10页以内)
       - 特征识别时间 <= 60秒 (复杂图纸)
       - AI模型响应时间 <= 120秒 (网络正常情况下)
    
    5. 鲁棒性指标
       - 支持PDF版本: 1.4-1.7
       - 支持图像分辨率: 150-300 DPI
       - 字体支持: 中英文主流字体
       - 错误处理能力: 能处理损坏或非标准PDF
    """
    print(standards)

def print_test_case_summary(test_cases):
    """
    打印测试用例摘要
    """
    print("=" * 80)
    print("CNC Agent二维PDF图纸理解能力测试用例摘要")
    print("=" * 80)
    
    total_tests = 0
    for category, data in test_cases.items():
        print(f"\n{data['name']}")
        print(f"描述: {data['description']}")
        print("测试项:")
        for item in data['test_items']:
            total_tests += 1
            print(f"  - {item['id']}: {item['name']}")
        print("-" * 60)
    
    print(f"\n总计: {total_tests} 个测试项分布在 {len(test_cases)} 个测试类别中")
    print("=" * 80)

if __name__ == "__main__":
    # 准备测试用例
    test_cases = prepare_test_cases()
    
    # 打印评估标准
    print_evaluation_standards()
    
    # 打印测试用例摘要
    print_test_case_summary(test_cases)
    
    print("\n测试用例和评估标准已准备就绪！")
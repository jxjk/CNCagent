"""
特征完整性评估模块
评估从图纸和用户描述中提取的特征信息的完整性，识别缺失信息并提供补充建议
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from src.modules.feature_definition import identify_features
from src.modules.material_tool_matcher import analyze_user_description
from src.modules.mechanical_drawing_expert import MechanicalDrawingExpert


class CompletenessLevel(Enum):
    """完整性等级枚举"""
    COMPLETE = "complete"          # 完整
    NEARLY_COMPLETE = "nearly_complete"  # 几乎完整
    PARTIAL = "partial"            # 部分信息
    INCOMPLETE = "incomplete"      # 不完整
    CRITICAL_MISSING = "critical_missing"  # 关键信息缺失


@dataclass
class CompletenessReport:
    """完整性报告"""
    level: CompletenessLevel
    geometric_features: Dict[str, Any]
    dimension_annotations: Dict[str, Any]
    process_requirements: Dict[str, Any]
    missing_info: List[str]
    recommendations: List[str]
    confidence: float


class FeatureCompletenessEvaluator:
    """特征完整性评估器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.drawing_expert = MechanicalDrawingExpert()
    
    def evaluate_completeness(
        self, 
        features: List[Dict], 
        user_description: str, 
        pdf_features: Optional[Dict] = None
    ) -> CompletenessReport:
        """
        评估特征识别的完整性
        
        Args:
            features: 识别的几何特征列表
            user_description: 用户描述
            pdf_features: 从PDF提取的特征信息（可选）
            
        Returns:
            CompletenessReport: 完整性报告
        """
        # 评估几何特征完整性
        geometric_result = self._evaluate_geometric_completeness(features)
        
        # 评估尺寸标注完整性
        dimension_result = self._evaluate_dimension_completeness(features, user_description, pdf_features)
        
        # 评估工艺要求完整性
        process_result = self._evaluate_process_completeness(user_description)
        
        # 识别缺失信息
        missing_info = self._identify_missing_info(
            geometric_result, dimension_result, process_result, user_description
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(
            missing_info, features, user_description
        )
        
        # 计算完整性等级
        level = self._calculate_completeness_level(
            geometric_result, dimension_result, process_result, missing_info
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(
            geometric_result, dimension_result, process_result
        )
        
        report = CompletenessReport(
            level=level,
            geometric_features=geometric_result,
            dimension_annotations=dimension_result,
            process_requirements=process_result,
            missing_info=missing_info,
            recommendations=recommendations,
            confidence=confidence
        )
        
        self.logger.info(f"特征完整性评估完成，等级: {level.value}, 置信度: {confidence:.2f}")
        return report
    
    def _evaluate_geometric_completeness(self, features: List[Dict]) -> Dict[str, Any]:
        """评估几何特征的完整性"""
        result = {
            'count': len(features),
            'types': {},
            'has_position_info': False,
            'has_size_info': False,
            'has_shape_info': True,
            'quality': 0.0
        }
        
        if not features:
            result['quality'] = 0.0
            return result
        
        # 统计特征类型
        for feature in features:
            shape = feature.get('shape', 'unknown')
            if shape in result['types']:
                result['types'][shape] += 1
            else:
                result['types'][shape] = 1
        
        # 检查位置信息
        position_found = any('center' in f and f['center'] for f in features)
        result['has_position_info'] = position_found
        
        # 检查尺寸信息
        size_found = any('dimensions' in f and f['dimensions'] for f in features)
        result['has_size_info'] = size_found
        
        # 计算质量分数
        quality_score = 0.0
        if position_found:
            quality_score += 0.4
        if size_found:
            quality_score += 0.3
        if result['types']:
            quality_score += 0.3  # 有形状信息
        
        result['quality'] = quality_score
        return result
    
    def _evaluate_dimension_completeness(
        self, 
        features: List[Dict], 
        user_description: str, 
        pdf_features: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """评估尺寸标注的完整性"""
        result = {
            'from_description': {},
            'from_pdf': {},
            'from_features': {},
            'has_depth_info': False,
            'has_diameter_info': False,
            'has_tolerance_info': False,
            'quality': 0.0
        }
        
        # 从用户描述中提取尺寸信息
        description_analysis = analyze_user_description(user_description)
        result['from_description'] = description_analysis
        
        # 从PDF特征中提取尺寸信息
        if pdf_features:
            result['from_pdf'] = pdf_features
        
        # 从几何特征中提取尺寸信息
        for feature in features:
            if 'dimensions' in feature:
                result['from_features'][feature.get('shape', 'unknown')] = feature['dimensions']
        
        # 检查深度信息
        has_depth = (
            description_analysis.get('depth') is not None or
            any('depth' in str(v) for v in result['from_pdf'].values()) if result['from_pdf'] else False
        )
        result['has_depth_info'] = has_depth
        
        # 检查直径信息
        has_diameter = (
            description_analysis.get('outer_diameter') is not None or
            description_analysis.get('inner_diameter') is not None or
            bool(re.search(r'φ\d+', user_description, re.IGNORECASE))
        )
        result['has_diameter_info'] = has_diameter
        
        # 检查公差信息
        has_tolerance = '±' in user_description or '公差' in user_description
        result['has_tolerance_info'] = has_tolerance
        
        # 计算质量分数
        quality_score = 0.0
        if has_depth:
            quality_score += 0.3
        if has_diameter:
            quality_score += 0.4
        if has_tolerance:
            quality_score += 0.3
        
        result['quality'] = quality_score
        return result
    
    def _evaluate_process_completeness(self, user_description: str) -> Dict[str, Any]:
        """评估工艺要求的完整性"""
        result = {
            'processing_type': 'unknown',
            'tool_required': 'unknown',
            'feed_rate': None,
            'spindle_speed': None,
            'material': None,
            'has_type_info': False,
            'has_parameter_info': False,
            'quality': 0.0
        }
        
        # 分析用户描述
        description_analysis = analyze_user_description(user_description)
        
        # 提取工艺信息
        result['processing_type'] = description_analysis.get('processing_type', 'unknown')
        result['tool_required'] = description_analysis.get('tool_required', 'unknown')
        result['feed_rate'] = description_analysis.get('feed_rate')
        result['spindle_speed'] = description_analysis.get('spindle_speed')
        result['material'] = description_analysis.get('material')
        
        # 检查工艺类型信息
        result['has_type_info'] = result['processing_type'] != 'unknown'
        
        # 检查参数信息
        result['has_parameter_info'] = (
            result['feed_rate'] is not None or
            result['spindle_speed'] is not None
        )
        
        # 计算质量分数
        quality_score = 0.0
        if result['has_type_info']:
            quality_score += 0.5
        if result['has_parameter_info']:
            quality_score += 0.5
        
        result['quality'] = quality_score
        return result
    
    def _identify_missing_info(
        self,
        geometric_result: Dict,
        dimension_result: Dict,
        process_result: Dict,
        user_description: str
    ) -> List[str]:
        """识别缺失的信息"""
        missing_info = []
        
        # 检查几何特征相关缺失
        if geometric_result['quality'] < 0.5:
            if not geometric_result['has_position_info']:
                missing_info.append("feature_positions")
            if not geometric_result['has_size_info']:
                missing_info.append("feature_sizes")
        
        # 检查尺寸标注相关缺失
        if dimension_result['quality'] < 0.5:
            if not dimension_result['has_depth_info']:
                missing_info.append("depth_information")
            if not dimension_result['has_diameter_info']:
                missing_info.append("diameter_information")
        
        # 检查工艺要求相关缺失
        if process_result['quality'] < 0.5:
            if not process_result['has_type_info']:
                missing_info.append("processing_type")
            if not process_result['has_parameter_info']:
                missing_info.append("process_parameters")
        
        # 使用正则表达式更精确地识别缺失的特定信息
        required_patterns = [
            (r'(?:位置|坐标|X|Y)', 'coordinates', '缺少孔位置坐标信息'),
            (r'(?:深度|深|DEPTH)', 'depth', '缺少加工深度信息'),
            (r'(?:直径|φ|diameter)', 'diameter', '缺少直径尺寸信息'),
            (r'(?:材料|material)', 'material', '缺少材料信息'),
            (r'(?:转速|spindle|S)', 'speed', '缺少主轴转速信息'),
            (r'(?:进给|feed|F)', 'feed', '缺少进给速度信息'),
        ]
        
        for pattern, key, message in required_patterns:
            if key not in missing_info and not re.search(pattern, user_description, re.IGNORECASE):
                # 对于某些信息（如转速、进给），如果在描述分析中有提取到，则不算缺失
                if key == 'speed' and process_result.get('spindle_speed') is not None:
                    continue
                if key == 'feed' and process_result.get('feed_rate') is not None:
                    continue
                # 特殊处理深度信息
                if key == 'depth' and dimension_result.get('from_description', {}).get('depth') is not None:
                    continue
                # 特殊处理直径信息
                if key == 'diameter':
                    desc_analysis = dimension_result.get('from_description', {})
                    if (desc_analysis.get('outer_diameter') is not None or 
                        desc_analysis.get('inner_diameter') is not None):
                        continue
                missing_info.append(message)
        
        # 添加安全性相关的检查，确保关键安全信息不缺失
        safety_patterns = [
            (r'(?:安全|safe|防护)', 'safety', '缺少安全相关要求'),
            (r'(?:冷却|切削液|coolant)', 'coolant', '缺少冷却液相关要求'),
            (r'(?:夹紧|装夹|clamping)', 'clamping', '缺少装夹相关要求'),
        ]
        
        for pattern, key, message in safety_patterns:
            if key not in missing_info and not re.search(pattern, user_description, re.IGNORECASE):
                # 检查是否在其他结果中已有相关信息
                if key == 'clamping' and ('clamping_suggestions' in geometric_result or 
                                          'clamping' in str(geometric_result.get('quality', 0))):
                    continue
                missing_info.append(message)
        
        # 如果没有任何缺失信息，但整体质量较低，添加一般性提示
        if not missing_info:
            if (geometric_result['quality'] < 0.7 or 
                dimension_result['quality'] < 0.7 or 
                process_result['quality'] < 0.7):
                missing_info.append("additional_detail_recommendation")
        
        return missing_info
    
    def _generate_recommendations(
        self, 
        missing_info: List[str], 
        features: List[Dict], 
        user_description: str
    ) -> List[str]:
        """生成补充信息的建议"""
        recommendations = []
        
        for missing in missing_info:
            if missing == "feature_positions":
                recommendations.append("请在图纸或描述中明确标注特征位置坐标(X,Y)")
            elif missing == "depth_information":
                recommendations.append("请提供加工深度信息，如'深度20mm'或'深20'")
            elif missing == "diameter_information":
                recommendations.append("请提供直径尺寸信息，如'φ22沉孔'或'直径22mm'")
            elif missing == "processing_type":
                recommendations.append("请明确加工类型，如'钻孔'、'沉孔'、'攻丝'、'铣削'等")
            elif missing == "process_parameters":
                recommendations.append("请提供加工参数，如'转速800'、'进给100'等")
            elif missing == "coordinates":
                recommendations.append("请提供孔位坐标信息，如'X100 Y50'或'位置(100,50)'")
            elif missing == "material":
                recommendations.append("请提供材料信息，如'45号钢'、'铝合金'等")
            elif missing == "speed":
                recommendations.append("请提供主轴转速，如'S800'或'转速800'")
            elif missing == "feed":
                recommendations.append("请提供进给速度，如'F100'或'进给100'")
            elif missing == "additional_detail_recommendation":
                # 分析当前描述，提供具体的改进建议
                if not any(t in user_description.lower() for t in ['钻孔', '沉孔', '攻丝', '铣', '车', 'tapping', 'drill', 'mill', 'turn']):
                    recommendations.append("建议在描述中明确加工类型，如'钻孔'、'沉孔'、'攻丝'等")
                if not any(c in user_description for c in ['X', 'Y', '(', ')', '坐标', '位置']):
                    recommendations.append("建议提供孔位坐标信息")
        
        # 如果特征数量为0，提供特殊建议
        if not features and not any('缺少' in rec for rec in recommendations):
            recommendations.insert(0, "未能从图纸中识别到明显的几何特征，建议检查图纸质量和格式")
        
        return recommendations
    
    def _calculate_completeness_level(
        self,
        geometric_result: Dict,
        dimension_result: Dict,
        process_result: Dict,
        missing_info: List[str]
    ) -> CompletenessLevel:
        """计算完整性等级"""
        # 如果有关键信息缺失，直接返回CRITICAL_MISSING
        critical_items = ['processing_type', 'depth_information', 'diameter_information']
        for missing in missing_info:
            if any(crit in missing for crit in critical_items):
                return CompletenessLevel.CRITICAL_MISSING
        
        # 计算总体质量分数
        total_quality = (
            geometric_result['quality'] + 
            dimension_result['quality'] + 
            process_result['quality']
        ) / 3
        
        if total_quality >= 0.8:
            return CompletenessLevel.COMPLETE
        elif total_quality >= 0.6:
            return CompletenessLevel.NEARLY_COMPLETE
        elif total_quality >= 0.4:
            return CompletenessLevel.PARTIAL
        else:
            return CompletenessLevel.INCOMPLETE
    
    def _calculate_confidence(
        self,
        geometric_result: Dict,
        dimension_result: Dict,
        process_result: Dict
    ) -> float:
        """计算整体置信度"""
        # 基于各部分的质量分数计算总体置信度
        geometric_weight = 0.4  # 几何特征权重
        dimension_weight = 0.4  # 尺寸标注权重
        process_weight = 0.2    # 工艺要求权重
        
        confidence = (
            geometric_result['quality'] * geometric_weight +
            dimension_result['quality'] * dimension_weight +
            process_result['quality'] * process_weight
        )
        
        return confidence


def evaluate_feature_completeness(
    features: List[Dict], 
    user_description: str, 
    pdf_features: Optional[Dict] = None
) -> CompletenessReport:
    """
    评估特征完整性的便捷函数
    
    Args:
        features: 识别的几何特征列表
        user_description: 用户描述
        pdf_features: 从PDF提取的特征信息（可选）
        
    Returns:
        CompletenessReport: 完整性报告
    """
    evaluator = FeatureCompletenessEvaluator()
    return evaluator.evaluate_completeness(features, user_description, pdf_features)


# 交互式查询系统
class InteractiveQuerySystem:
    """交互式查询系统，用于获取缺失的信息"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_queries_for_missing_info(
        self, 
        missing_info: List[str], 
        features: List[Dict], 
        user_description: str
    ) -> List[Dict[str, str]]:
        """
        为缺失的信息生成查询问题
        
        Args:
            missing_info: 缺失信息列表
            features: 识别的几何特征
            user_description: 用户描述
            
        Returns:
            查询问题列表，每个问题包含问题文本和信息类型
        """
        queries = []
        
        for missing in missing_info:
            if "位置" in missing or "坐标" in missing or "coordinates" in missing:
                query_text = (
                    "请提供孔位坐标信息。支持以下格式：\n"
                    "1. X100.0 Y50.0\n"
                    "2. X=100, Y=50\n" 
                    "3. (100, 50)\n"
                    "4. 位置X100 Y50\n"
                    "请根据您的图纸提供准确坐标："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'coordinates',
                    'required': True
                })
            elif "深度" in missing or "depth" in missing:
                query_text = (
                    "请提供加工深度信息，例如：\n"
                    "1. 深度20mm\n"
                    "2. 深20\n"
                    "3. 20mm深\n"
                    "请输入加工深度："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'depth',
                    'required': True
                })
            elif "直径" in missing or "diameter" in missing:
                query_text = (
                    "请提供直径尺寸信息，例如：\n"
                    "1. φ22沉孔\n"
                    "2. 直径22mm\n"
                    "3. φ22锪孔\n"
                    "请输入直径尺寸："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'diameter',
                    'required': True
                })
            elif "加工类型" in missing or "processing_type" in missing:
                query_text = (
                    "请明确加工类型：\n"
                    "1. 钻孔 - 简单的孔加工\n"
                    "2. 沉孔 - 锪平孔口\n"
                    "3. 攻丝 - 加工螺纹\n"
                    "4. 铣削 - 平面或轮廓加工\n"
                    "5. 车削 - 外圆或内孔车削\n"
                    "请选择或描述您的加工需求："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'processing_type',
                    'required': True
                })
            elif "材料" in missing or "material" in missing:
                query_text = (
                    "请提供材料信息，例如：\n"
                    "1. 45号钢\n"
                    "2. 铝合金\n"
                    "3. 不锈钢\n"
                    "4. 铜\n"
                    "5. 塑料\n"
                    "请输入材料类型："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'material',
                    'required': False  # 材料不是绝对必需的
                })
            elif "转速" in missing or "speed" in missing:
                query_text = (
                    "请提供主轴转速（可选，如不提供将使用默认值）：\n"
                    "例如：S800 或 转速800\n"
                    "输入转速值："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'spindle_speed',
                    'required': False
                })
            elif "进给" in missing or "feed" in missing:
                query_text = (
                    "请提供进给速度（可选，如不提供将使用默认值）：\n"
                    "例如：F100 或 进给100\n"
                    "输入进给速度："
                )
                queries.append({
                    'question': query_text,
                    'info_type': 'feed_rate',
                    'required': False
                })
        
        return queries
    
    def validate_user_response(self, info_type: str, response: str) -> Tuple[bool, str]:
        """
        验证用户响应的有效性
        
        Args:
            info_type: 信息类型
            response: 用户响应
            
        Returns:
            (是否有效, 错误信息或处理后的值)
        """
        if not response or not response.strip():
            return False, "响应不能为空"
        
        response = response.strip()
        
        if info_type == 'coordinates':
            # 验证坐标格式
            import re
            # 支持多种坐标格式
            patterns = [
                r'X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)',  # X100 Y50
                r'X\s*[=:]\s*([+-]?\d+\.?\d*)\s*[,，和]\s*Y\s*[=:]\s*([+-]?\d+\.?\d*)',  # X=100, Y=50
                r'\(\s*([+-]?\d+\.?\d*)\s*[,,\s]\s*([+-]?\d+\.?\d*)\s*\)',  # (100, 50)
                r'（\s*([+-]?\d+\.?\d*)\s*[，,\s]\s*([+-]?\d+\.?\d*)\s*）',  # （100，50）
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    try:
                        x, y = float(match[0]), float(match[1])
                        if -1000 <= x <= 1000 and -1000 <= y <= 1000:  # 合理范围检查
                            return True, f"X{x} Y{y}"
                    except (ValueError, IndexError):
                        continue
            
            return False, "坐标格式不正确，请使用 X100 Y50 或 (100, 50) 等格式"
        
        elif info_type == 'depth':
            # 验证深度格式
            import re
            patterns = [
                r'(\d+\.?\d*)\s*([mM]?[mM]?)',  # 20mm, 20
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    try:
                        value = float(match[0])
                        if 0 < value <= 1000:  # 合理范围检查
                            unit = match[1].lower() if len(match) > 1 else 'mm'
                            if unit in ['', 'mm', 'm']:
                                if unit == 'm':
                                    value *= 1000  # 转换为mm
                                return True, str(value)
                    except (ValueError, IndexError):
                        continue
            
            return False, "深度格式不正确，请使用数字或数字+单位，如'20mm'或'20'"
        
        elif info_type == 'diameter':
            # 验证直径格式
            import re
            patterns = [
                r'φ?\s*(\d+\.?\d*)',  # φ22, 22
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    try:
                        value = float(match)
                        if 0 < value <= 500:  # 合理范围检查
                            return True, str(value)
                    except ValueError:
                        continue
            
            return False, "直径格式不正确，请使用数字或φ+数字，如'φ22'或'22'"
        
        elif info_type == 'processing_type':
            # 验证加工类型
            valid_types = ['钻孔', '沉孔', '攻丝', '铣削', '车削', 
                          'drilling', 'counterbore', 'tapping', 'milling', 'turning']
            response_lower = response.lower()
            for valid_type in valid_types:
                if valid_type in response_lower:
                    # 返回标准化的类型名称
                    if any(t in response_lower for t in ['钻孔', 'drill']):
                        return True, 'drilling'
                    elif any(t in response_lower for t in ['沉孔', '锪孔', 'counterbore']):
                        return True, 'counterbore'
                    elif any(t in response_lower for t in ['攻丝', 'tapping']):
                        return True, 'tapping'
                    elif any(t in response_lower for t in ['铣', 'mill']):
                        return True, 'milling'
                    elif any(t in response_lower for t in ['车', 'turn']):
                        return True, 'turning'
            
            return False, "不支持的加工类型，请从钻孔、沉孔、攻丝、铣削、车削中选择"
        
        elif info_type in ['material', 'spindle_speed', 'feed_rate']:
            # 对于这些信息，只要非空就认为有效
            return True, response
        
        return True, response  # 默认认为有效


# 全局实例
completeness_evaluator = FeatureCompletenessEvaluator()
query_system = InteractiveQuerySystem()
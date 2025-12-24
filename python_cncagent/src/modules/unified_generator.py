"""
统一CNC程序生成入口
整合AI驱动、OCR推理和传统图像处理功能
"""
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

from src.exceptions import CNCError, InputValidationError, handle_exception
from .ai_driven_generator import generate_nc_with_ai
from .ocr_ai_inference import extract_features_from_pdf_with_ai
from .gcode_generation import generate_fanuc_nc
from .material_tool_matcher import analyze_user_description
from .feature_definition import identify_features

class UnifiedCNCGenerator:
    """
    统一CNC程序生成器
    整合AI驱动、OCR推理和传统图像处理功能
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_generator = generate_nc_with_ai
        self.ocr_extractor = extract_features_from_pdf_with_ai
        self.traditional_generator = generate_fanuc_nc
        self.description_analyzer = analyze_user_description
        self.feature_identifier = identify_features
    
    def generate_cnc_program(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        use_ai_primary: bool = True,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        生成CNC程序的统一接口
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            use_ai_primary: 是否优先使用AI驱动方法
            user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
            
        Returns:
            str: 生成的NC程序代码
            
        Raises:
            InputValidationError: 输入参数验证失败
            CNCError: 生成过程中发生错误
        """
        # 输入验证
        if not user_prompt or not user_prompt.strip():
            raise InputValidationError("用户需求描述不能为空")
        
        if pdf_path and not Path(pdf_path).exists():
            raise InputValidationError(f"PDF文件不存在: {pdf_path}")
        
        if image_path and not Path(image_path).exists():
            raise InputValidationError(f"图像文件不存在: {image_path}")
        
        if not 0.0 <= user_priority_weight <= 1.0:
            raise InputValidationError("用户优先级权重必须在0.0到1.0之间")
        
        try:
            if use_ai_primary:
                return self._generate_with_ai_approach(user_prompt, pdf_path, image_path, user_priority_weight)
            else:
                return self._generate_with_traditional_approach(user_prompt, pdf_path, image_path, user_priority_weight)
        except CNCError:
            # 如果已经是CNCError，直接重新抛出
            raise
        except Exception as e:
            error = handle_exception(e, self.logger, "生成CNC程序时出错")
            raise CNCError(f"生成CNC程序失败: {str(error)}", original_exception=e) from e
    
    def _generate_with_ai_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用AI驱动方法生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 如果有PDF，先提取特征，但确保用户描述优先
        if pdf_path:
            try:
                pdf_features = self.ocr_extractor(pdf_path)
                # 重点：将用户需求放在首位，PDF特征作为补充
                enhanced_prompt = self._enhance_prompt_with_user_priority(user_prompt, pdf_features, user_priority_weight)
                return self.ai_generator(enhanced_prompt, pdf_path)
            except Exception as e:
                self.logger.warning(f"PDF特征提取失败，回退到基础AI生成: {str(e)}")
                # 即使PDF提取失败，也要确保用户需求优先
                return self.ai_generator(user_prompt, pdf_path)
        else:
            # 直接使用AI生成，但确保用户需求优先
            return self.ai_generator(user_prompt, pdf_path)
    
    def _enhance_prompt_with_pdf_features(self, user_prompt: str, pdf_features: Dict) -> str:
        """
        使用PDF特征增强用户提示
        
        Args:
            user_prompt: 原始用户提示
            pdf_features: 从PDF提取的特征
            
        Returns:
            str: 增强后的提示
        """
        enhanced = f"{user_prompt}\n\n参考图纸信息：\n"
        
        # 添加材料信息
        materials = pdf_features.get('materials', [])
        if materials:
            enhanced += f"材料规格: {', '.join(materials)}\n"
        
        # 添加尺寸信息
        dimensions = pdf_features.get('dimensions', [])
        if dimensions:
            enhanced += f"关键尺寸: {', '.join(map(str, dimensions[:5]))}...\n"  # 只取前5个
        
        # 添加孔信息
        holes = pdf_features.get('hole_details', [])
        if holes:
            enhanced += f"孔特征: {', '.join(holes[:3])}...\n"  # 只取前3个
        
        # 添加推断的加工类型
        inferred_types = pdf_features.get('inferred_process_types', [])
        if inferred_types:
            enhanced += f"建议加工类型: {', '.join(inferred_types)}\n"
        
        return enhanced
    
    def _enhance_prompt_with_user_priority(self, user_prompt: str, pdf_features: Dict, user_priority_weight: float = 1.0) -> str:
        """
        增强用户提示，确保用户需求优先，PDF特征作为补充
        
        Args:
            user_prompt: 原始用户提示
            pdf_features: 从PDF提取的特征
            user_priority_weight: 用户描述优先级权重 (0.0-1.0)
            
        Returns:
            str: 增强后的提示（用户需求优先）
        """
        # 根据权重调整用户需求的强调程度
        if user_priority_weight >= 0.9:
            # 最高优先级：强烈强调用户需求
            enhanced = f"重要：严格按照以下用户需求生成NC程序。用户需求优先级最高。\n\n"
            enhanced += f"用户需求: {user_prompt}\n\n"
            enhanced += f"图纸参考信息（仅在与用户需求一致时使用）：\n"
        elif user_priority_weight >= 0.7:
            # 高优先级：适度强调用户需求
            enhanced = f"注意：优先满足以下用户需求，图纸信息仅作参考。\n\n"
            enhanced += f"用户需求: {user_prompt}\n\n"
            enhanced += f"图纸参考信息：\n"
        else:
            # 中等优先级：平衡用户需求和图纸信息
            enhanced = f"请满足以下用户需求，并参考图纸信息进行加工。\n\n"
            enhanced += f"用户需求: {user_prompt}\n\n"
            enhanced += f"图纸信息：\n"
        
        # 添加材料信息
        materials = pdf_features.get('materials', [])
        if materials:
            enhanced += f"材料规格: {', '.join(materials)}\n"
        
        # 添加尺寸信息
        dimensions = pdf_features.get('dimensions', [])
        if dimensions:
            enhanced += f"图纸标注尺寸: {', '.join(map(str, dimensions[:5]))}...\n"  # 只取前5个
        
        # 添加孔信息
        holes = pdf_features.get('hole_details', [])
        if holes:
            enhanced += f"图纸孔特征: {', '.join(holes[:3])}...\n"  # 只取前3个
        
        # 添加推断的加工类型
        inferred_types = pdf_features.get('inferred_process_types', [])
        if inferred_types:
            enhanced += f"图纸建议加工类型: {', '.join(inferred_types)}\n"
        
        # 根据权重添加冲突处理说明
        if user_priority_weight >= 0.9:
            enhanced += f"\n重要提醒：如果图纸信息与用户需求冲突，必须严格以用户需求为准。"
        elif user_priority_weight >= 0.7:
            enhanced += f"\n提醒：如果图纸信息与用户需求冲突，优先考虑用户需求。"
        else:
            enhanced += f"\n提醒：如果图纸信息与用户需求冲突，根据实际情况平衡考虑。"
        
        return enhanced
    
    def _generate_with_traditional_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用传统方法生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 分析用户描述，确保用户需求优先
        description_analysis = self.description_analyzer(user_prompt)
        
        # 根据用户优先级权重调整分析结果
        if user_priority_weight < 1.0:
            # 降低用户需求优先级时，增加对图纸信息的依赖
            if pdf_path:
                try:
                    pdf_features = self.ocr_extractor(pdf_path)
                    # 将PDF特征与用户描述分析结果合并，但保持用户需求的权重
                    description_analysis = self._merge_user_and_pdf_analysis(
                        description_analysis, pdf_features, user_priority_weight
                    )
                except Exception as e:
                    self.logger.warning(f"PDF特征提取失败，仅使用用户描述: {str(e)}")
        
        # 如果有图像，识别特征
        features = []
        if image_path:
            try:
                import cv2
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                if image is not None:
                    features = self.feature_identifier(image)
            except Exception as e:
                self.logger.warning(f"图像特征识别失败: {str(e)}")
        
        # 生成NC程序，确保用户需求优先
        return self.traditional_generator(features, description_analysis)
    
    def _merge_user_and_pdf_analysis(self, user_analysis: Dict, pdf_features: Dict, user_priority_weight: float) -> Dict:
        """
        合并用户描述分析和PDF特征分析结果，根据用户优先级权重调整
        
        Args:
            user_analysis: 用户描述分析结果
            pdf_features: PDF特征提取结果
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            Dict: 合并后的分析结果
        """
        # 创建合并结果的副本
        merged_analysis = user_analysis.copy()
        
        # 根据用户优先级权重决定如何合并
        if user_priority_weight >= 0.9:
            # 用户需求最高优先级，几乎不考虑PDF特征
            self.logger.info("用户需求优先级最高，仅将PDF信息作为参考")
            return merged_analysis
        elif user_priority_weight >= 0.7:
            # 用户需求高优先级，但适当考虑PDF特征
            self.logger.info("用户需求优先，适当参考PDF特征")
            # 将PDF中的材料信息添加到分析中
            if 'materials' in pdf_features and pdf_features['materials']:
                if 'material' not in merged_analysis or not merged_analysis['material']:
                    merged_analysis['material'] = pdf_features['materials'][0]
        else:
            # 平衡用户需求和PDF特征
            self.logger.info("平衡用户需求和PDF特征")
            # 添加更多PDF特征到分析中
            if 'materials' in pdf_features and pdf_features['materials']:
                merged_analysis['material'] = pdf_features['materials'][0]
            
            if 'dimensions' in pdf_features and pdf_features['dimensions']:
                if 'dimensions' not in merged_analysis or not merged_analysis['dimensions']:
                    merged_analysis['dimensions'] = pdf_features['dimensions'][:5]
        
        return merged_analysis
    
    def generate_with_hybrid_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        confidence_threshold: float = 0.7,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用混合方法生成NC程序
        根据特征完整性决定使用AI生成还是传统方法
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            confidence_threshold: 置信度阈值
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 首先尝试从PDF中提取特征
        pdf_features = {}
        if pdf_path:
            try:
                pdf_features = self.ocr_extractor(pdf_path)
            except Exception as e:
                self.logger.warning(f"PDF特征提取失败: {str(e)}")
        
        # 计算特征完整性
        feature_completeness = self._calculate_feature_completeness(
            user_prompt, pdf_features
        )
        
        # 根据特征完整性决定生成策略，但始终考虑用户优先级
        if feature_completeness >= confidence_threshold:
            # 特征完整，使用AI生成，确保用户需求优先
            return self._generate_with_ai_approach(user_prompt, pdf_path, image_path, user_priority_weight)
        else:
            # 特征不完整，结合AI和传统方法，强调用户需求
            return self._generate_with_enhanced_ai(user_prompt, pdf_features, user_priority_weight)
    
    def _calculate_feature_completeness(self, user_prompt: str, pdf_features: Dict) -> float:
        """
        计算特征完整性分数
        
        Args:
            user_prompt: 用户需求
            pdf_features: PDF特征
            
        Returns:
            float: 特征完整性分数 (0-1)
        """
        score = 0.0
        max_score = 4.0  # 最大可能分数
        
        # 检查基本加工类型是否明确
        processing_keywords = ['钻孔', '铣削', '沉孔', '攻丝', 'drill', 'mill', 'counterbore', 'tapping']
        if any(keyword in user_prompt.lower() for keyword in processing_keywords):
            score += 1.0
        
        # 检查是否有尺寸信息
        import re
        if re.search(r'φ?\d+\.?\d*', user_prompt):
            score += 0.5
        
        # 检查PDF中是否有材料信息
        if pdf_features.get('materials'):
            score += 0.5
        
        # 检查PDF中是否有尺寸标注
        if pdf_features.get('dimensions'):
            score += 1.0
        
        # 检查是否有位置信息
        if re.search(r'X\s*\d+\.?\d*\s*Y\s*[+-]?\d+\.?\d*', user_prompt):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def _generate_with_enhanced_ai(
        self, 
        user_prompt: str, 
        pdf_features: Dict,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用增强的AI方法生成NC程序
        结合PDF特征但以AI生成为主
        
        Args:
            user_prompt: 用户需求
            pdf_features: PDF特征
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 根据用户优先级权重创建详细的上下文提示
        if user_priority_weight >= 0.9:
            # 最高优先级：强烈强调用户需求
            context_prompt = f"""
            重要：严格按照以下用户需求生成NC程序。用户需求优先级最高。
            
            用户原始需求:
            {user_prompt}

            从图纸中提取的补充信息（仅在与用户需求一致时使用）:
            """
        elif user_priority_weight >= 0.7:
            # 高优先级：适度强调用户需求
            context_prompt = f"""
            请根据以下信息生成NC程序，优先满足用户需求：
            
            用户原始需求:
            {user_prompt}

            从图纸中提取的补充信息:
            """
        else:
            # 中等优先级：平衡用户需求和图纸信息
            context_prompt = f"""
            请根据以下完整信息生成NC程序：
            
            用户原始需求:
            {user_prompt}

            从图纸中提取的补充信息:
            """
        
        # 添加各种提取的信息
        if pdf_features.get('materials'):
            context_prompt += f"材料: {', '.join(pdf_features['materials'][:2])}\n"
        
        if pdf_features.get('dimensions'):
            context_prompt += f"关键尺寸: {', '.join(map(str, pdf_features['dimensions'][:5]))}\n"
        
        if pdf_features.get('hole_details'):
            context_prompt += f"孔特征: {', '.join(pdf_features['hole_details'][:3])}\n"
        
        if pdf_features.get('inferred_process_types'):
            context_prompt += f"建议加工类型: {', '.join(pdf_features['inferred_process_types'])}\n"
        
        if pdf_features.get('recommended_tool_sizes'):
            context_prompt += f"推荐刀具: {', '.join(pdf_features['recommended_tool_sizes'][:3])}\n"
        
        # 根据用户优先级权重添加冲突处理说明
        if user_priority_weight >= 0.9:
            context_prompt += """
            请综合考虑用户需求和图纸信息，生成最合适的NC程序。
            重要提醒：如果用户需求与图纸信息冲突，必须严格以用户需求为准。
            """
        elif user_priority_weight >= 0.7:
            context_prompt += """
            请综合考虑用户需求和图纸信息，生成最合适的NC程序。
            提醒：如果用户需求与图纸信息冲突，优先考虑用户需求。
            """
        else:
            context_prompt += """
            请综合考虑用户需求和图纸信息，生成最合适的NC程序。
            提醒：如果用户需求与图纸信息冲突，根据实际情况平衡考虑。
            """
        
        # 使用AI生成程序
        return self.ai_generator(context_prompt)

# 创建全局实例
unified_generator = UnifiedCNCGenerator()

def generate_cnc_with_unified_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    use_ai_primary: bool = True,
    user_priority_weight: float = 1.0
) -> str:
    """
    使用统一方法生成CNC程序
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        use_ai_primary: 是否优先使用AI驱动方法
        user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
        
    Returns:
        str: 生成的NC程序代码
    """
    return unified_generator.generate_cnc_program(
        user_prompt, pdf_path, image_path, use_ai_primary, user_priority_weight
    )

def generate_cnc_with_hybrid_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    confidence_threshold: float = 0.7,
    user_priority_weight: float = 1.0
) -> str:
    """
    使用混合方法生成CNC程序
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        confidence_threshold: 置信度阈值
        user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
        
    Returns:
        str: 生成的NC程序代码
    """
    return unified_generator.generate_with_hybrid_approach(
        user_prompt, pdf_path, image_path, confidence_threshold, user_priority_weight
    )
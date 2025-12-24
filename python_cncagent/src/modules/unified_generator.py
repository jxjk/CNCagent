"""
统一CNC程序生成入口
整合AI驱动、OCR推理和传统图像处理功能
"""
import logging
from typing import Dict, Optional, List
from pathlib import Path

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
        use_ai_primary: bool = True
    ) -> str:
        """
        生成CNC程序的统一接口
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            use_ai_primary: 是否优先使用AI驱动方法
            
        Returns:
            str: 生成的NC程序代码
        """
        if use_ai_primary:
            return self._generate_with_ai_approach(user_prompt, pdf_path, image_path)
        else:
            return self._generate_with_traditional_approach(user_prompt, pdf_path, image_path)
    
    def _generate_with_ai_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> str:
        """
        使用AI驱动方法生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            
        Returns:
            str: 生成的NC程序代码
        """
        # 如果有PDF，先提取特征
        if pdf_path:
            try:
                pdf_features = self.ocr_extractor(pdf_path)
                # 将PDF特征信息整合到用户提示中，提高AI生成的准确性
                enhanced_prompt = self._enhance_prompt_with_pdf_features(user_prompt, pdf_features)
                return self.ai_generator(enhanced_prompt, pdf_path)
            except Exception as e:
                self.logger.warning(f"PDF特征提取失败，回退到基础AI生成: {str(e)}")
                return self.ai_generator(user_prompt, pdf_path)
        else:
            # 直接使用AI生成
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
    
    def _generate_with_traditional_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> str:
        """
        使用传统方法生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            
        Returns:
            str: 生成的NC程序代码
        """
        # 分析用户描述
        description_analysis = self.description_analyzer(user_prompt)
        
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
        
        # 生成NC程序
        return self.traditional_generator(features, description_analysis)
    
    def generate_with_hybrid_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        confidence_threshold: float = 0.7
    ) -> str:
        """
        使用混合方法生成NC程序
        根据特征完整性决定使用AI生成还是传统方法
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            confidence_threshold: 置信度阈值
            
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
        
        # 根据特征完整性决定生成策略
        if feature_completeness >= confidence_threshold:
            # 特征完整，使用AI生成
            return self._generate_with_ai_approach(user_prompt, pdf_path, image_path)
        else:
            # 特征不完整，结合AI和传统方法
            return self._generate_with_enhanced_ai(user_prompt, pdf_features)
    
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
        pdf_features: Dict
    ) -> str:
        """
        使用增强的AI方法生成NC程序
        结合PDF特征但以AI生成为主
        
        Args:
            user_prompt: 用户需求
            pdf_features: PDF特征
            
        Returns:
            str: 生成的NC程序代码
        """
        # 创建详细的上下文提示
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
        
        context_prompt += """
        请综合考虑用户需求和图纸信息，生成最合适的NC程序。
        如果用户需求与图纸信息冲突，请优先考虑用户需求，但需在注释中说明。
        """
        
        # 使用AI生成程序
        return self.ai_generator(context_prompt)

# 创建全局实例
unified_generator = UnifiedCNCGenerator()

def generate_cnc_with_unified_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    use_ai_primary: bool = True
) -> str:
    """
    使用统一方法生成CNC程序
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        use_ai_primary: 是否优先使用AI驱动方法
        
    Returns:
        str: 生成的NC程序代码
    """
    return unified_generator.generate_cnc_program(
        user_prompt, pdf_path, image_path, use_ai_primary
    )

def generate_cnc_with_hybrid_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    confidence_threshold: float = 0.7
) -> str:
    """
    使用混合方法生成CNC程序
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        confidence_threshold: 置信度阈值
        
    Returns:
        str: 生成的NC程序代码
    """
    return unified_generator.generate_with_hybrid_approach(
        user_prompt, pdf_path, image_path, confidence_threshold
    )
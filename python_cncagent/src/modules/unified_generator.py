"""
统一CNC程序生成入口
重构：直接调用大模型生成NC代码，PDF特征仅作为辅助参考
"""
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

from src.exceptions import CNCError, InputValidationError, handle_exception
from .ai_driven_generator import generate_nc_with_ai
from .ocr_ai_inference import extract_features_from_pdf_with_ai
from .gcode_generation import generate_fanuc_nc  # 保留作为备用
from .material_tool_matcher import analyze_user_description
from .feature_definition import identify_features  # 保留作为备用

class UnifiedCNCGenerator:
    """
    统一CNC程序生成器
    直接调用大模型生成NC代码，PDF特征仅作为辅助参考
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        self.ai_generator = lambda user_prompt, pdf_path: generate_nc_with_ai(
            user_prompt, pdf_path, api_key=self.api_key, model=self.model
        )
        self.ocr_extractor = extract_features_from_pdf_with_ai
        # 传统方法仅作为备用选项
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
            use_ai_primary: 是否优先使用AI驱动方法（此参数现在已固定使用AI方法）
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
            # 重构：始终使用AI方法，PDF特征仅作为辅助参考
            return self._generate_with_ai_primary(user_prompt, pdf_path, image_path, user_priority_weight)
        except CNCError:
            # 如果已经是CNCError，直接重新抛出
            raise
        except Exception as e:
            error = handle_exception(e, self.logger, "生成CNC程序时出错")
            raise CNCError(f"生成CNC程序失败: {str(error)}", original_exception=e) from e
    
    def _generate_with_ai_primary(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用AI优先方法生成NC程序（重构后的方法）
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 直接使用AI生成，PDF特征仅作为辅助参考
        return self.ai_generator(user_prompt, pdf_path)
    
    def _generate_with_traditional_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        传统方法生成NC程序（已弃用，仅作为备用）
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        self.logger.warning("使用传统方法生成NC程序 - 此方法已弃用，仅作为备用")
        
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
        
        # 使用传统方法生成
        return self.traditional_generator(features, description_analysis)
    
    def generate_with_hybrid_approach(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        confidence_threshold: float = 0.7,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用混合方法生成NC程序（重构：仍以AI为主，PDF特征为辅）
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            confidence_threshold: 置信度阈值（此参数现在已忽略）
            user_priority_weight: 用户描述优先级权重（此参数现在已忽略）
            
        Returns:
            str: 生成的NC程序代码
        """
        # 重构：始终使用AI方法，PDF特征仅作为辅助参考
        self.logger.info("使用AI优先方法生成NC程序，PDF特征仅作为辅助参考")
        return self.ai_generator(user_prompt, pdf_path)
    
    def generate_from_description_only(self, user_prompt: str, material: str = "Aluminum") -> str:
        """
        仅根据用户描述生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            material: 材料类型
            
        Returns:
            str: 生成的NC程序代码
        """
        # 确保用户提示是字符串并正确处理中文字符
        if isinstance(user_prompt, bytes):
            try:
                user_prompt = user_prompt.decode('utf-8')
            except UnicodeError:
                user_prompt = user_prompt.decode('utf-8', errors='replace')
        elif not isinstance(user_prompt, str):
            user_prompt = str(user_prompt)
        
        # 直接使用AI生成器，PDF路径为None
        return self.ai_generator(user_prompt, pdf_path=None)


# 创建全局实例
unified_generator = UnifiedCNCGenerator()

def generate_cnc_with_unified_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    use_ai_primary: bool = True,
    user_priority_weight: float = 1.0,
    api_key: Optional[str] = None,
    model: str = "deepseek-chat"
) -> str:
    """
    使用统一方法生成CNC程序
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        use_ai_primary: 是否优先使用AI驱动方法
        user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
        api_key: 大模型API密钥
        model: 使用的模型名称
        
    Returns:
        str: 生成的NC程序代码
    """
    generator = UnifiedCNCGenerator(api_key=api_key, model=model)
    return generator.generate_cnc_program(
        user_prompt, pdf_path, image_path, use_ai_primary, user_priority_weight
    )

def generate_cnc_with_hybrid_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    confidence_threshold: float = 0.7,
    user_priority_weight: float = 1.0,
    api_key: Optional[str] = None,
    model: str = "deepseek-chat"
) -> str:
    """
    使用混合方法生成CNC程序（重构：主要使用AI方法）
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        confidence_threshold: 置信度阈值
        user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
        api_key: 大模型API密钥
        model: 使用的模型名称
        
    Returns:
        str: 生成的NC程序代码
    """
    generator = UnifiedCNCGenerator(api_key=api_key, model=model)
    return generator.generate_with_hybrid_approach(
        user_prompt, pdf_path, image_path, confidence_threshold, user_priority_weight
    )
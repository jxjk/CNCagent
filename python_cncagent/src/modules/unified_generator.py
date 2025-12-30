"""
统一CNC程序生成入口
重构：完全以大模型为中心，利用智能提示词构建器整合多源信息
移除了对传统方法的依赖，简化架构
"""
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

from src.exceptions import CNCError, InputValidationError, handle_exception
from .ai_driven_generator import generate_nc_with_ai
# 移除对传统方法的依赖
from .material_tool_matcher import analyze_user_description
# 移除了 feature_definition, gcode_generation 等传统模块的导入
from .model_3d_processor import process_3d_model, Model3DProcessor

class UnifiedCNCGenerator:
    """
    统一CNC程序生成器
    完全以大模型为中心，移除对传统方法的依赖
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        # 仅使用AI方法，移除传统方法依赖
        self.ai_generator = lambda user_prompt, pdf_path, image_path=None, model_3d_path=None: generate_nc_with_ai(
            user_prompt, pdf_path, image_path=image_path, model_3d_path=model_3d_path, api_key=self.api_key, model=self.model
        )
        self.description_analyzer = analyze_user_description
        # 移除对传统特征识别的依赖
    
    def generate_cnc_program(
        self, 
        user_prompt: str, 
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        model_3d_path: Optional[str] = None,
        use_ai_primary: bool = True,
        user_priority_weight: float = 1.0,
        enable_completeness_check: bool = False  # 默认关闭完整性检查，依赖大模型
    ) -> str:
        """
        生成CNC程序的统一接口 - 完全由大模型驱动
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            model_3d_path: 3D模型文件路径
            use_ai_primary: 此参数已废弃，始终使用AI方法
            user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
            enable_completeness_check: 是否启用特征完整性检查（现在默认关闭）
            
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
            
        if model_3d_path and not Path(model_3d_path).exists():
            raise InputValidationError(f"3D模型文件不存在: {model_3d_path}")
        
        if not 0.0 <= user_priority_weight <= 1.0:
            raise InputValidationError("用户优先级权重必须在0.0到1.0之间")
        
        try:
            # 简化流程：直接使用AI生成，移除传统验证步骤
            # 信任大模型的智能处理能力
            return self.ai_generator(user_prompt, pdf_path, image_path, model_3d_path)
            
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
        model_3d_path: Optional[str] = None,
        user_priority_weight: float = 1.0
    ) -> str:
        """
        使用AI生成NC程序
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            model_3d_path: 3D模型文件路径
            user_priority_weight: 用户描述优先级权重
            
        Returns:
            str: 生成的NC程序代码
        """
        # 如果有3D模型，将其信息整合到用户提示中以供AI使用
        if model_3d_path:
            try:
                # 处理3D模型并提取关键信息
                model_3d_features = process_3d_model(model_3d_path)
                geometric_features = model_3d_features.get('geometric_features', {})
                
                # 将3D模型信息添加到用户提示中
                model_info = f"\n\n3D模型信息:\n"
                model_info += f"- 模型类型: {model_3d_features.get('format', 'unknown')}\n"
                model_info += f"- 顶点数: {geometric_features.get('vertices_count', 'unknown')}\n"
                model_info += f"- 面数: {geometric_features.get('faces_count', 'unknown')}\n"
                model_info += f"- 体积: {geometric_features.get('volume', 'unknown')}\n"
                model_info += f"- 表面积: {geometric_features.get('surface_area', 'unknown')}\n"
                
                if geometric_features.get('bounding_box'):
                    bbox = geometric_features['bounding_box']
                    model_info += f"- 边界框: X({bbox['min'][0]:.2f}~{bbox['max'][0]:.2f}), Y({bbox['min'][1]:.2f}~{bbox['max'][1]:.2f}), Z({bbox['min'][2]:.2f}~{bbox['max'][2]:.2f})\n"
                
                if geometric_features.get('geometric_primitives'):
                    model_info += f"- 检测到的几何基元: {len(geometric_features['geometric_primitives'])}个\n"
                
                user_prompt += model_info
                self.logger.info(f"已将3D模型信息整合到用户提示中: {model_3d_path}")
            except Exception as e:
                self.logger.warning(f"处理3D模型时出错，将忽略3D模型信息: {str(e)}")
        
        # 直接使用AI生成
        return self.ai_generator(user_prompt, pdf_path, image_path, model_3d_path)
    
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
        
        # 检查当前实例是否有API密钥，如果没有则从环境变量获取
        if not self.api_key:
            import os
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
            model = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
            
            if api_key:
                # 创建新的AI生成器实例，使用环境变量中的API密钥
                temp_generator = lambda user_prompt, pdf_path: generate_nc_with_ai(
                    user_prompt, pdf_path, api_key=api_key, model=model
                )
                return temp_generator(user_prompt, pdf_path=None)
        
        # 直接使用AI生成器，PDF路径为None
        return self.ai_generator(user_prompt, pdf_path=None)


# 创建全局实例
unified_generator = UnifiedCNCGenerator()

def generate_cnc_with_unified_approach(
    user_prompt: str, 
    pdf_path: Optional[str] = None,
    image_path: Optional[str] = None,
    model_3d_path: Optional[str] = None,
    use_ai_primary: bool = True,  # 保留此参数以保持接口兼容性，但内部忽略
    user_priority_weight: float = 1.0,
    api_key: Optional[str] = None,
    model: str = "deepseek-chat",
    enable_completeness_check: bool = False  # 默认关闭完整性检查
) -> str:
    """
    使用统一方法生成CNC程序 - 完全由大模型驱动
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: PDF图纸路径
        image_path: 图像文件路径
        model_3d_path: 3D模型文件路径
        use_ai_primary: 此参数已废弃，始终使用AI方法
        user_priority_weight: 用户描述优先级权重 (0.0-1.0)，1.0表示最高优先级
        api_key: 大模型API密钥
        model: 使用的模型名称
        enable_completeness_check: 是否启用特征完整性检查（默认关闭）
        
    Returns:
        str: 生成的NC程序代码
    """
    generator = UnifiedCNCGenerator(api_key=api_key, model=model)
    return generator.generate_cnc_program(
        user_prompt, pdf_path, image_path, model_3d_path, use_ai_primary, user_priority_weight, enable_completeness_check
    )
"""
智能提示词构建器模块
将OCR、图纸、3D模型特征等多源信息整合为高质量提示词
用于驱动大模型生成高质量NC程序
"""
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from .pdf_parsing_process import extract_text_from_pdf, pdf_to_images, ocr_image
from .model_3d_processor import process_3d_model
from .feature_definition import identify_features
from .material_tool_matcher import analyze_user_description


class PromptBuilder:
    """
    智能提示词构建器
    将多源特征信息整合为高质量提示词，避免因描述不完整造成的NC程序质量不高
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_optimized_prompt(
        self,
        user_description: str,
        pdf_path: Optional[str] = None,
        image_path: Optional[str] = None,
        model_3d_path: Optional[str] = None,
        material: str = "Aluminum",
        precision_requirement: str = "General",
        process_constraints: Optional[Dict] = None
    ) -> str:
        """
        构建优化的提示词
        
        Args:
            user_description: 用户加工需求描述
            pdf_path: PDF图纸路径
            image_path: 图像文件路径
            model_3d_path: 3D模型文件路径
            material: 材料类型
            precision_requirement: 精度要求
            process_constraints: 加工约束条件
            
        Returns:
            str: 优化的提示词
        """
        # 分析用户描述
        description_analysis = analyze_user_description(user_description)
        
        # 构建基础提示词结构
        prompt_parts = []
        
        # 1. 系统角色设定
        prompt_parts.append(self._build_system_role_section())
        
        # 2. 工程图纸信息
        drawing_info = self._extract_drawing_info(pdf_path, image_path)
        if drawing_info:
            prompt_parts.append(self._build_drawing_info_section(drawing_info))
        
        # 3. 3D模型特征
        model_3d_info = self._extract_3d_model_info(model_3d_path)
        if model_3d_info:
            prompt_parts.append(self._build_3d_model_info_section(model_3d_info))
        
        # 4. 用户加工需求
        prompt_parts.append(self._build_user_requirement_section(user_description, description_analysis))
        
        # 5. 加工约束条件
        prompt_parts.append(self._build_process_constraints_section(
            material, precision_requirement, process_constraints, description_analysis
        ))
        
        # 6. 生成要求
        prompt_parts.append(self._build_generation_requirements_section())
        
        # 合并所有部分
        full_prompt = "\n\n".join(prompt_parts)
        return full_prompt
    
    def _build_system_role_section(self) -> str:
        """构建系统角色设定部分"""
        return f"""
你是业界顶尖的CNC编程工程师，拥有30年FANUC系统编程经验。
你精通机械加工工艺，能够根据图纸、3D模型和用户需求生成高质量的NC程序。
你的程序符合ISO标准，安全可靠，考虑了切削力、刀具寿命、表面质量等工艺要点。
        """.strip()
    
    def _extract_drawing_info(
        self, 
        pdf_path: Optional[str] = None, 
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """提取图纸信息"""
        drawing_info = {}
        
        # 从PDF提取文本信息
        if pdf_path:
            try:
                text_content = extract_text_from_pdf(pdf_path)
                drawing_info['pdf_text'] = text_content
                
                # 使用OCR处理PDF图像
                images = pdf_to_images(pdf_path)
                ocr_results = []
                for img in images:
                    ocr_result = ocr_image(img)
                    ocr_results.append(ocr_result)
                drawing_info['ocr_text'] = " ".join(ocr_results)
                
                # 识别图像特征
                features = []
                for img in images:
                    # 将PIL图像转换为numpy数组
                    import numpy as np
                    img_array = np.array(img.convert('L'))
                    img_features = identify_features(img_array, drawing_text=text_content)
                    features.extend(img_features)
                
                drawing_info['geometric_features'] = features
            except Exception as e:
                self.logger.warning(f"处理PDF图纸时出错: {str(e)}")
        
        # 从图像文件提取信息
        if image_path:
            try:
                from PIL import Image
                import numpy as np
                
                img = Image.open(image_path)
                img_array = np.array(img.convert('L'))
                
                # 识别几何特征
                features = identify_features(img_array)
                drawing_info['image_features'] = features
                
                # OCR识别
                ocr_result = ocr_image(img)
                drawing_info['image_ocr'] = ocr_result
            except Exception as e:
                self.logger.warning(f"处理图像文件时出错: {str(e)}")
        
        return drawing_info
    
    def _extract_3d_model_info(self, model_3d_path: Optional[str] = None) -> Dict[str, Any]:
        """提取3D模型信息"""
        if not model_3d_path:
            return {}
        
        try:
            # 处理3D模型
            model_features = process_3d_model(model_3d_path)
            
            # 转换为更适合NC生成的格式
            processed_info = {
                'format': model_features.get('format', 'unknown'),
                'geometric_features': model_features.get('geometric_features', {}),
                'dimensional_info': self._extract_dimensional_info(model_features),
                'process_features': self._identify_process_features(model_features),
                'material_info': model_features.get('material_info', {})
            }
            
            return processed_info
        except Exception as e:
            self.logger.warning(f"处理3D模型时出错: {str(e)}")
            return {}
    
    def _extract_dimensional_info(self, model_features: Dict) -> Dict[str, Any]:
        """从3D模型中提取尺寸信息"""
        geometric_features = model_features.get('geometric_features', {})
        dimensional_info = {}
        
        # 提取边界框信息
        if 'bounding_box' in geometric_features:
            bbox = geometric_features['bounding_box']
            dimensional_info['bounding_box'] = {
                'x_range': [bbox['min'][0], bbox['max'][0]],
                'y_range': [bbox['min'][1], bbox['max'][1]],
                'z_range': [bbox['min'][2], bbox['max'][2]],
                'dimensions': [
                    bbox['max'][0] - bbox['min'][0],  # 长度
                    bbox['max'][1] - bbox['min'][1],  # 宽度
                    bbox['max'][2] - bbox['min'][2]   # 高度
                ]
            }
        
        # 提取体积和表面积
        if 'volume' in geometric_features:
            dimensional_info['volume'] = geometric_features['volume']
        
        if 'surface_area' in geometric_features:
            dimensional_info['surface_area'] = geometric_features['surface_area']
        
        return dimensional_info
    
    def _identify_process_features(self, model_features: Dict) -> List[Dict]:
        """识别加工特征"""
        geometric_primitives = model_features.get('geometric_primitives', [])
        process_features = []
        
        for primitive in geometric_primitives:
            feature_type = primitive.get('type', 'unknown')
            
            if feature_type in ['cylinder', 'cone', 'sphere']:
                # 孔、凸台等特征
                process_features.append({
                    'type': 'hole' if 'hole' in primitive.get('name', '').lower() else 'protrusion',
                    'dimensions': primitive.get('dimensions', {}),
                    'position': primitive.get('position', [0, 0, 0])
                })
            elif feature_type == 'box':
                # 平面、槽等特征
                process_features.append({
                    'type': 'plane',
                    'dimensions': primitive.get('dimensions', {}),
                    'position': primitive.get('position', [0, 0, 0])
                })
            elif feature_type == 'extrusion':
                # 凸台、槽等特征
                process_features.append({
                    'type': 'extrusion',
                    'dimensions': primitive.get('dimensions', {}),
                    'position': primitive.get('position', [0, 0, 0])
                })
        
        return process_features
    
    def _build_drawing_info_section(self, drawing_info: Dict[str, Any]) -> str:
        """构建图纸信息部分"""
        sections = ["# 图纸信息"]
        
        if 'pdf_text' in drawing_info:
            sections.append(f"## PDF文本内容:\n{drawing_info['pdf_text'][:500]}...")  # 限制长度
        
        if 'ocr_text' in drawing_info:
            sections.append(f"## OCR识别文本:\n{drawing_info['ocr_text'][:500]}...")
        
        if 'geometric_features' in drawing_info:
            features = drawing_info['geometric_features']
            feature_summary = self._summarize_geometric_features(features)
            sections.append(f"## 几何特征:\n{feature_summary}")
        
        if 'image_features' in drawing_info:
            features = drawing_info['image_features']
            feature_summary = self._summarize_geometric_features(features)
            sections.append(f"## 图像几何特征:\n{feature_summary}")
        
        return "\n\n".join(sections)
    
    def _summarize_geometric_features(self, features: List[Dict]) -> str:
        """总结几何特征"""
        if not features:
            return "未识别到几何特征"
        
        summary_parts = []
        for i, feature in enumerate(features[:10]):  # 限制为前10个特征
            shape = feature.get('shape', 'unknown')
            center = feature.get('center', [0, 0])
            dimensions = feature.get('dimensions', [])
            confidence = feature.get('confidence', 1.0)
            
            summary_parts.append(
                f"特征{i+1}: {shape}, 位置{center}, 尺寸{dimensions}, 置信度{confidence:.2f}"
            )
        
        return "\n".join(summary_parts)
    
    def _build_3d_model_info_section(self, model_3d_info: Dict[str, Any]) -> str:
        """构建3D模型信息部分"""
        sections = ["# 3D模型信息"]
        
        if 'format' in model_3d_info:
            sections.append(f"## 模型格式: {model_3d_info['format']}")
        
        if 'dimensional_info' in model_3d_info:
            dim_info = model_3d_info['dimensional_info']
            if 'bounding_box' in dim_info:
                bbox = dim_info['bounding_box']
                sections.append(f"## 尺寸信息:")
                sections.append(f"- 长度: {bbox['dimensions'][0]:.2f}mm")
                sections.append(f"- 宽度: {bbox['dimensions'][1]:.2f}mm") 
                sections.append(f"- 高度: {bbox['dimensions'][2]:.2f}mm")
                sections.append(f"- X轴范围: {bbox['x_range'][0]:.2f} ~ {bbox['x_range'][1]:.2f}mm")
                sections.append(f"- Y轴范围: {bbox['y_range'][0]:.2f} ~ {bbox['y_range'][1]:.2f}mm")
                sections.append(f"- Z轴范围: {bbox['z_range'][0]:.2f} ~ {bbox['z_range'][1]:.2f}mm")
            
            if 'volume' in dim_info:
                sections.append(f"- 体积: {dim_info['volume']:.2f}mm³")
            
            if 'surface_area' in dim_info:
                sections.append(f"- 表面积: {dim_info['surface_area']:.2f}mm²")
        
        if 'process_features' in model_3d_info:
            process_features = model_3d_info['process_features']
            if process_features:
                sections.append("## 识别的加工特征:")
                for i, feature in enumerate(process_features[:10]):  # 限制为前10个
                    sections.append(f"- {feature['type']}: 位置{feature['position']}, 尺寸{feature.get('dimensions', {})})")
        
        return "\n\n".join(sections)
    
    def _build_user_requirement_section(self, user_description: str, description_analysis: Dict) -> str:
        """构建用户需求部分"""
        sections = ["# 用户加工需求"]
        
        sections.append(f"## 原始描述:\n{user_description}")
        
        # 分析结果
        analysis_summary = []
        if 'processing_type' in description_analysis:
            analysis_summary.append(f"加工类型: {description_analysis['processing_type']}")
        if 'material' in description_analysis:
            analysis_summary.append(f"材料: {description_analysis['material']}")
        if 'depth' in description_analysis:
            analysis_summary.append(f"加工深度: {description_analysis['depth']}mm")
        if 'workpiece_dimensions' in description_analysis:
            dims = description_analysis['workpiece_dimensions']
            analysis_summary.append(f"工件尺寸: {dims[0]}x{dims[1]}x{dims[2]}mm")
        
        if analysis_summary:
            sections.append(f"## 需求分析:\n" + "\n".join(f"- {item}" for item in analysis_summary))
        
        return "\n\n".join(sections)
    
    def _build_process_constraints_section(
        self, 
        material: str, 
        precision_requirement: str, 
        process_constraints: Optional[Dict],
        description_analysis: Dict
    ) -> str:
        """构建加工约束部分"""
        sections = ["# 加工约束条件"]
        
        # 材料约束
        sections.append(f"## 材料: {material}")
        
        # 精度要求
        sections.append(f"## 精度要求: {precision_requirement}")
        
        # 从描述分析中提取的约束
        constraints_from_analysis = []
        if 'tool_required' in description_analysis:
            constraints_from_analysis.append(f"刀具要求: {description_analysis['tool_required']}")
        if 'feed_rate' in description_analysis:
            constraints_from_analysis.append(f"进给要求: {description_analysis['feed_rate']}mm/min")
        if 'spindle_speed' in description_analysis:
            constraints_from_analysis.append(f"转速要求: {description_analysis['spindle_speed']}rpm")
        if 'precision' in description_analysis:
            constraints_from_analysis.append(f"精度要求: {description_analysis['precision']}")
        
        if constraints_from_analysis:
            sections.append("## 从描述中提取的约束:\n" + "\n".join(f"- {item}" for item in constraints_from_analysis))
        
        # 用户提供的额外约束
        if process_constraints:
            extra_constraints = []
            for key, value in process_constraints.items():
                extra_constraints.append(f"{key}: {value}")
            if extra_constraints:
                sections.append("## 额外约束:\n" + "\n".join(f"- {item}" for item in extra_constraints))
        
        return "\n\n".join(sections)
    
    def _build_generation_requirements_section(self) -> str:
        """构建生成要求部分"""
        return """
# NC程序生成要求

## 必须包含的元素
1. 完整的FANUC G代码格式
2. 合理的刀具路径规划
3. 优化的切削参数（转速、进给、切削深度、步距）
4. 安全操作（安全高度、冷却液控制、刀具补偿）
5. 工艺顺序优化

## 工艺要点考虑（详细工艺知识）
- 刀具直径与工件尺寸的匹配：铣削时步距通常为刀具直径的40-60%，钻削时进给为直径的0.05-0.2mm/rev
- 切削力对加工的影响：粗加工时降低进给和切削深度以减少切削力，精加工时优化参数以获得良好表面质量
- 加工余量分配：粗铣预留0.15-0.25mm精加工余量，根据材料硬度调整
- 表面质量要求：精加工时降低进给速度，提高主轴转速
- 刀具寿命优化：合理分配切削负荷，避免过载
- 加工效率：优化刀具路径以减少空行程时间

## 材料相关工艺参数
- 铝合金：主轴转速800-2000rpm，进给速度500-1500mm/min，切削深度1-3mm
- 钢材：主轴转速400-800rpm，进给速度200-500mm/min，切削深度0.5-2mm
- 不锈钢：主轴转速300-600rpm，进给速度100-300mm/min，切削深度0.3-1mm
- 铸铁：主轴转速500-1000rpm，进给速度300-800mm/min，切削深度1-2mm

## 刀具选择指南
- 面铣：使用面铣刀，直径根据加工面积选择（大平面用大直径刀具）
- 轮廓铣：使用立铣刀，直径根据最小内圆角选择
- 钻孔：钻头直径=目标孔径，或先用中心钻定位
- 攻丝：先钻底孔（螺纹直径-螺距），再用丝锥攻丝

## 安全要求
- 程序开始前的安全检查：确认工件装夹、刀具安装、冷却液开启
- 加工过程中的安全高度控制：非切削移动使用安全高度（通常100mm）
- 程序结束后的安全操作：返回安全位置，停止主轴，关闭冷却液
- 异常情况处理：程序中包含安全暂停点

## 特殊工艺要求
- 对于大平面铣削：采用往复或螺旋路径，确保表面平整
- 对于深孔加工：使用深孔钻削循环(G83)，分段排屑
- 对于螺纹加工：使用攻丝循环(G84)，确保主轴转速与进给同步
- 对于精加工：采用顺铣方式以获得更好表面质量

请生成完整、安全、高效的NC程序，确保所有工艺要点都得到充分考虑，输出格式为标准FANUC G代码。
        """.strip()


# 创建全局实例
prompt_builder = PromptBuilder()

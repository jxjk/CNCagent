"""
用户需求解析和澄清机制
使用AI对话功能来澄清用户模糊的需求
"""
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class RequirementClarification:
    """需求澄清结果"""
    is_clear: bool
    missing_info: List[str]
    suggested_questions: List[str]
    processed_requirements: Dict
    confidence_score: float

class RequirementClarifier:
    """
    用户需求澄清器
    使用AI对话功能来澄清模糊的用户需求
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 定义需要澄清的关键信息类型
        self.key_info_types = [
            '加工类型', '材料类型', '加工深度', '刀具规格', 
            '加工精度', '表面粗糙度', '热处理要求',
            '孔位置', '几何尺寸', '加工数量'
        ]
    
    def analyze_requirement_clarity(self, user_prompt: str) -> RequirementClarification:
        """
        分析用户需求的清晰度
        
        Args:
            user_prompt: 用户原始需求
            
        Returns:
            RequirementClarification: 需求澄清结果
        """
        analysis_result = {
            "processing_type": self._extract_processing_type(user_prompt),
            "material": self._extract_material(user_prompt),
            "depth": self._extract_depth(user_prompt),
            "dimensions": self._extract_dimensions(user_prompt),
            "positions": self._extract_positions(user_prompt),
            "quantity": self._extract_quantity(user_prompt),
            "tolerance": self._extract_tolerance(user_prompt)
        }
        
        # 检查哪些信息缺失
        missing_info = []
        for key, value in analysis_result.items():
            if not value:
                missing_info.append(self._map_key_to_description(key))
        
        # 生成建议问题
        suggested_questions = self._generate_suggested_questions(missing_info, user_prompt)
        
        # 计算置信度（基于提取到的信息比例）
        total_info_types = len(analysis_result)
        filled_info_types = sum(1 for v in analysis_result.values() if v)
        confidence_score = filled_info_types / total_info_types if total_info_types > 0 else 0
        
        is_clear = confidence_score >= 0.7  # 如果70%以上信息已知，则认为需求清晰
        
        return RequirementClarification(
            is_clear=is_clear,
            missing_info=missing_info,
            suggested_questions=suggested_questions,
            processed_requirements=analysis_result,
            confidence_score=confidence_score
        )
    
    def _extract_processing_type(self, prompt: str) -> str:
        """提取加工类型"""
        processing_types = {
            'drilling': ['钻', '孔', 'drill', 'hole'],
            'milling': ['铣', 'mill', 'cut', '铣削'],
            'turning': ['车', 'turn', '车削'],
            'grinding': ['磨', 'grind', '磨削'],
            'tapping': ['攻丝', '螺纹', 'tap', 'thread'],
            'counterboring': ['沉孔', '锪孔', 'counterbore', 'counter bore']
        }
        
        prompt_lower = prompt.lower()
        for proc_type, keywords in processing_types.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return proc_type
        
        return ""
    
    def _extract_material(self, prompt: str) -> str:
        """提取材料信息"""
        material_patterns = [
            r'(?:材料|材质|Material)[：:]\s*([A-Z0-9\s-]+)',
            r'(?:材料|材质|Material)\s+([A-Z0-9\s-]+)',
            r'(45#|40Cr|35CrMo|铝合金|不锈钢|铜|铝|钢|铁)',
        ]
        
        import re
        for pattern in material_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def _extract_depth(self, prompt: str) -> float:
        """提取深度信息"""
        import re
        depth_patterns = [
            r'(?:深|depth)\s*(\d+\.?\d*)\s*mm?',
            r'(?:深|depth)[：:]\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*mm\s*(?:深|depth)'
        ]
        
        for pattern in depth_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        
        return 0.0
    
    def _extract_dimensions(self, prompt: str) -> List[str]:
        """提取尺寸信息"""
        import re
        # 匹配直径、半径等尺寸标注
        dimension_patterns = [
            r'φ\s*(\d+\.?\d*)',  # 直径
            r'R\s*(\d+\.?\d*)',  # 半径
            r'(\d+\.?\d*)\s*[x*]\s*(\d+\.?\d*)',  # 长x宽
            r'(\d+\.?\d*)\s*[x*]\s*(\d+\.?\d*)\s*[x*]\s*(\d+\.?\d*)'  # 长x宽x高
        ]
        
        dimensions = []
        for pattern in dimension_patterns:
            matches = re.findall(pattern, prompt)
            for match in matches:
                if isinstance(match, tuple):
                    dimensions.append('x'.join(match))
                else:
                    dimensions.append(match)
        
        return dimensions
    
    def _extract_positions(self, prompt: str) -> List[Tuple[float, float]]:
        """提取位置信息"""
        import re
        # 匹配X、Y坐标
        pos_patterns = [
            r'X\s*(\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)',
            r'位置[：:]?\s*X?\s*(\d+\.?\d*)\s*,?\s*Y?\s*([+-]?\d+\.?\d*)',
            r'\((\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)\)'  # (x,y)格式
        ]
        
        positions = []
        for pattern in pos_patterns:
            matches = re.findall(pattern, prompt)
            for match in matches:
                try:
                    x = float(match[0])
                    y = float(match[1])
                    positions.append((x, y))
                except (ValueError, IndexError):
                    continue
        
        return positions
    
    def _extract_quantity(self, prompt: str) -> int:
        """提取数量信息"""
        import re
        quantity_patterns = [
            r'(\d+)\s*个',
            r'([一二三四五六七八九十\d]+)\s*件',
            r'数量[：:]?\s*(\d+)',
            r'总共[：:]?\s*(\d+)'
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, prompt)
            for match in matches:
                # 处理中文数字
                if match in ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']:
                    chinese_to_arabic = {
                        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
                    }
                    return chinese_to_arabic.get(match, 0)
                else:
                    try:
                        return int(match)
                    except ValueError:
                        continue
        
        return 0
    
    def _extract_tolerance(self, prompt: str) -> str:
        """提取公差信息"""
        import re
        tolerance_patterns = [
            r'([±+−]\s*\d+\.?\d*)\s*mm?',
            r'公差[：:]?\s*([±+−]\s*\d+\.?\d*)',
            r'IT\d+',  # IT等级
            r'(?:H\d+|h\d+|k\d+|K\d+)'  # 基孔制/轴制
        ]
        
        for pattern in tolerance_patterns:
            matches = re.findall(pattern, prompt)
            if matches:
                return matches[0]
        
        return ""
    
    def _map_key_to_description(self, key: str) -> str:
        """将键映射到描述"""
        mapping = {
            'processing_type': '加工类型',
            'material': '材料规格',
            'depth': '加工深度',
            'dimensions': '几何尺寸',
            'positions': '加工位置',
            'quantity': '加工数量',
            'tolerance': '尺寸公差'
        }
        return mapping.get(key, key)
    
    def _generate_suggested_questions(self, missing_info: List[str], original_prompt: str) -> List[str]:
        """生成建议的澄清问题"""
        questions = []
        
        for info_type in missing_info:
            if info_type == '加工类型':
                questions.append("请问具体需要进行什么类型的加工？例如：钻孔、铣削、沉孔等。")
            elif info_type == '材料规格':
                questions.append("请提供工件的材料信息，例如：45#钢、铝合金、不锈钢等。")
            elif info_type == '加工深度':
                questions.append("请提供具体的加工深度要求，单位为毫米(mm)。")
            elif info_type == '几何尺寸':
                questions.append("请提供具体的几何尺寸，如孔径、外形尺寸等。")
            elif info_type == '加工位置':
                questions.append("请提供加工位置的坐标信息，如X、Y坐标。")
            elif info_type == '加工数量':
                questions.append("请提供需要加工的数量。")
            elif info_type == '尺寸公差':
                questions.append("请提供尺寸公差要求，如±0.1mm。")
        
        # 如果原始提示中提到图纸，建议上传图纸
        if any(keyword in original_prompt.lower() for keyword in ['图纸', '图', 'drawing', 'pdf']):
            questions.insert(0, "如果有详细的技术图纸，请提供PDF文件，我可以从中提取详细的技术信息。")
        
        return questions
    
    def generate_clarification_dialogue(self, user_prompt: str) -> str:
        """
        生成需求澄清对话
        
        Args:
            user_prompt: 用户原始需求
            
        Returns:
            str: 澄清对话内容
        """
        clarification = self.analyze_requirement_clarity(user_prompt)
        
        dialogue = []
        dialogue.append("根据您的需求，我需要进一步了解以下信息以生成准确的NC程序：\n")
        
        for i, question in enumerate(clarification.suggested_questions, 1):
            dialogue.append(f"{i}. {question}")
        
        if clarification.processed_requirements.get('processing_type'):
            dialogue.append(f"\n根据我的分析，您可能需要进行{clarification.processed_requirements['processing_type']}加工。")
        
        dialogue.append(f"\n当前需求清晰度评分: {clarification.confidence_score:.1%}")
        if clarification.confidence_score < 0.5:
            dialogue.append("建议提供更多信息以获得更准确的程序生成。")
        elif clarification.confidence_score < 0.8:
            dialogue.append("请考虑回答上述问题以优化程序生成。")
        else:
            dialogue.append("需求信息相对完整，可以生成程序。")
        
        return "\n".join(dialogue)
    
    def get_enhanced_requirements(self, original_prompt: str, answers: Dict[str, str]) -> str:
        """
        结合用户回答生成增强的需求描述
        
        Args:
            original_prompt: 原始需求
            answers: 用户对澄清问题的回答
            
        Returns:
            str: 增强后的需求描述
        """
        enhanced_prompt = f"原始需求: {original_prompt}\n\n补充信息:\n"
        
        for question, answer in answers.items():
            if answer.strip():
                enhanced_prompt += f"- {question}: {answer}\n"
        
        return enhanced_prompt

# 创建全局实例
clarifier = RequirementClarifier()

def analyze_requirement_clarity(user_prompt: str) -> RequirementClarification:
    """
    分析用户需求的清晰度
    
    Args:
        user_prompt: 用户原始需求
        
    Returns:
        RequirementClarification: 需求分析结果
    """
    return clarifier.analyze_requirement_clarity(user_prompt)

def generate_clarification_dialogue(user_prompt: str) -> str:
    """
    生成需求澄清对话
    
    Args:
        user_prompt: 用户原始需求
        
    Returns:
        str: 澄清对话内容
    """
    return clarifier.generate_clarification_dialogue(user_prompt)

def get_enhanced_requirements(original_prompt: str, answers: Dict[str, str]) -> str:
    """
    获取增强后的需求描述
    
    Args:
        original_prompt: 原始需求
        answers: 用户回答
        
    Returns:
        str: 增强后的需求描述
    """
    return clarifier.get_enhanced_requirements(original_prompt, answers)
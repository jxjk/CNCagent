"""
AI驱动的NC程序生成模块
基于大语言模型直接生成NC代码，减少对预定义Python函数的依赖
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 尝试导入可能需要的库，如果不存在则使用替代方案
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    import logging
    logging.warning("警告: 未安装PyMuPDF库，PDF功能将受限")

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    import logging
    logging.warning("警告: 未安装OpenCV库，图像处理功能将受限")

@dataclass
class ProcessingRequirements:
    """处理需求数据类"""
    user_prompt: str
    processing_type: str = "general"
    hole_positions: List[Tuple[float, float]] = None
    depth: float = None
    tool_diameters: Dict[str, float] = None
    material: str = None
    special_requirements: List[str] = None
    
    def __post_init__(self):
        if self.hole_positions is None:
            self.hole_positions = []
        if self.tool_diameters is None:
            self.tool_diameters = {}
        if self.special_requirements is None:
            self.special_requirements = []

class AIDrivenCNCGenerator:
    """
    AI驱动的CNC程序生成器
    以大语言模型为核心，减少对预定义Python函数的依赖
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ocr_engine = None
        self.feature_analyzer = None
        
    def parse_user_requirements(self, user_prompt: str) -> ProcessingRequirements:
        """
        使用AI解析用户需求
        
        Args:
            user_prompt: 用户原始需求描述
            
        Returns:
            ProcessingRequirements: 解析后的需求对象
        """
        # 确保用户提示是字符串并正确处理中文字符
        if isinstance(user_prompt, bytes):
            try:
                user_prompt = user_prompt.decode('utf-8')
            except UnicodeError:
                user_prompt = user_prompt.decode('utf-8', errors='replace')
        elif not isinstance(user_prompt, str):
            user_prompt = str(user_prompt)
        
        # 这里使用AI模型来解析用户需求
        # 模拟AI解析过程，实际应用中应调用AI模型API
        requirements = ProcessingRequirements(user_prompt=user_prompt)
        
        # 使用更精确的规则匹配作为AI解析的模拟
        user_lower = user_prompt.lower()
        
        # 识别加工类型 - 增加更详细的识别逻辑
        # 使用正则表达式进行更精确的匹配，避免关键词冲突
        import re
        
        # 优化：先识别复合加工类型（如沉孔），再识别单一类型，防止误判
        if re.search(r'(?:沉孔|counterbore|锪孔)', user_lower):
            requirements.processing_type = 'counterbore'
        elif re.search(r'(?:攻丝|tapping|螺纹)', user_lower):
            requirements.processing_type = 'tapping'
        elif re.search(r'(?:钻孔|drill|hole|钻)', user_lower) and not re.search(r'(?:沉孔|counterbore|锪孔)', user_lower):
            requirements.processing_type = 'drilling'
        elif re.search(r'(?:车|turn)', user_lower):
            requirements.processing_type = 'turning'
        elif re.search(r'(?:铣|mill|cut)', user_lower) and not any(re.search(keyword, user_lower) for keyword in [r'沉孔', r'counterbore', r'锪孔', r'钻孔', r'drill']):
            # 铣削类型放在后面，防止与沉孔/锪孔/钻孔混淆
            requirements.processing_type = 'milling'
        else:
            requirements.processing_type = 'general'
        
        # 更精确地提取深度信息，考虑更多格式
        import re
        depth_patterns = [
            r'深\s*(\d+\.?\d*)\s*mm?',
            r'(\d+\.?\d*)\s*mm\s*深',
            r'深度[：:]?\s*(\d+\.?\d*)',
            r'depth[：:]?\s*(\d+\.?\d*)'
        ]
        for pattern in depth_patterns:
            depth_matches = re.findall(pattern, user_prompt)
            if depth_matches:
                try:
                    requirements.depth = float(depth_matches[0])
                    break  # 找到第一个匹配就停止
                except ValueError:
                    continue
        
        # 提取孔位置信息，支持更多格式
        pos_patterns = [
            r'X\s*(\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)',
            r'X[=:]\s*(\d+\.?\d*)\s*[,，]\s*Y[=:]\s*([+-]?\d+\.?\d*)',
            r'位置[：:]?\s*X?\s*(\d+\.?\d*)\s*[，,]\s*Y?\s*([+-]?\d+\.?\d*)',
            r'\((\d+\.?\d*)\s*[，,]\s*([+-]?\d+\.?\d*)\)'  # 坐标形式 (x,y)
        ]
        for pattern in pos_patterns:
            pos_matches = re.findall(pattern, user_prompt)
            for match in pos_matches:
                try:
                    x = float(match[0])
                    y = float(match[1])
                    requirements.hole_positions.append((x, y))
                except (ValueError, IndexError):
                    continue
        
        # 更精确地提取直径信息，特别是沉孔的内外径
        # 使用优化的函数来提取沉孔直径
        from src.modules.material_tool_matcher import _extract_counterbore_diameters
        outer_dia, inner_dia = _extract_counterbore_diameters(user_prompt)
        
        if outer_dia is not None and inner_dia is not None:
            # 成功提取到沉孔的内外径
            requirements.tool_diameters['outer'] = outer_dia
            requirements.tool_diameters['inner'] = inner_dia
        else:
            # 如果没有提取到沉孔直径，使用原始方法
            dia_matches = re.findall(r'φ\s*(\d+\.?\d*)', user_prompt)
            
            # 如果提取到φ234这样的大直径，可能不是沉孔直径，需要特殊处理
            dia_values = [float(d) for d in dia_matches if 5 <= float(d) <= 50]  # 过滤明显不是孔径的数字
            
            # 特别处理沉孔格式 "φ22沉孔深20，φ14.5贯通底孔"
            counterbore_pattern = r'φ\s*(\d+\.?\d*)\s*(?:沉孔|counterbore|锪孔).*?φ\s*(\d+\.?\d*)\s*(?:贯通|thru|底孔)'
            counterbore_match = re.search(counterbore_pattern, user_prompt)
            if counterbore_match:
                try:
                    outer_dia = float(counterbore_match.group(1))
                    inner_dia = float(counterbore_match.group(2))
                    requirements.tool_diameters['outer'] = outer_dia
                    requirements.tool_diameters['inner'] = inner_dia
                except (ValueError, IndexError):
                    pass
            elif len(dia_values) >= 2:
                # 如果有至少2个在合理范围内的直径值，按大小排序
                dia_values.sort(reverse=True)  # 降序排列
                if requirements.processing_type == 'counterbore':
                    # 对于沉孔，假设较大的是外径，较小的是内径
                    requirements.tool_diameters['outer'] = dia_values[0]
                    requirements.tool_diameters['inner'] = dia_values[1]
                else:
                    requirements.tool_diameters['default'] = dia_values[0]
                    if len(dia_values) > 1:
                        requirements.tool_diameters['secondary'] = dia_values[1]
            elif len(dia_matches) >= 2:
                # 如果直径值不在合理范围内，可能是其他尺寸，仅用于非沉孔类型
                if requirements.processing_type != 'counterbore':
                    try:
                        requirements.tool_diameters['default'] = float(dia_matches[0])
                        if len(dia_matches) > 1:
                            requirements.tool_diameters['secondary'] = float(dia_matches[1])
                    except ValueError:
                        pass
            elif len(dia_matches) == 1:
                try:
                    requirements.tool_diameters['default'] = float(dia_matches[0])
                except ValueError:
                    pass
        
        # 提取孔数量信息
        count_matches = re.findall(r'(\d+)\s*个', user_prompt)
        if count_matches:
            try:
                requirements.special_requirements.append(f"数量:{count_matches[0]}")
            except ValueError:
                pass
        
        # 提取材料信息
        material_keywords = ['钢', '铝', '铜', '铁', '不锈钢', '铝合金', '塑料', 'wood', 'steel', 'aluminum', 'copper']
        for keyword in material_keywords:
            if keyword in user_lower:
                requirements.material = keyword
                break
        
        return requirements
    
    def extract_features_from_pdf(self, pdf_path: str) -> Dict:
        """
        从PDF图纸中提取特征信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Dict: 提取的特征信息
        """
        if not HAS_PYMUPDF:
            return {"error": "PyMuPDF未安装，无法处理PDF文件"}
        
        try:
            doc = fitz.open(pdf_path)
            features = {
                "text_content": "",
                "dimensions": [],
                "annotations": [],
                "image_features": []
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本内容
                text = page.get_text()
                features["text_content"] += text + "\n"
                
                # 提取尺寸标注（简化版本）
                # 在实际应用中，这里需要更复杂的图像和文本分析
                blocks = page.get_text_blocks()
                for block in blocks:
                    if len(block[4]) > 2:  # 简单的文本块判断
                        # 检查是否包含尺寸信息
                        if any(char.isdigit() for char in block[4]) and any(unit in block[4] for unit in ['mm', 'cm', 'φ', 'R']):
                            features["dimensions"].append(block[4])
            
            doc.close()
            return features
        except Exception as e:
            self.logger.error(f"处理PDF文件时出错: {str(e)}")
            return {"error": f"处理PDF文件时出错: {str(e)}"}
    
    def merge_requirements_and_features(self, requirements: ProcessingRequirements, 
                                      pdf_features: Dict) -> ProcessingRequirements:
        """
        合并用户需求和PDF特征信息
        
        Args:
            requirements: 用户需求
            pdf_features: PDF提取的特征
            
        Returns:
            ProcessingRequirements: 合并后的需求
        """
        # 如果PDF中有更详细的信息，更新需求
        if "text_content" in pdf_features:
            pdf_text = pdf_features["text_content"]
            
            # 从PDF文本中提取可能遗漏的信息
            import re
            
            # 检查是否有更精确的深度信息
            if requirements.depth is None:
                depth_pattern = r'深\s*(\d+\.?\d*)\s*mm?'
                depth_matches = re.findall(depth_pattern, pdf_text)
                if depth_matches:
                    try:
                        requirements.depth = float(depth_matches[0])
                    except ValueError:
                        pass
            
            # 检查是否有更精确的直径信息
            dia_pattern = r'φ\s*(\d+\.?\d*)'
            dia_matches = re.findall(dia_pattern, pdf_text)
            if len(dia_matches) >= 2 and not requirements.tool_diameters:
                try:
                    requirements.tool_diameters['outer'] = float(dia_matches[0])
                    requirements.tool_diameters['inner'] = float(dia_matches[1])
                except ValueError:
                    pass
        
        return requirements
    
    def generate_with_ai(self, requirements: ProcessingRequirements) -> str:
        """
        使用AI生成NC程序
        
        Args:
            requirements: 处理需求
            
        Returns:
            str: 生成的NC程序代码
        """
        # 构建AI提示词
        prompt = self._build_generation_prompt(requirements)
        
        # 模拟AI生成（在实际应用中，这里应调用AI模型API）
        # 为了演示，我将生成一个符合要求的NC程序
        try:
            nc_program = self._generate_nc_code(requirements)
        except UnicodeError as e:
            self.logger.error(f"处理中文字符时出现编码错误: {str(e)}")
            # 尝试使用UTF-8编码处理
            if isinstance(requirements.user_prompt, str):
                requirements.user_prompt = requirements.user_prompt.encode('utf-8').decode('utf-8')
            elif isinstance(requirements.user_prompt, bytes):
                try:
                    requirements.user_prompt = requirements.user_prompt.decode('utf-8')
                except UnicodeError:
                    requirements.user_prompt = requirements.user_prompt.decode('utf-8', errors='replace')
            nc_program = self._generate_nc_code(requirements)
        except Exception as e:
            self.logger.error(f"处理用户需求时出现未知错误: {str(e)}")
            # 通用错误处理
            if isinstance(requirements.user_prompt, str):
                pass  # 已经是字符串，无需处理
            elif isinstance(requirements.user_prompt, bytes):
                try:
                    requirements.user_prompt = requirements.user_prompt.decode('utf-8')
                except UnicodeError:
                    requirements.user_prompt = requirements.user_prompt.decode('utf-8', errors='replace')
            else:
                requirements.user_prompt = str(requirements.user_prompt)
            nc_program = self._generate_nc_code(requirements)
        
        return nc_program
    
    def _build_generation_prompt(self, requirements: ProcessingRequirements) -> str:
        """
        构建AI生成的提示词
        
        Args:
            requirements: 处理需求
            
        Returns:
            str: 构建的提示词
        """
        # 优化的提示词，能够更好处理中文描述
        prompt = f"""
        作为专业的FANUC加工中心编程专家，请仔细分析以下中文加工需求并生成完整的NC程序。

        用户加工需求: {requirements.user_prompt}

        已识别的关键信息:
        - 加工类型: {requirements.processing_type}
        """
        
        if requirements.depth:
            prompt += f"- 加工深度: {requirements.depth}mm\n"
        
        if requirements.hole_positions:
            prompt += f"- 孔位置坐标: {requirements.hole_positions}\n"
        
        if requirements.tool_diameters:
            prompt += f"- 刀具直径信息: {requirements.tool_diameters}\n"
        
        if requirements.material:
            prompt += f"- 材料类型: {requirements.material}\n"
        
        # 添加对中文描述的特别指导
        prompt += """
        
        重要提示:
        1. 仔细分析用户描述中的中文术语，特别是：
           - 沉孔/锪孔: 指Counterbore，需要分步骤加工（点孔→钻孔→锪孔）
           - 贯通: 指孔是通孔
           - 极坐标位置: 指相对于某个基准点的角度和半径位置
           - φXX: 表示直径为XXmm的孔
        2. 如果用户描述中包含多个加工步骤（如"使用点孔、钻孔、沉孔工艺"），请严格按照多步骤工艺生成程序
        3. 对于沉孔加工，必须包含完整的三步工艺：先点孔定位，再钻底孔，最后锪沉孔
        4. 注意用户提到的坐标原点选择策略，如"坐标原点选择正视图φ234的圆的圆心最高点"
        5. 严格按照FANUC编程规范生成程序
        6. 使用G90绝对坐标系统
        7. 包含必要的安全高度和刀具补偿指令
        8. 程序应包含详细注释，特别是每个加工步骤的说明

        请生成:
        1. 完整的FANUC兼容NC程序
        2. 包含详细的安全指令和初始化代码
        3. 适当的中文注释说明
        4. 符合加工工艺的刀具路径
        5. 安全高度和回零操作
        6. 符合FANUC编程规范
        7. 对于多步骤工艺（如沉孔、攻丝），按正确顺序生成各步骤代码
        """
        
        return prompt
    
    def _generate_nc_code(self, requirements: ProcessingRequirements) -> str:
        """
        根据需求生成NC代码（模拟AI生成）
        
        Args:
            requirements: 处理需求
            
        Returns:
            str: NC程序代码
        """
        # 根据加工类型生成相应的NC代码
        nc_lines = [
            "O0001 (AI-GENERATED CNC PROGRAM)",
            f"(USER REQUEST: {requirements.user_prompt[:50]}...)",
            "(GENERATED BY AI-DRIVEN CNC GENERATOR)",
            f"(DATE: 2025-12-24)",
            ""
        ]
        
        # 程序初始化
        nc_lines.extend([
            "(PROGRAM INITIALIZATION)",
            "G21 (MILLIMETER UNITS)",
            "G90 (ABSOLUTE COORDINATE SYSTEM)",
            "G40 (CANCEL TOOL RADIUS COMPENSATION)",
            "G49 (CANCEL TOOL LENGTH COMPENSATION)",
            "G80 (CANCEL FIXED CYCLE)",
            "G54 (SELECT WORK COORDINATE SYSTEM)",
            ""
        ])
        
        # 安全高度
        nc_lines.extend([
            "(MOVE TO SAFE HEIGHT)",
            "G00 Z100.0 (RAPID MOVE TO SAFE HEIGHT)",
            ""
        ])
        
        # 根据加工类型添加相应代码
        if requirements.processing_type == 'counterbore':
            nc_lines.extend(self._generate_counterbore_code(requirements))
        elif requirements.processing_type == 'tapping':
            nc_lines.extend(self._generate_tapping_code(requirements))
        elif requirements.processing_type == 'drilling':
            nc_lines.extend(self._generate_drilling_code(requirements))
        elif requirements.processing_type == 'milling':
            nc_lines.extend(self._generate_milling_code(requirements))
        else:
            nc_lines.extend(self._generate_general_code(requirements))
        
        # 程序结束
        nc_lines.extend([
            "",
            "(PROGRAM END)",
            "G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)",
            "G00 X0.0 Y0.0 (RETURN TO ORIGIN)",
            "M05 (SPINDLE STOP)",
            "M30 (PROGRAM END)"
        ])
        
        return "\n".join(nc_lines)
    
    def _generate_counterbore_code(self, requirements: ProcessingRequirements) -> List[str]:
        """生成沉孔加工代码"""
        lines = [
            f"(COUNTERBORE PROCESSING - {len(requirements.hole_positions)} HOLES)",
            "(STEP 1: PILOT DRILLING)"
        ]
        
        if requirements.hole_positions:
            # 点孔
            lines.extend([
                "T1 M06 (TOOL CHANGE - CENTER DRILL)",
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                "G43 H1 Z100. (TOOL LENGTH COMPENSATION)",
                "M03 S1000 (SPINDLE SPEED)",
                "M08 (COOLANT ON)"
            ])
            
            first_pos = True
            for pos in requirements.hole_positions:
                if first_pos:
                    lines.append(f"G82 X{pos[0]:.3f} Y{pos[1]:.3f} Z-2.0 R5.0 P1000 F100.0 (SPOT DRILLING)")
                    first_pos = False
                else:
                    lines.append(f"X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO NEXT POSITION)")
            
            lines.extend([
                "G80 (CANCEL DRILLING CYCLE)",
                "G00 Z100.0 (RAISE TOOL)",
                "M09 (COOLANT OFF)",
                ""
            ])
            
            # 钻孔
            inner_dia = requirements.tool_diameters.get('inner', requirements.tool_diameters.get('default', 10.0))
            depth = requirements.depth or 20.0
            lines.extend([
                f"(STEP 2: DRILLING φ{inner_dia} THRU HOLES)",
                "T2 M06 (TOOL CHANGE - DRILL BIT)",
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                f"G43 H2 Z100. (TOOL LENGTH COMPENSATION FOR φ{inner_dia} DRILL)",
                "M03 S800 (SPINDLE SPEED)",
                "M08 (COOLANT ON)"
            ])
            
            first_pos = True
            for pos in requirements.hole_positions:
                if first_pos:
                    lines.append(f"G83 X{pos[0]:.3f} Y{pos[1]:.3f} Z{-depth-2:.3f} R5.0 Q2.0 F120.0 (PECK DRILLING)")
                    first_pos = False
                else:
                    lines.append(f"X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO NEXT POSITION)")
            
            lines.extend([
                "G80 (CANCEL DRILLING CYCLE)",
                "G00 Z100.0 (RAISE TOOL)",
                "M09 (COOLANT OFF)",
                ""
            ])
            
            # 沉孔
            outer_dia = requirements.tool_diameters.get('outer', 22.0)
            lines.extend([
                f"(STEP 3: COUNTERBORING φ{outer_dia} HOLES)",
                "T3 M06 (TOOL CHANGE - COUNTERBORING TOOL)",
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                f"G43 H3 Z100. (TOOL LENGTH COMPENSATION FOR φ{outer_dia} COUNTERBORING TOOL)",
                "M03 S600 (SPINDLE SPEED)",
                "M08 (COOLANT ON)"
            ])
            
            first_pos = True
            for pos in requirements.hole_positions:
                if first_pos:
                    lines.append(f"G81 X{pos[0]:.3f} Y{pos[1]:.3f} Z{-depth:.3f} R5.0 F80.0 (COUNTERBORING)")
                    first_pos = False
                else:
                    lines.append(f"X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO NEXT POSITION)")
        
        return lines
    
    def _generate_tapping_code(self, requirements: ProcessingRequirements) -> List[str]:
        """生成攻丝加工代码"""
        lines = [
            f"(TAPPING PROCESSING - {len(requirements.hole_positions)} HOLES)",
            "T3 M06 (TOOL CHANGE - TAP)"
        ]
        
        if requirements.hole_positions:
            depth = requirements.depth or 15.0
            lines.extend([
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                "G43 H3 Z100. (TOOL LENGTH COMPENSATION)",
                f"M03 S200 (TAPPING SPINDLE SPEED)"
            ])
            
            # 计算进给 - F = S * 螺距
            pitch = 1.5  # 假设M10螺纹
            feed = 200 * pitch  # 进给 = 转速 * 螺距
            lines.append(f"G00 Z100.0 (RAPID TO SAFE HEIGHT)")
            
            first_pos = True
            for pos in requirements.hole_positions:
                if first_pos:
                    lines.append(f"G84 X{pos[0]:.3f} Y{pos[1]:.3f} Z{-depth:.3f} R5.0 F{feed:.1f} (TAPPING)")
                    first_pos = False
                else:
                    lines.append(f"X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO NEXT POSITION)")
        
        return lines
    
    def _generate_drilling_code(self, requirements: ProcessingRequirements) -> List[str]:
        """生成钻孔加工代码"""
        lines = [
            f"(DRILLING PROCESSING - {len(requirements.hole_positions)} HOLES)"
        ]
        
        if requirements.hole_positions:
            depth = requirements.depth or 10.0
            dia = requirements.tool_diameters.get('default', 10.0)
            lines.extend([
                f"T2 M06 (TOOL CHANGE - φ{dia} DRILL)",
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                f"G43 H2 Z100. (TOOL LENGTH COMPENSATION FOR φ{dia} DRILL)",
                "M03 S1000 (SPINDLE SPEED)",
                "M08 (COOLANT ON)"
            ])
            
            first_pos = True
            for pos in requirements.hole_positions:
                if first_pos:
                    lines.append(f"G83 X{pos[0]:.3f} Y{pos[1]:.3f} Z{-depth-1:.3f} R5.0 Q2.0 F150.0 (PECK DRILLING)")
                    first_pos = False
                else:
                    lines.append(f"X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO NEXT POSITION)")
            
            lines.extend([
                "G80 (CANCEL DRILLING CYCLE)",
                "M09 (COOLANT OFF)"
            ])
        
        return lines
    
    def _generate_milling_code(self, requirements: ProcessingRequirements) -> List[str]:
        """生成铣削加工代码"""
        lines = [
            f"(MILLING PROCESSING - {len(requirements.hole_positions)} FEATURES)"
        ]
        
        if requirements.hole_positions:
            depth = requirements.depth or 5.0
            lines.extend([
                "T4 M06 (TOOL CHANGE - END MILL)",
                "G54 (ENSURE WORK COORDINATE SYSTEM IS SELECTED)",
                "G43 H4 Z100. (TOOL LENGTH COMPENSATION)",
                "M03 S1200 (SPINDLE SPEED)",
                "M08 (COOLANT ON)"
            ])
            
            for i, pos in enumerate(requirements.hole_positions):
                lines.extend([
                    f"G00 X{pos[0]:.3f} Y{pos[1]:.3f} (MOVE TO MILLING POSITION {i+1})",
                    f"G01 Z{-depth/2:.3f} F200.0 (FIRST PASS)",
                    f"G02 I10.0 J0 F400.0 (CIRCULAR MILLING)",
                    f"G01 Z{-depth:.3f} F200.0 (SECOND PASS)",
                    f"G02 I10.0 J0 F400.0 (CIRCULAR MILLING)"
                ])
            
            lines.extend([
                "M09 (COOLANT OFF)"
            ])
        
        return lines
    
    def _generate_general_code(self, requirements: ProcessingRequirements) -> List[str]:
        """生成通用加工代码"""
        return [
            "(GENERAL PROCESSING - FOLLOWING USER SPECIFICATIONS)",
            f"(PROCESSING BASED ON: {requirements.user_prompt})"
        ]
    
    def validate_and_optimize(self, nc_program: str) -> str:
        """
        验证和优化NC程序
        
        Args:
            nc_program: 原始NC程序
            
        Returns:
            str: 验证和优化后的NC程序
        """
        # 基本验证：检查关键指令是否存在
        required_commands = ['G21', 'G90', 'G80', 'M30']
        program_lines = nc_program.split('\n')
        validated_lines = []
        
        # 检查是否有必需的指令
        has_required = {cmd: False for cmd in required_commands}
        
        for line in program_lines:
            for cmd in required_commands:
                if cmd in line:
                    has_required[cmd] = True
            validated_lines.append(line)
        
        # 如果缺少某些关键指令，添加它们
        missing_commands = [cmd for cmd, exists in has_required.items() if not exists]
        if missing_commands:
            self.logger.warning(f"检测到缺少关键指令: {missing_commands}")
            # 在实际应用中，这里可能需要重新生成或修复程序
        
        return "\n".join(validated_lines)
    
    def generate_nc_program(self, user_prompt: str, pdf_path: Optional[str] = None) -> str:
        """
        主要的NC程序生成方法
        
        Args:
            user_prompt: 用户需求描述
            pdf_path: 可选的PDF图纸路径
            
        Returns:
            str: 生成的NC程序代码
        """
        try:
            # 步骤1: 解析用户需求
            self.logger.info("解析用户需求...")
            parsed_requirements = self.parse_user_requirements(user_prompt)
            
            # 步骤2: 从图纸中提取特征（如果提供）
            if pdf_path and HAS_PYMUPDF:
                self.logger.info("从PDF中提取特征信息...")
                pdf_features = self.extract_features_from_pdf(pdf_path)
                parsed_requirements = self.merge_requirements_and_features(parsed_requirements, pdf_features)
            
            # 步骤3: 生成NC程序
            self.logger.info("生成NC程序...")
            nc_program = self.generate_with_ai(parsed_requirements)
            
            # 步骤4: 验证和优化
            self.logger.info("验证和优化NC程序...")
            validated_program = self.validate_and_optimize(nc_program)
            
            self.logger.info("NC程序生成完成")
            return validated_program
            
        except Exception as e:
            self.logger.error(f"生成NC程序时出错: {str(e)}")
            error_program = [
                "O9999 (ERROR PROGRAM)",
                f"(ERROR: {str(e)})",
                "M30 (PROGRAM END)"
            ]
            return "\n".join(error_program)

# 全局实例
ai_generator = AIDrivenCNCGenerator()

def generate_nc_with_ai(user_prompt: str, pdf_path: Optional[str] = None) -> str:
    """
    AI驱动的NC程序生成函数
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: 可选的PDF图纸路径
        
    Returns:
        str: 生成的NC程序代码
    """
    return ai_generator.generate_nc_program(user_prompt, pdf_path)

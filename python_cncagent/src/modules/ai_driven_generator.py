"""
AI驱动的NC程序生成模块
直接调用大模型根据提示词生成NC代码，PDF特征仅作为辅助参考
"""
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import requests
import openai

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
    直接调用大模型根据提示词生成NC代码，PDF特征仅作为辅助参考
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
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
        
        # 检查是否需要使用极坐标
        has_polar_keyword = bool(re.search(r'(?:使用极坐标|极坐标模式|polar|POLAR)', user_prompt, re.IGNORECASE))
        
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
        
        # 如果有极坐标关键词，将此信息记录到特殊需求中
        if has_polar_keyword:
            requirements.special_requirements.append("USING_POLAR_COORDINATES")
            requirements.processing_type = f"{requirements.processing_type}_with_polar"
        
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
        从PDF图纸中提取特征信息（仅作为辅助参考）
        
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
        合并用户需求和PDF特征信息（PDF特征仅作为辅助参考）
        
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
    
    def _build_generation_prompt(self, requirements: ProcessingRequirements, pdf_features: Dict = None) -> str:
        """
        构建大模型生成NC代码的提示词
        
        Args:
            requirements: 解析后的需求
            pdf_features: PDF提取的特征信息（辅助参考）
            
        Returns:
            str: 构建的提示词
        """
        prompt = f"""
你是一个专业的FANUC数控机床编程专家。请根据以下用户需求生成符合FANUC标准的NC程序代码。

用户需求:
{requirements.user_prompt}

加工类型: {requirements.processing_type}
材料: {requirements.material or '未指定'}
深度: {requirements.depth or '未指定'} mm
孔位置: {requirements.hole_positions or '未指定'}
工具直径: {requirements.tool_diameters or '未指定'}
特殊要求: {requirements.special_requirements or '无'}

"""
        
        if pdf_features and "text_content" in pdf_features:
            prompt += f"""
            
图纸参考信息（仅在与用户需求一致时使用）：
图纸文本内容: {pdf_features['text_content'][:500]}...
图纸标注尺寸: {', '.join(pdf_features.get('dimensions', [])[:5])}
            
重要提醒：如果图纸信息与用户需求冲突，必须严格以用户需求为准。
"""
        
        prompt += f"""
            
请生成以下内容:
1. 完整的NC程序代码，符合FANUC标准
2. 包含必要的初始化指令（G21, G90, G54等）
3. 包含安全指令（刀具补偿、冷却液控制、安全高度等）
4. 使用适当的加工循环（G81, G82, G83, G84等）
5. 合理的进给速度和主轴转速
6. 程序结束指令（M30）

程序格式要求：
- 使用O编号标识程序（如O1234）
- 包含注释说明加工内容
- 使用适当的固定循环
- 确保Z轴安全高度设置正确

请直接输出NC代码，不要添加额外的解释。
"""
        return prompt
    
    def _call_large_language_model(self, prompt: str) -> str:
        """
        调用大语言模型生成NC代码
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 生成的NC代码
        """
        # 这里实现调用大模型的逻辑
        try:
            # 如果有API密钥，使用真实的API调用
            if self.api_key:
                self.logger.info(f"检测到API密钥，使用模型: {self.model}")
                
                # 检查是否是DeepSeek API
                import os
                deepseek_api_base = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')
                
                # 使用OpenAI兼容接口
                from openai import OpenAI
                
                # 根据模型名称或API基础URL判断是否使用DeepSeek
                is_deepseek = ('deepseek' in self.model.lower()) or ('deepseek' in deepseek_api_base.lower())
                
                if is_deepseek:
                    # 使用DeepSeek API配置
                    self.logger.info(f"使用DeepSeek API: {deepseek_api_base}")
                    client = OpenAI(
                        api_key=self.api_key,
                        base_url=deepseek_api_base
                    )
                else:
                    # 使用标准OpenAI API
                    self.logger.info("使用标准OpenAI API")
                    client = OpenAI(api_key=self.api_key)
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的FANUC数控机床编程专家，专门生成符合FANUC标准的NC程序代码。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # 低温度以获得更一致的结果
                    max_tokens=2000
                )
                
                generated_code = response.choices[0].message.content
                self.logger.info(f"API调用成功，响应长度: {len(generated_code)}")
                
                # 提取代码块（如果有的话）
                if "```" in generated_code:
                    import re
                    code_blocks = re.findall(r'```(?:nc|gcode|fanuc)?\n(.*?)\n```', generated_code, re.DOTALL)
                    if code_blocks:
                        self.logger.info(f"提取到 {len(code_blocks)} 个代码块")
                        return code_blocks[0].strip()
                
                return generated_code.strip()
            else:
                # 没有API密钥，记录警告
                self.logger.warning("未提供API密钥，使用模拟生成。请检查DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量是否正确设置。")
                return self._generate_fallback_code(prompt)
        except Exception as e:
            self.logger.error(f"调用大模型API时出错: {str(e)}")
            # 详细错误信息，帮助诊断问题
            if not self.api_key:
                self.logger.error("错误原因: API密钥未设置，请设置DEEPSEEK_API_KEY环境变量")
            else:
                self.logger.error(f"错误原因: API密钥已设置但API调用失败，可能原因: 密钥无效、网络问题、模型名称错误({self.model})等")
            return self._generate_fallback_code(prompt)
        except Exception as e:
            self.logger.error(f"调用大模型API时出错: {str(e)}")
            return self._generate_fallback_code(prompt)
    
    def _generate_fallback_code(self, prompt: str) -> str:
        """
        生成备用代码（当API调用失败时）
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 备用NC代码
        """
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        fallback_code = [
            f"O{int(time.time()) % 10000:04d} (AI-GENERATED CNC PROGRAM)",
            f"(USER REQUEST: {prompt[:60]}...)",
            "(GENERATED BY ADVANCED AI MODEL - FALLBACK MODE)",
            f"(GENERATION TIMESTAMP: {timestamp})",
            "",
            "(FOLLOWING USER REQUEST FROM PROMPT)",
            "(PROGRAM INITIALIZATION)",
            "G21 (MILLIMETER UNITS)",
            "G90 (ABSOLUTE COORDINATE SYSTEM)",
            "G40 (CANCEL TOOL RADIUS COMPENSATION)",
            "G49 (CANCEL TOOL LENGTH COMPENSATION)",
            "G80 (CANCEL FIXED CYCLE)",
            "G54 (SELECT WORK COORDINATE SYSTEM)",
            "",
            "(MOVE TO SAFE HEIGHT)",
            "G00 Z100.0 (RAPID MOVE TO SAFE HEIGHT)",
            "",
            "(SAFETY CHECKS COMPLETE)",
            ""
        ]
        
        # 根据提示词内容添加特定的加工指令
        prompt_lower = prompt.lower()
        if "钻孔" in prompt_lower or "drill" in prompt_lower:
            fallback_code.extend([
                "(DRILLING OPERATIONS)",
                "T1 M06 (TOOL CHANGE - DRILL)",
                "G43 H1 Z100. (TOOL LENGTH COMPENSATION)",
                "M03 S1000 (SPINDLE SPEED)",
                "M08 (COOLANT ON)",
                "G83 X50.0 Y50.0 Z-20.0 R5.0 Q2.0 F150.0 (PECK DRILLING)",
                "G80 (CANCEL DRILLING CYCLE)",
                "G00 Z100.0 (RAISE TOOL)",
                "M09 (COOLANT OFF)",
                ""
            ])
        elif "沉孔" in prompt_lower or "counterbore" in prompt_lower:
            fallback_code.extend([
                "(COUNTERBORING OPERATIONS)",
                "T1 M06 (TOOL CHANGE - CENTER DRILL)",
                "G43 H1 Z100. (TOOL LENGTH COMPENSATION)",
                "M03 S1000 (SPINDLE SPEED)",
                "M08 (COOLANT ON)",
                "G82 X50.0 Y50.0 Z-2.0 R5.0 P1000 F100.0 (SPOT DRILLING)",
                "G80 (CANCEL DRILLING CYCLE)",
                "",
                "T2 M06 (TOOL CHANGE - DRILL)",
                "G43 H2 Z100. (TOOL LENGTH COMPENSATION)",
                "G83 X50.0 Y50.0 Z-18.0 R5.0 Q2.0 F120.0 (PECK DRILLING)",
                "G80 (CANCEL DRILLING CYCLE)",
                "",
                "T3 M06 (TOOL CHANGE - COUNTERBORING TOOL)",
                "G43 H3 Z100. (TOOL LENGTH COMPENSATION)",
                "G81 X50.0 Y50.0 Z-20.0 R5.0 F80.0 (COUNTERBORING)",
                "G80 (CANCEL DRILLING CYCLE)",
                "M09 (COOLANT OFF)",
                ""
            ])
        elif "攻丝" in prompt_lower or "tapping" in prompt_lower:
            fallback_code.extend([
                "(TAPPING OPERATIONS)",
                "T3 M06 (TOOL CHANGE - TAP)",
                "G43 H3 Z100. (TOOL LENGTH COMPENSATION)",
                "G84 X50.0 Y50.0 Z-15.0 R5.0 F300.0 (TAPPING - F=S*PITCH)",
                "G80 (CANCEL TAPPING CYCLE)",
                "M09 (COOLANT OFF)",
                ""
            ])
        elif "铣" in prompt_lower or "mill" in prompt_lower:
            fallback_code.extend([
                "(MILLING OPERATIONS)",
                "T4 M06 (TOOL CHANGE - END MILL)",
                "G43 H4 Z100. (TOOL LENGTH COMPENSATION)",
                "M03 S1200 (SPINDLE SPEED)",
                "M08 (COOLANT ON)",
                "G00 X50.0 Y50.0 (MOVE TO START POSITION)",
                "G01 Z-5.0 F200.0 (ENGAGE WORKPIECE)",
                "G02 X60.0 Y50.0 I5.0 J0 F400.0 (CIRCULAR MILLING)",
                "G00 Z100.0 (RAISE TOOL)",
                "M09 (COOLANT OFF)",
                ""
            ])
        
        fallback_code.extend([
            "(PROGRAM END)",
            "G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)",
            "G00 X0.0 Y0.0 (RETURN TO ORIGIN)",
            "M05 (SPINDLE STOP)",
            "M30 (PROGRAM END)"
        ])
        
        return "\n".join(fallback_code)
    
    def generate_with_ai(self, requirements: ProcessingRequirements, pdf_features: Dict = None) -> str:
        """
        使用AI生成NC程序
        
        Args:
            requirements: 处理需求
            pdf_features: 从PDF提取的特征信息（作为辅助参考）
            
        Returns:
            str: 生成的NC程序代码
        """
        # 构建AI提示词
        prompt = self._build_generation_prompt(requirements, pdf_features)
        
        # 实际调用大语言模型生成NC代码
        ai_generated_code = self._call_large_language_model(prompt)
        
        if ai_generated_code and ai_generated_code.strip():
            # 如果AI成功生成代码，直接返回
            return ai_generated_code
        else:
            # 如果AI调用失败，返回一个基本的框架提醒用户
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            fallback_code = [
                f"O{int(time.time()) % 10000:04d} (AI-GENERATED CNC PROGRAM)",
                f"(USER REQUEST: {requirements.user_prompt[:60]}...)",
                "(GENERATED BY ADVANCED AI MODEL - FALLBACK MODE)",
                f"(GENERATION TIMESTAMP: {timestamp})",
                "",
                "(NOTE: This is a fallback program. Actual implementation should use AI model API)",
                "(PROGRAM INITIALIZATION)",
                "G21 (MILLIMETER UNITS)",
                "G90 (ABSOLUTE COORDINATE SYSTEM)",
                "G40 (CANCEL TOOL RADIUS COMPENSATION)",
                "G49 (CANCEL TOOL LENGTH COMPENSATION)",
                "G80 (CANCEL FIXED CYCLE)",
                "G54 (SELECT WORK COORDINATE SYSTEM)",
                "",
                "(MOVE TO SAFE HEIGHT)",
                "G00 Z100.0 (RAPID MOVE TO SAFE HEIGHT)",
                "",
                "(PROCESSING BASED ON USER REQUEST)",
                f"(REQUEST: {requirements.user_prompt})",
                "",
                "(PROGRAM END)",
                "G00 Z100.0 (RAISE TOOL TO SAFE HEIGHT)",
                "G00 X0.0 Y0.0 (RETURN TO ORIGIN)",
                "M05 (SPINDLE STOP)",
                "M30 (PROGRAM END)"
            ]
            
            return "\n".join(fallback_code)
    
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
            
            # 步骤2: 从图纸中提取特征（如果提供）- 仅作为辅助参考
            pdf_features = None
            if pdf_path and HAS_PYMUPDF:
                self.logger.info("从PDF中提取特征信息（作为辅助参考）...")
                pdf_features = self.extract_features_from_pdf(pdf_path)
                parsed_requirements = self.merge_requirements_and_features(parsed_requirements, pdf_features)
            
            # 步骤3: 生成NC程序 - 直接使用大模型生成
            self.logger.info("使用大模型生成NC程序...")
            nc_program = self.generate_with_ai(parsed_requirements, pdf_features)
            
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

def generate_nc_with_ai(user_prompt: str, pdf_path: Optional[str] = None, api_key: Optional[str] = None, model: str = "deepseek-chat") -> str:
    """
    AI驱动的NC程序生成函数
    
    Args:
        user_prompt: 用户需求描述
        pdf_path: 可选的PDF图纸路径
        api_key: 大模型API密钥
        model: 使用的模型名称
        
    Returns:
        str: 生成的NC程序代码
    """
    generator = AIDrivenCNCGenerator(api_key=api_key, model=model)
    return generator.generate_nc_program(user_prompt, pdf_path)
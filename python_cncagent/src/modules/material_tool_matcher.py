"""
用户描述理解模块
使用NLP技术分析用户对加工需求的描述，提取关键信息如加工类型、材料、精度要求等
"""
import spacy
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProcessingInstruction:
    """加工指令数据类"""
    processing_type: str  # 加工类型：drilling, milling, turning等
    tool_required: str    # 需要的刀具
    depth: Optional[float] = None  # 加工深度
    feed_rate: Optional[float] = None  # 进给速度
    spindle_speed: Optional[float] = None  # 主轴转速
    material: Optional[str] = None  # 材料类型
    precision: Optional[str] = None  # 精度要求


class UserDescriptionAnalyzer:
    """用户描述分析器"""
    
    def __init__(self):
        """初始化分析器，加载NLP模型"""
        try:
            # 尝试加载中文模型，如果失败则加载英文模型
            try:
                self.nlp = spacy.load("zh_core_web_sm")
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    # 如果都没有安装，则使用简化版本
                    self.nlp = None
        except:
            self.nlp = None
    
    def analyze(self, description: str) -> ProcessingInstruction:
        """
        分析用户描述，提取加工指令
        
        Args:
            description (str): 用户描述文本
        
        Returns:
            ProcessingInstruction: 解析出的加工指令
        """
        if self.nlp:
            return self._analyze_with_nlp(description)
        else:
            return self._analyze_without_nlp(description)
    
    def _analyze_with_nlp(self, description: str) -> ProcessingInstruction:
        """使用NLP模型分析描述"""
        doc = self.nlp(description)
        
        # 提取实体和关键词
        entities = {}
        for ent in doc.ents:
            entities[ent.label_] = ent.text
        
        # 分析加工类型
        processing_type = self._identify_processing_type(description)
        
        # 提取数值信息（深度、转速等）
        depth = self._extract_depth(description)
        feed_rate = self._extract_feed_rate(description)
        spindle_speed = self._extract_spindle_speed(description)
        
        # 提取材料信息
        material = self._extract_material(description)
        
        # 提取精度要求
        precision = self._extract_precision(description)
        
        # 确定所需刀具
        tool_required = self._identify_tool_required(processing_type)
        
        return ProcessingInstruction(
            processing_type=processing_type,
            tool_required=tool_required,
            depth=depth,
            feed_rate=feed_rate,
            spindle_speed=spindle_speed,
            material=material,
            precision=precision
        )
    
    def _analyze_without_nlp(self, description: str) -> ProcessingInstruction:
        """不使用NLP模型的简化分析"""
        processing_type = self._identify_processing_type(description)
        depth = self._extract_depth(description)
        feed_rate = self._extract_feed_rate(description)
        spindle_speed = self._extract_spindle_speed(description)
        material = self._extract_material(description)
        precision = self._extract_precision(description)
        tool_required = self._identify_tool_required(processing_type)
        
        return ProcessingInstruction(
            processing_type=processing_type,
            tool_required=tool_required,
            depth=depth,
            feed_rate=feed_rate,
            spindle_speed=spindle_speed,
            material=material,
            precision=precision
        )
    
    def _identify_processing_type(self, description: str) -> str:
        """识别加工类型"""
        description_lower = description.lower()
        
        # 关键词映射
        drilling_keywords = ['drill', 'hole', '钻孔', '打孔', '孔']
        milling_keywords = ['mill', 'milling', 'cut', 'cutting', '铣', '铣削', '切削']
        turning_keywords = ['turn', 'turning', 'lathe', '车', '车削']
        grinding_keywords = ['grind', 'grinding', '磨', '磨削']
        
        if any(keyword in description_lower for keyword in drilling_keywords):
            return 'drilling'
        elif any(keyword in description_lower for keyword in milling_keywords):
            return 'milling'
        elif any(keyword in description_lower for keyword in turning_keywords):
            return 'turning'
        elif any(keyword in description_lower for keyword in grinding_keywords):
            return 'grinding'
        else:
            return 'general'
    
    def _identify_tool_required(self, processing_type: str) -> str:
        """根据加工类型确定需要的刀具"""
        tool_mapping = {
            'drilling': 'drill_bit',
            'milling': 'end_mill',
            'turning': 'cutting_tool',
            'grinding': 'grinding_wheel'
        }
        
        return tool_mapping.get(processing_type, 'general_tool')
    
    def _extract_depth(self, description: str) -> Optional[float]:
        """提取加工深度"""
        # 匹配 "深度5mm" 或 "5mm深" 等模式
        patterns = [
            r'深度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
            r'(\d+\.?\d*)\s*([mM]?[mM])\s*深',
            r'depth[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()
                
                # 如果单位是mm，则直接返回；如果是cm或m，则转换为mm
                if 'cm' in unit:
                    return value * 10
                elif 'm' in unit and 'mm' not in unit:
                    return value * 1000
                else:
                    return value  # 默认为mm
        
        return None
    
    def _extract_feed_rate(self, description: str) -> Optional[float]:
        """提取进给速度"""
        patterns = [
            r'进给[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
            r'feed[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)',
            r'速度[：:]?\s*(\d+\.?\d*)\s*(mm/min|mm/s|mm/rev)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return float(match.group(1))
        
        return None
    
    def _extract_spindle_speed(self, description: str) -> Optional[float]:
        """提取主轴转速"""
        patterns = [
            r'转速[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|转/分钟)',
            r'speed[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM|rev/min)',
            r'主轴[：:]?\s*(\d+\.?\d*)\s*(rpm|RPM)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return float(match.group(1))
        
        return None
    
    def _extract_material(self, description: str) -> Optional[str]:
        """提取材料信息"""
        materials = ['steel', 'aluminum', 'aluminium', 'titanium', 'copper', 'brass', 
                     'plastic', 'wood', 'steel', '不锈钢', '铝合金', '钛合金', '铜', 
                     '塑料', '木材', 'steel', '铁', 'metal', '金属']
        
        for material in materials:
            if material in description.lower():
                return material
        
        return None
    
    def _extract_precision(self, description: str) -> Optional[str]:
        """提取精度要求"""
        # 匹配 "精度0.01mm" 或 "Ra1.6" 等
        patterns = [
            r'精度[：:]?\s*(\d+\.?\d*)\s*([mM]?[mM])',
            r'Ra\s*(\d+\.?\d*)',
            r'粗糙度[：:]?\s*Ra\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return f"Ra{match.group(1)}"
        
        return None


def analyze_user_description(description: str) -> Dict:
    """
    分析用户描述，提取关键信息
    
    Args:
        description (str): 用户对加工需求的描述
    
    Returns:
        dict: 包含提取信息的字典
    """
    analyzer = UserDescriptionAnalyzer()
    instruction = analyzer.analyze(description)
    
    return {
        "processing_type": instruction.processing_type,
        "tool_required": instruction.tool_required,
        "depth": instruction.depth,
        "feed_rate": instruction.feed_rate,
        "spindle_speed": instruction.spindle_speed,
        "material": instruction.material,
        "precision": instruction.precision,
        "description": description
    }
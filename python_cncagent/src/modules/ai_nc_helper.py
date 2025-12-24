"""
AI辅助NC编程工具核心模块
基于插件式架构的智能CAM补充工具
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from .feature_definition import identify_features
from .gcode_generation import generate_fanuc_nc
from .validation import validate_nc_program


class QuickFeatureDetector:
    """
    快速特征检测器
    使用预训练模型快速识别常见特征
    """
    def __init__(self):
        self.min_area = 100
        self.min_perimeter = 10
        self.canny_low = 50
        self.canny_high = 150

    def detect_features(self, drawing_input: np.ndarray, drawing_text: str = "") -> Dict:
        """
        从图纸中识别几何特征

        Args:
            drawing_input: 输入的图纸图像
            drawing_text: 图纸中的文本信息

        Returns:
            dict: 包含识别出的特征信息
        """
        # 调用现有的特征识别函数
        features = identify_features(
            drawing_input, 
            min_area=self.min_area,
            min_perimeter=self.min_perimeter,
            canny_low=self.canny_low,
            canny_high=self.canny_high,
            drawing_text=drawing_text
        )
        
        # 分类特征
        circles = [f for f in features if f["shape"] == "circle"]
        holes = [f for f in features if f["shape"] in ["circle", "counterbore"]]
        pockets = [f for f in features if f["shape"] in ["rectangle", "square", "polygon"]]
        other = [f for f in features if f["shape"] not in ["circle", "counterbore", "rectangle", "square", "polygon"]]
        
        return {
            "holes": holes,
            "circles": circles,
            "pockets": pockets,
            "other": other,
            "all_features": features
        }


class SmartProcessLibrary:
    """
    智能工艺库
    基于特征类型智能推荐工艺参数
    """
    def __init__(self):
        self.predefined_processes = {
            "drilling": {
                "feed_rate": 100,
                "spindle_speed": 800,
                "depth": 10,
                "tool": "drill_bit"
            },
            "milling": {
                "feed_rate": 200,
                "spindle_speed": 1000,
                "depth": 5,
                "stepover": 0.8,
                "tool": "end_mill"
            },
            "tapping": {
                "feed_rate": 100,
                "spindle_speed": 300,
                "depth": 14,
                "tool": "tap"
            },
            "counterbore": {
                "feed_rate": 80,
                "spindle_speed": 400,
                "depth": 20,
                "tool": "counterbore_tool"
            },
            "turning": {
                "feed_rate": 100,
                "spindle_speed": 800,
                "depth": 2,
                "tool": "cutting_tool"
            }
        }

    def suggest_process(self, feature_type: str) -> Dict:
        """
        基于特征类型智能推荐工艺参数

        Args:
            feature_type: 特征类型

        Returns:
            dict: 推荐的工艺参数
        """
        # 映射特征类型到工艺类型
        feature_to_process = {
            "circle": "drilling",
            "counterbore": "counterbore",
            "rectangle": "milling",
            "square": "milling",
            "polygon": "milling",
            "triangle": "milling"
        }

        process_type = feature_to_process.get(feature_type, "general")
        return self.predefined_processes.get(process_type, {})


class SmartProcessSelector:
    """
    智能工艺选择器
    根据识别的特征选择合适的加工工艺
    """
    def __init__(self):
        self.process_library = SmartProcessLibrary()

    def select(self, features: List[Dict]) -> List[Dict]:
        """
        根据特征选择加工工艺

        Args:
            features: 识别出的特征列表

        Returns:
            list: 选择的工艺列表
        """
        processes = []
        for feature in features:
            shape = feature.get("shape", "unknown")
            process = self.process_library.suggest_process(shape)
            process["feature"] = feature
            process["shape"] = shape
            processes.append(process)
        return processes


class SimpleNCGenerator:
    """
    简单NC代码生成器
    根据特征和工艺参数生成NC代码
    """
    def __init__(self):
        self.material_properties = {
            "Aluminum": {"feed_multiplier": 1.2, "speed_multiplier": 1.1},
            "Steel": {"feed_multiplier": 0.8, "speed_multiplier": 0.9},
            "Stainless Steel": {"feed_multiplier": 0.7, "speed_multiplier": 0.8},
            "Brass": {"feed_multiplier": 1.3, "speed_multiplier": 1.2},
            "Plastic": {"feed_multiplier": 1.4, "speed_multiplier": 1.3}
        }

    def generate(self, processes: List[Dict], material: str = "Aluminum", description: str = "") -> str:
        """
        根据工艺参数生成NC代码

        Args:
            processes: 工艺参数列表
            material: 材料类型
            description: 用户描述

        Returns:
            str: 生成的NC代码
        """
        # 构建描述分析字典
        description_analysis = {
            "description": description if description else "Automatic NC generation from detected features",
            "processing_type": self._determine_processing_type(processes),
            "tool_required": "general_tool",
            "depth": self._get_common_depth(processes),
            "feed_rate": self._get_common_feed_rate(processes),
            "spindle_speed": self._get_common_spindle_speed(processes)
        }

        # 获取特征列表（从工艺中提取特征）
        features = [proc["feature"] for proc in processes if "feature" in proc]
        
        # 根据材料调整参数
        material_props = self.material_properties.get(material, {"feed_multiplier": 1.0, "speed_multiplier": 1.0})
        if "depth" in description_analysis:
            description_analysis["depth"] *= material_props.get("feed_multiplier", 1.0)
        if "feed_rate" in description_analysis:
            description_analysis["feed_rate"] *= material_props.get("feed_multiplier", 1.0)
        if "spindle_speed" in description_analysis:
            description_analysis["spindle_speed"] *= material_props.get("speed_multiplier", 1.0)

        # 生成NC代码
        try:
            nc_code = generate_fanuc_nc(features, description_analysis)
        except Exception as e:
            # 如果生成失败，构造一个基本的代码
            nc_code = self._generate_basic_code(features, description_analysis)
            
        return nc_code

    def _determine_processing_type(self, processes: List[Dict]) -> str:
        """确定主要加工类型"""
        if not processes:
            return "general"
        
        # 统计各种工艺类型的数量
        types = [proc.get("shape", "general") for proc in processes]
        type_counts = {}
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 选择最常见的类型
        if type_counts:
            main_type = max(type_counts, key=type_counts.get)
            # 映射到标准工艺类型
            type_mapping = {
                "circle": "drilling",
                "counterbore": "counterbore",
                "rectangle": "milling",
                "square": "milling",
                "polygon": "milling",
                "triangle": "milling"
            }
            return type_mapping.get(main_type, "general")
        return "general"

    def _get_common_depth(self, processes: List[Dict]) -> float:
        """获取通用深度"""
        depths = [proc.get("depth", 10) for proc in processes if "depth" in proc]
        return sum(depths) / len(depths) if depths else 10.0

    def _get_common_feed_rate(self, processes: List[Dict]) -> float:
        """获取通用进给率"""
        feeds = [proc.get("feed_rate", 100) for proc in processes if "feed_rate" in proc]
        return sum(feeds) / len(feeds) if feeds else 100.0

    def _get_common_spindle_speed(self, processes: List[Dict]) -> float:
        """获取通用主轴转速"""
        speeds = [proc.get("spindle_speed", 800) for proc in processes if "spindle_speed" in proc]
        return sum(speeds) / len(speeds) if speeds else 800.0

    def _generate_basic_code(self, features: List[Dict], description_analysis: Dict) -> str:
        """生成基本的NC代码作为备选方案"""
        gcode = []
        gcode.append("O0001 (AUTO-GENERATED PROGRAM)")
        gcode.append("(Generated by AI NC Helper)")
        gcode.append("G21 (MM MODE)")
        gcode.append("G90 (ABSOLUTE MODE)")
        gcode.append("G40 (CANCEL TOOL COMP)")  # 添加取消刀具补偿
        gcode.append("G49 (CANCEL LENGTH COMP)")  # 添加取消长度补偿
        gcode.append("G80 (CANCEL CYCLE)")
        gcode.append("G00 Z100 (SAFE HEIGHT)")
        gcode.append("M05 (SPINDLE STOP)")
        gcode.append("M30 (PROGRAM END)")
        return "\n".join(gcode)


class CAM_Plugin_Interface:
    """
    CAM插件接口
    用于与主流CAM软件集成
    """
    def __init__(self):
        pass

    def export_to_cambam(self, nc_code: str) -> str:
        """导出到CamBam格式"""
        # 添加CamBam特定的格式要求
        header = ["; CamBam Generated Code", "; Exported from AI NC Helper", ""]
        nc_lines = nc_code.split('\n')
        return '\n'.join(header + nc_lines)

    def export_to_mastercam(self, nc_code: str) -> str:
        """导出到Mastercam格式"""
        # 添加Mastercam特定的格式要求
        header = [
            "$$ MASTERCAM POST PROCESSOR OUTPUT",
            "$$ Generated by AI NC Helper", 
            "$$"
        ]
        nc_lines = nc_code.split('\n')
        return '\n'.join(header + nc_lines)

    def export_to_fusion360(self, nc_code: str) -> str:
        """导出到Fusion 360格式"""
        # 添加Fusion 360特定的格式要求
        header = [
            "(Fusion 360 Generated Code)",
            "(Exported from AI NC Helper)",
            ""
        ]
        nc_lines = nc_code.split('\n')
        return '\n'.join(header + nc_lines)

    def export_to_generic(self, nc_code: str) -> str:
        """导出到通用格式"""
        return nc_code


class AI_NC_Helper:
    """
    AI辅助NC编程工具主类
    插件式架构设计，支持一键式处理流程
    """
    def __init__(self):
        self.feature_detector = QuickFeatureDetector()
        self.process_selector = SmartProcessSelector()
        self.nc_generator = SimpleNCGenerator()
        self.cam_interface = CAM_Plugin_Interface()
        self.last_features = None
        self.last_processes = None
        self.last_nc_code = None

    def quick_nc_generation(self, drawing_input: np.ndarray, drawing_text: str = "", material: str = "Aluminum", user_description: str = "") -> str:
        """
        一键式NC生成流程

        Args:
            drawing_input: 图纸输入（图像或路径）
            drawing_text: 图纸中的文本信息
            material: 材料类型
            user_description: 用户描述

        Returns:
            str: 生成的NC代码
        """
        # 1. 检测特征
        features_data = self.feature_detector.detect_features(drawing_input, drawing_text)
        self.last_features = features_data["all_features"]
        features = self.last_features

        # 2. 选择工艺
        processes = self.process_selector.select(features)
        self.last_processes = processes

        # 3. 生成NC代码
        nc_code = self.nc_generator.generate(processes, material, user_description)
        self.last_nc_code = nc_code

        return nc_code

    def process_pdf(self, pdf_path: str, drawing_text: str = "", material: str = "Aluminum", user_description: str = "") -> str:
        """
        处理PDF文件

        Args:
            pdf_path: PDF文件路径
            drawing_text: 图纸中的文本信息
            material: 材料类型
            user_description: 用户描述

        Returns:
            str: 生成的NC代码
        """
        from .pdf_parsing_process import pdf_to_images
        
        # 只处理PDF的第一页，避免处理大型PDF文件时的性能问题
        images = pdf_to_images(pdf_path)
        if images:
            # 使用第一页进行处理
            first_page_image = np.array(images[0].convert('L'))  # 转换为灰度图并转换为numpy数组
            return self.quick_nc_generation(first_page_image, drawing_text, material, user_description)
        else:
            raise ValueError("无法从PDF中提取图像")

    def validate_output(self, nc_code: str = None) -> List[str]:
        """
        验证输出的NC代码

        Args:
            nc_code: 要验证的NC代码，如果为None则验证上次生成的代码

        Returns:
            list: 验证错误列表
        """
        code_to_validate = nc_code if nc_code is not None else self.last_nc_code
        if code_to_validate:
            return validate_nc_program(code_to_validate)
        return ["No NC code to validate"]

    def get_analysis_report(self) -> Dict:
        """
        获取分析报告

        Returns:
            dict: 包含分析结果的字典
        """
        report = {
            "features_count": len(self.last_features) if self.last_features else 0,
            "processes_count": len(self.last_processes) if self.last_processes else 0,
            "nc_code_length": len(self.last_nc_code.split('\n')) if self.last_nc_code else 0,
            "features": {
                "circles": len([f for f in (self.last_features or []) if f["shape"] == "circle"]),
                "holes": len([f for f in (self.last_features or []) if f["shape"] in ["circle", "counterbore"]]),
                "pockets": len([f for f in (self.last_features or []) if f["shape"] in ["rectangle", "square", "polygon"]]),
                "counterbores": len([f for f in (self.last_features or []) if f["shape"] == "counterbore"])
            } if self.last_features else {}
        }
        return report
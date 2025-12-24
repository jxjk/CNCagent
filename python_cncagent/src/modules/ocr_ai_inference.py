"""
OCR和AI推理模块
用于从PDF图纸中提取特征信息
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# 尝试导入所需的库
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("警告: 未安装PyMuPDF库，PDF功能将受限")

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("警告: 未安装OpenCV库，图像处理功能将受限")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("警告: 未安装pytesseract库，OCR功能将受限")

class PDFFeatureExtractor:
    """
    PDF特征提取器
    从PDF图纸中提取几何特征、尺寸标注等信息
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_features_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        从PDF中提取特征信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Dict: 提取的特征信息
        """
        if not HAS_PYMUPDF:
            return {"error": "PyMuPDF未安装，无法处理PDF文件"}
        
        try:
            doc = fitz.open(pdf_path)
            all_features = {
                "pages": [],
                "global_text": "",
                "dimensions": [],
                "geometric_features": [],
                "annotations": [],
                "materials": [],
                "tolerances": [],
                "surface_finishes": [],
                "overall_dimensions": [],
                "hole_details": []
            }
            
            for page_num in range(len(doc)):
                page_features = self._extract_page_features(doc[page_num], page_num)
                all_features["pages"].append(page_features)
                all_features["global_text"] += page_features.get("text_content", "") + "\n"
            
            # 从全局文本中提取通用信息
            all_features.update(self._extract_global_features(all_features["global_text"]))
            
            doc.close()
            return all_features
        except Exception as e:
            self.logger.error(f"处理PDF文件时出错: {str(e)}")
            return {"error": f"处理PDF文件时出错: {str(e)}"}
    
    def _extract_page_features(self, page: Any, page_num: int) -> Dict[str, Any]:
        """
        提取单页PDF的特征
        
        Args:
            page: PDF页面对象
            page_num: 页码
            
        Returns:
            Dict: 页面特征
        """
        page_features = {
            "page_number": page_num,
            "text_content": "",
            "image_count": 0,
            "tables": [],
            "figures": [],
            "dimensions": [],
            "geometric_features": []
        }
        
        # 提取文本
        text = page.get_text()
        page_features["text_content"] = text
        
        # 提取文本块（可能包含尺寸标注）
        text_blocks = page.get_text_blocks()
        for block in text_blocks:
            block_text = block[4]  # 文本内容
            # 检查是否包含尺寸信息
            if self._is_dimension_text(block_text):
                page_features["dimensions"].append({
                    "text": block_text,
                    "bbox": block[:4],  # 边界框
                    "type": "dimension"
                })
        
        # 提取图像
        image_list = page.get_images()
        page_features["image_count"] = len(image_list)
        
        # 尝试从图像中提取特征（如果OpenCV可用）
        if HAS_OPENCV:
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                # 将Pixmap转换为OpenCV格式
                if pix.n < 5:  # 灰度或RGB
                    img_array = np.frombuffer(pix.tobytes(), dtype=np.uint8)
                    img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    # 提取图像特征
                    image_features = self._extract_image_features(img_cv, xref)
                    page_features["geometric_features"].extend(image_features)
                
                pix = None  # 释放资源
        
        return page_features
    
    def _is_dimension_text(self, text: str) -> bool:
        """
        判断文本是否为尺寸标注
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否为尺寸标注
        """
        text_lower = text.lower()
        
        # 检查是否包含尺寸相关的字符
        dimension_indicators = [
            'φ', 'r', 'sr', 'sφ',  # 直径、半径等
            'mm', 'cm', 'm',  # 单位
            'x', '*',  # 个数标记
        ]
        
        has_indicator = any(indicator in text_lower for indicator in dimension_indicators)
        
        # 检查是否包含数字
        has_number = any(char.isdigit() for char in text)
        
        # 检查是否符合尺寸标注的模式
        import re
        dimension_pattern = r'φ?\d+\.?\d*\s*[x*]?\s*\d*\.?\d*|R\d+\.?\d*|SR\d+\.?\d*|Sφ\d+\.?\d*'
        matches_pattern = bool(re.search(dimension_pattern, text_lower))
        
        return has_indicator and has_number or matches_pattern
    
    def _extract_image_features(self, image: np.ndarray, image_id: int) -> List[Dict]:
        """
        从图像中提取几何特征
        
        Args:
            image: OpenCV图像
            image_id: 图像ID
            
        Returns:
            List[Dict]: 几何特征列表
        """
        if not HAS_OPENCV:
            return []
        
        features = []
        
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 应用阈值处理
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # 计算轮廓的几何属性
                area = cv2.contourArea(contour)
                
                # 过滤小面积轮廓
                if area < 100:  # 阈值可调整
                    continue
                
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算长宽比
                aspect_ratio = float(w) / h if h != 0 else 0
                
                # 拟合圆形以判断是否为圆形特征
                (circle_x, circle_y), radius = cv2.minEnclosingCircle(contour)
                circle_area = 3.14159 * radius * radius
                circularity = 4 * 3.14159 * area / (cv2.arcLength(contour, True) ** 2) if cv2.arcLength(contour, True) > 0 else 0
                
                # 判断形状类型
                shape_type = self._identify_shape_type(contour, area, circularity, aspect_ratio)
                
                feature = {
                    "id": f"img_{image_id}_contour_{len(features)}",
                    "type": shape_type,
                    "area": area,
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "circularity": circularity,
                    "aspect_ratio": aspect_ratio,
                    "is_circle": circularity > 0.8 and abs(aspect_ratio - 1.0) < 0.2,
                    "diameter_approx": int(2 * radius) if shape_type == "circle" else None
                }
                
                features.append(feature)
        
        except Exception as e:
            self.logger.warning(f"处理图像特征时出错: {str(e)}")
        
        return features
    
    def _identify_shape_type(self, contour: np.ndarray, area: float, circularity: float, aspect_ratio: float) -> str:
        """
        识别轮廓的形状类型
        
        Args:
            contour: 轮廓
            area: 面积
            circularity: 圆形度
            aspect_ratio: 长宽比
            
        Returns:
            str: 形状类型
        """
        # 计算近似多边形
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)
        
        # 基于顶点数、圆形度等判断形状
        if vertices == 3:
            return "triangle"
        elif vertices == 4:
            # 判断是矩形还是正方形
            if abs(aspect_ratio - 1.0) < 0.1:
                return "square"
            else:
                return "rectangle"
        elif vertices > 4 and circularity > 0.8:
            return "circle"
        elif vertices > 4 and 0.7 < circularity <= 0.8:
            return "ellipse"
        else:
            return "irregular"
    
    def _extract_global_features(self, global_text: str) -> Dict[str, List]:
        """
        从全局文本中提取特征
        
        Args:
            global_text: 全局文本内容
            
        Returns:
            Dict: 提取的特征
        """
        import re
        
        extracted = {
            "dimensions": [],
            "materials": [],
            "tolerances": [],
            "surface_finishes": [],
            "overall_dimensions": [],
            "hole_details": []
        }
        
        # 提取尺寸信息
        dim_pattern = r'(?:φ|Φ)?\s*(\d+\.?\d*)\s*(?:[x*]\s*(\d+\.?\d*))?'
        dims = re.findall(dim_pattern, global_text)
        for dim in dims:
            if dim[1]:  # 有乘号，如"10x20"
                extracted["dimensions"].append(f"{dim[0]}x{dim[1]}")
            else:  # 单个尺寸
                extracted["dimensions"].append(dim[0])
        
        # 提取材料信息
        material_pattern = r'(?:材料|材质|Material)\s*[:：]\s*([A-Z0-9\s-]+)'
        materials = re.findall(material_pattern, global_text, re.IGNORECASE)
        extracted["materials"] = materials
        
        # 提取公差信息
        tolerance_pattern = r'([±+−]\s*\d+\.?\d*)\s*mm?'
        tolerances = re.findall(tolerance_pattern, global_text)
        extracted["tolerances"] = tolerances
        
        # 提取表面粗糙度
        roughness_pattern = r'(?:Ra|表面粗糙度)\s*([0-9.]+)'
        roughnesses = re.findall(roughness_pattern, global_text)
        extracted["surface_finishes"] = roughnesses
        
        # 提取总体尺寸
        overall_pattern = r'(?:总体|外形|轮廓)\s*尺寸[:：]\s*(\d+\.?\d*)\s*[x*]\s*(\d+\.?\d*)\s*mm?'
        overalls = re.findall(overall_pattern, global_text, re.IGNORECASE)
        for overall in overalls:
            extracted["overall_dimensions"].append(f"{overall[0]}x{overall[1]}")
        
        # 提取孔详细信息
        hole_pattern = r'(?:孔|hole)\s*(?:[φΦ]\s*(\d+\.?\d*))?\s*(?:深|deep)?\s*(\d+\.?\d*)?\s*mm?'
        holes = re.findall(hole_pattern, global_text, re.IGNORECASE)
        for hole in holes:
            if hole[0] and hole[1]:  # 有直径和深度
                extracted["hole_details"].append(f"φ{hole[0]}x{hole[1]}mm")
            elif hole[0]:  # 只有直径
                extracted["hole_details"].append(f"φ{hole[0]}")
        
        return extracted

class OCRProcessor:
    """
    OCR处理器
    使用OCR技术从图纸中提取文本信息
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_extractor = PDFFeatureExtractor()
    
    def extract_text_with_ocr(self, image_path: str) -> str:
        """
        使用OCR从图像中提取文本
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            str: 提取的文本
        """
        if not HAS_TESSERACT:
            self.logger.warning("Tesseract未安装，无法执行OCR")
            return ""
        
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"无法读取图像: {image_path}")
                return ""
            
            # 预处理图像以提高OCR准确性
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 应用阈值处理
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 使用Tesseract进行OCR
            text = pytesseract.image_to_string(thresh, lang='chi_sim+eng')
            
            return text.strip()
        except Exception as e:
            self.logger.error(f"OCR处理出错: {str(e)}")
            return ""
    
    def extract_features_with_ai_inference(self, pdf_path: str) -> Dict[str, Any]:
        """
        使用AI推理从PDF中提取特征
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Dict: AI推断的特征信息
        """
        # 首先使用传统的PDF和OCR方法提取特征
        basic_features = self.feature_extractor.extract_features_from_pdf(pdf_path)
        
        # 使用AI模型进行推理和补充
        ai_inferred = self._ai_inference_on_features(basic_features)
        
        # 合并基本特征和AI推断的特征
        combined_features = basic_features.copy()
        combined_features.update(ai_inferred)
        
        return combined_features
    
    def _ai_inference_on_features(self, basic_features: Dict) -> Dict[str, Any]:
        """
        基于基本特征进行AI推理
        
        Args:
            basic_features: 基本特征
            
        Returns:
            Dict: AI推断的特征
        """
        # 这里模拟AI推理过程，实际应用中应调用AI模型
        ai_inferred = {
            "inferred_process_types": [],
            "recommended_tool_sizes": [],
            "suggested_sequence": [],
            "potential_issues": [],
            "confidence_scores": {}
        }
        
        # 基于提取的文本和几何特征进行简单推理
        global_text = basic_features.get("global_text", "")
        
        # 推断加工类型
        if "沉孔" in global_text or "counterbore" in global_text.lower():
            ai_inferred["inferred_process_types"].append("counterboring")
        if "攻丝" in global_text or "tapping" in global_text.lower():
            ai_inferred["inferred_process_types"].append("tapping")
        if "钻孔" in global_text or "drill" in global_text.lower():
            ai_inferred["inferred_process_types"].append("drilling")
        
        # 推荐刀具尺寸
        dimensions = basic_features.get("dimensions", [])
        for dim in dimensions:
            try:
                # 尝试提取可能的孔径或特征尺寸
                import re
                numbers = re.findall(r'\d+\.?\d*', str(dim))
                for num in numbers:
                    if 1 <= float(num) <= 5:  # 可能是小孔径
                        ai_inferred["recommended_tool_sizes"].append(f"φ{num}")
                    elif 6 <= float(num) <= 20:  # 中等尺寸
                        ai_inferred["recommended_tool_sizes"].append(f"φ{num}")
            except:
                continue
        
        # 推断加工顺序
        if "粗加工" in global_text or "rough" in global_text.lower():
            ai_inferred["suggested_sequence"].append("rough_machining")
        if "精加工" in global_text or "finish" in global_text.lower():
            ai_inferred["suggested_sequence"].append("finish_machining")
        
        # 标记潜在问题
        if not basic_features.get("materials"):
            ai_inferred["potential_issues"].append("missing_material_specification")
        if not basic_features.get("dimensions"):
            ai_inferred["potential_issues"].append("missing_dimension_annotations")
        
        # 设置置信度
        ai_inferred["confidence_scores"] = {
            "dimensions": 0.8 if basic_features.get("dimensions") else 0.3,
            "material": 0.7 if basic_features.get("materials") else 0.2,
            "tolerances": 0.6 if basic_features.get("tolerances") else 0.3
        }
        
        return ai_inferred

# 创建全局实例
ocr_processor = OCRProcessor()
pdf_extractor = PDFFeatureExtractor()

def extract_features_from_pdf_with_ai(pdf_path: str) -> Dict[str, Any]:
    """
    使用AI推理从PDF中提取特征
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        Dict: 提取和推断的特征信息
    """
    return ocr_processor.extract_features_with_ai_inference(pdf_path)

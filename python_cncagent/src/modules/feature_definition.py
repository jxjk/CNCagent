"""
几何特征识别模块
从图像中识别几何形状，如圆形、矩形、多边形等，并提取其尺寸和位置信息
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple


def identify_features(image: np.ndarray) -> List[Dict]:
    """
    从图像中识别几何特征（圆形、矩形、多边形等）
    
    Args:
        image (numpy.ndarray): 输入图像（预处理后的灰度图）
    
    Returns:
        list: 识别出的特征列表，每个特征包含形状、位置、尺寸等信息
    """
    # 边缘检测
    edges = cv2.Canny(image, 50, 150)
    
    # 寻找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    features = []
    for contour in contours:
        # 过滤小面积轮廓
        area = cv2.contourArea(contour)
        if area < 100:  # 面积小于100的轮廓忽略
            continue
            
        # 近似轮廓
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 识别形状
        shape = identify_shape(approx, contour)
        
        if shape:
            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            feature = {
                "shape": shape,
                "contour": approx,
                "bounding_box": (x, y, w, h),
                "area": area,
                "center": (int(x + w/2), int(y + h/2)),
                "dimensions": (w, h)
            }
            
            # 添加特定形状的额外信息
            if shape == "circle":
                # 计算圆形的半径
                radius = int(w / 2)
                feature["radius"] = radius
            elif shape == "rectangle":
                # 确定长宽
                feature["length"] = max(w, h)
                feature["width"] = min(w, h)
            elif shape == "triangle":
                # 计算三角形顶点
                feature["vertices"] = [tuple(point[0]) for point in approx]
            
            features.append(feature)
    
    return features


def identify_shape(approx: np.ndarray, contour: np.ndarray) -> str:
    """
    根据轮廓近似结果识别形状
    
    Args:
        approx (numpy.ndarray): 轮廓近似结果
        contour (numpy.ndarray): 原始轮廓
    
    Returns:
        str: 识别出的形状类型
    """
    num_vertices = len(approx)
    
    # 计算轮廓的面积和周长
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    
    if num_vertices == 3:
        return "triangle"
    elif num_vertices == 4:
        # 检查是否为正方形或矩形
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h
        if 0.9 <= aspect_ratio <= 1.1:
            return "square"
        else:
            return "rectangle"
    elif num_vertices > 4:
        # 检查是否为圆形
        # 使用轮廓面积与最小外接圆面积的比值
        (x, y), radius = cv2.minEnclosingCircle(contour)
        circle_area = 3.14159 * radius * radius
        if area > 0 and abs(circle_area - area) / area < 0.2:
            return "circle"
        else:
            return "polygon"
    else:
        return "unknown"


def extract_dimensions(features: List[Dict], scale: float = 1.0) -> List[Dict]:
    """
    根据比例尺提取特征的实际尺寸
    
    Args:
        features (list): 识别出的特征列表
        scale (float): 图纸比例尺因子
    
    Returns:
        list: 包含实际尺寸的特征列表
    """
    scaled_features = []
    
    for feature in features:
        scaled_feature = feature.copy()
        
        # 根据比例尺调整尺寸
        if 'length' in scaled_feature:
            scaled_feature['length'] = scaled_feature['length'] * scale
        if 'width' in scaled_feature:
            scaled_feature['width'] = scaled_feature['width'] * scale
        if 'radius' in scaled_feature:
            scaled_feature['radius'] = scaled_feature['radius'] * scale
        if 'dimensions' in scaled_feature:
            w, h = scaled_feature['dimensions']
            scaled_feature['dimensions'] = (w * scale, h * scale)
        
        scaled_features.append(scaled_feature)
    
    return scaled_features


def find_reference_scale(image: np.ndarray, text_regions: List[str]) -> float:
    """
    在图纸中查找比例尺信息
    
    Args:
        image (numpy.ndarray): 输入图像
        text_regions (list): OCR识别出的文本区域
    
    Returns:
        float: 比例尺因子，如果未找到则返回1.0
    """
    # 在文本中查找比例尺信息
    for text in text_regions:
        text_lower = text.lower()
        if 'scale' in text_lower or '比例' in text_lower:
            # 简化的比例尺提取逻辑
            # 实际应用中可能需要更复杂的正则表达式
            if '1:1' in text_lower:
                return 1.0
            elif '1:2' in text_lower:
                return 0.5
            elif '2:1' in text_lower:
                return 2.0
            elif '1:5' in text_lower:
                return 0.2
            elif '1:10' in text_lower:
                return 0.1
    
    # 如果没有找到明确的比例尺信息，返回默认值
    return 1.0
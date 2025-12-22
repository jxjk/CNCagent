"""
几何特征识别模块
从图像中识别几何形状，如圆形、矩形、多边形等，并提取其尺寸和位置信息
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
import math


def identify_features(image: np.ndarray) -> List[Dict]:
    """
    从图像中识别几何特征（圆形、矩形、多边形等）
    
    Args:
        image (numpy.ndarray): 输入图像（预处理后的灰度图）
    
    Returns:
        list: 识别出的特征列表，每个特征包含形状、位置、尺寸等信息
    """
    # 应用高斯模糊以减少噪声
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    
    # 边缘检测
    edges = cv2.Canny(blurred, 50, 150)
    
    # 形态学操作以连接断开的边缘
    kernel = np.ones((2,2), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # 寻找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    features = []
    min_area = 100  # 最小面积阈值
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # 过滤小面积轮廓
        if area < min_area:
            continue
        
        # 计算轮廓的周长
        perimeter = cv2.arcLength(contour, True)
        
        # 跳过周长过小的轮廓
        if perimeter < 10:
            continue
        
        # 轮廓近似
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 计算边界框
        x, y, w, h = cv2.boundingRect(contour)
        
        # 计算轮廓的圆度，用于识别圆形
        _, radius = cv2.minEnclosingCircle(contour)
        radius = int(radius)
        circle_area = math.pi * radius * radius
        
        # 计算长宽比
        aspect_ratio = float(w) / h if h != 0 else 0
        
        # 识别形状
        shape, confidence = identify_shape_with_confidence(approx, contour, area, circle_area)
        
        if shape and confidence > 0.6:  # 设置置信度阈值
            feature = {
                "shape": shape,
                "contour": contour,
                "bounding_box": (x, y, w, h),
                "area": area,
                "center": (int(x + w/2), int(y + h/2)),
                "dimensions": (w, h),
                "confidence": confidence  # 添加置信度
            }
            
            # 添加特定形状的额外信息
            if shape == "circle":
                feature["radius"] = radius
            elif shape == "rectangle" or shape == "square":
                feature["length"] = max(w, h)
                feature["width"] = min(w, h)
                feature["aspect_ratio"] = aspect_ratio
            elif shape == "triangle":
                feature["vertices"] = [tuple(point[0]) for point in approx]
            
            features.append(feature)
    
    # 过滤重复特征
    features = filter_duplicate_features(features)
    
    return features


def identify_shape_with_confidence(approx: np.ndarray, contour: np.ndarray, area: float, circle_area: float) -> Tuple[str, float]:
    """
    识别形状并返回置信度
    
    Args:
        approx: 轮廓近似结果
        contour: 原始轮廓
        area: 轮廓面积
        circle_area: 最小外接圆面积
    
    Returns:
        tuple: (形状名称, 置信度)
    """
    num_vertices = len(approx)
    perimeter = cv2.arcLength(contour, True)
    
    # 计算轮廓的实心度（solidity）
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0
    
    # 计算轮廓的延伸度（extent）
    x, y, w, h = cv2.boundingRect(contour)
    rect_area = w * h
    extent = float(area) / rect_area if rect_area > 0 else 0
    
    if num_vertices == 3:
        # 三角形
        return "triangle", min(1.0, solidity * 1.2)
    elif num_vertices == 4:
        # 检查是否为正方形或矩形
        aspect_ratio = float(w) / h if h != 0 else 0
        if 0.8 <= aspect_ratio <= 1.2:
            return "square", min(1.0, solidity * extent * 1.5)
        else:
            return "rectangle", min(1.0, solidity * extent * 1.3)
    elif num_vertices > 6:
        # 检查是否为圆形
        # 使用轮廓面积与最小外接圆面积的比值
        if area > 0 and circle_area > 0:
            circularity = area / circle_area
            if 0.7 <= circularity <= 1.3 and solidity > 0.8:
                return "circle", min(1.0, circularity * solidity)
    
    # 对于其他形状，根据顶点数和实心度判断
    if num_vertices > 6 and solidity > 0.85:
        return "polygon", min(1.0, solidity * 0.9)
    
    # 无法确定形状
    return "unknown", 0.0


def filter_duplicate_features(features: List[Dict]) -> List[Dict]:
    """
    过滤重复的特征
    
    Args:
        features: 特征列表
    
    Returns:
        过滤后的特征列表
    """
    if not features:
        return []
    
    filtered_features = []
    
    for current_feature in features:
        is_duplicate = False
        
        for existing_feature in filtered_features:
            # 计算中心点距离
            curr_center = current_feature["center"]
            exist_center = existing_feature["center"]
            distance = math.sqrt((curr_center[0] - exist_center[0])**2 + (curr_center[1] - exist_center[1])**2)
            
            # 如果中心点距离小于两个特征最大尺寸的一半，则认为是重复
            curr_max_dim = max(current_feature["dimensions"])
            exist_max_dim = max(existing_feature["dimensions"])
            threshold = max(curr_max_dim, exist_max_dim) / 2
            
            if distance < threshold:
                # 保留置信度更高的特征
                if current_feature.get("confidence", 0) > existing_feature.get("confidence", 0):
                    filtered_features.remove(existing_feature)
                    break
                else:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            filtered_features.append(current_feature)
    
    return filtered_features


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
        # 查找比例尺格式，如 1:1, 1:2, 1:5, 1:10, 等
        import re
        scale_match = re.search(r'(\d+):(\d+)', text_lower)
        if scale_match:
            numerator = int(scale_match.group(1))
            denominator = int(scale_match.group(2))
            if denominator != 0:
                return numerator / denominator
    
    # 检查中文比例尺描述
    for text in text_regions:
        text_lower = text.lower()
        if '比例' in text_lower or 'scale' in text_lower:
            scale_match = re.search(r'(\d+):(\d+)', text_lower)
            if scale_match:
                numerator = int(scale_match.group(1))
                denominator = int(scale_match.group(2))
                if denominator != 0:
                    return numerator / denominator
    
    # 如果没有找到明确的比例尺信息，返回默认值
    return 1.0
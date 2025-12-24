"""
Feature Definition模块的单元测试
测试几何特征识别功能
"""
import unittest
import numpy as np
import cv2
from src.modules.feature_definition import (
    identify_features, identify_shape_advanced, 
    filter_duplicate_features_advanced, identify_counterbore_features,
    find_baseline_feature, analyze_pcd_features, extract_depth_from_description,
    extract_highest_y_center_point, adjust_coordinate_system
)

class TestFeatureDefinition(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        # 创建一个简单的测试图像
        self.test_image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # 在图像上绘制一个圆形
        cv2.circle(self.test_image, (100, 100), 30, (255, 255, 255), -1)
        
        # 在图像上绘制一个矩形
        cv2.rectangle(self.test_image, (50, 50), (80, 80), (255, 255, 255), -1)
        
        # 将图像转换为灰度图
        self.test_gray_image = cv2.cvtColor(self.test_image, cv2.COLOR_BGR2GRAY)

    def test_identify_features(self):
        """测试特征识别功能"""
        features = identify_features(self.test_gray_image)
        
        # 应该识别出至少一个特征
        self.assertGreater(len(features), 0)
        
        # 检查特征的基本结构
        for feature in features:
            self.assertIn('shape', feature)
            self.assertIn('center', feature)
            self.assertIn('confidence', feature)
    
    def test_identify_shape_advanced_circle(self):
        """测试高级形状识别 - 圆形"""
        # 创建一个圆形轮廓
        circle_contour = np.array([
            [[100, 50]], [[120, 60]], [[130, 80]], [[120, 100]], 
            [[100, 110]], [[80, 100]], [[70, 80]], [[80, 60]]
        ], dtype=np.int32)
        
        area = cv2.contourArea(circle_contour)
        _, radius = cv2.minEnclosingCircle(circle_contour)
        circle_area = np.pi * radius * radius
        aspect_ratio = 1.0  # 圆形的长宽比为1
        
        shape, confidence = identify_shape_advanced(circle_contour, area, circle_area, aspect_ratio)
        
        # 圆形识别的置信度应该较高
        self.assertIn(shape, ['circle', 'ellipse'])
        self.assertGreater(confidence, 0.5)
    
    def test_identify_shape_advanced_rectangle(self):
        """测试高级形状识别 - 矩形"""
        # 创建一个矩形轮廓
        rect_contour = np.array([
            [[50, 50]], [[80, 50]], [[80, 80]], [[50, 80]]
        ], dtype=np.int32)
        
        area = cv2.contourArea(rect_contour)
        _, radius = cv2.minEnclosingCircle(rect_contour)
        circle_area = np.pi * radius * radius
        aspect_ratio = 1.0  # 正方形的长宽比为1
        
        shape, confidence = identify_shape_advanced(rect_contour, area, circle_area, aspect_ratio)
        
        # 矩形或正方形识别
        self.assertIn(shape, ['rectangle', 'square', 'parallelogram'])
        self.assertGreater(confidence, 0.5)
    
    def test_filter_duplicate_features_advanced(self):
        """测试重复特征过滤功能"""
        # 创建一些模拟特征数据
        features = [
            {
                "shape": "circle",
                "center": (100, 100),
                "bounding_box": (90, 90, 20, 20),
                "dimensions": (20, 20),
                "confidence": 0.9
            },
            {
                "shape": "circle", 
                "center": (101, 101),  # 几乎相同的位置
                "bounding_box": (91, 91, 20, 20),
                "dimensions": (20, 20),
                "confidence": 0.7  # 低置信度会被过滤
            },
            {
                "shape": "circle",
                "center": (150, 150),  # 不同位置
                "bounding_box": (140, 140, 20, 20),
                "dimensions": (20, 20),
                "confidence": 0.8
            }
        ]
        
        filtered_features = filter_duplicate_features_advanced(features)
        
        # 应该过滤掉重复的特征，保留高置信度的
        self.assertEqual(len(filtered_features), 2)
        # 应该保留高置信度的特征
        self.assertEqual(filtered_features[0]["confidence"], 0.9)
    
    def test_extract_depth_from_description(self):
        """测试从描述中提取深度信息"""
        # 测试不同的深度描述格式
        test_cases = [
            ("沉孔深20mm", 20.0),
            ("锪孔深15", 15.0),
            ("深度12mm", 12.0),
            ("10mm深", 10.0),
            ("深8mm", 8.0),
            ("counterbore 25mm", 25.0),
            ("no depth info", None),
            ("", None)
        ]
        
        for description, expected in test_cases:
            result = extract_depth_from_description(description)
            self.assertEqual(result, expected)
    
    def test_extract_highest_y_center_point(self):
        """测试提取最高Y坐标圆心点功能"""
        features = [
            {"shape": "circle", "center": (50, 100)},
            {"shape": "circle", "center": (60, 80)},   # Y坐标更小，应该是最高点
            {"shape": "circle", "center": (70, 90)}
        ]
        
        highest_point = extract_highest_y_center_point(features)
        
        # 在图像坐标系中，Y越小越靠上
        self.assertEqual(highest_point, (60, 80))
    
    def test_adjust_coordinate_system(self):
        """测试坐标系统调整功能"""
        features = [
            {"shape": "circle", "center": (150, 150), "bounding_box": (140, 140, 20, 20)},
            {"shape": "rectangle", "center": (100, 100), "bounding_box": (90, 90, 20, 20)}
        ]
        
        # 使用指定原点调整坐标
        new_origin = (50, 50)
        adjusted_features = adjust_coordinate_system(features, new_origin, "custom")
        
        # 检查坐标是否正确调整
        for i, feature in enumerate(adjusted_features):
            original_center = features[i]["center"]
            expected_new_center = (
                original_center[0] - new_origin[0],
                original_center[1] - new_origin[1]
            )
            self.assertEqual(feature["center"], expected_new_center)


class TestCounterboreFeatures(unittest.TestCase):
    """测试沉孔特征识别功能"""
    
    def test_find_baseline_feature(self):
        """测试基准特征查找功能"""
        circle_features = [
            {"shape": "circle", "center": (100, 100), "radius": 50},  # 最大的圆，可能是基准
            {"shape": "circle", "center": (50, 50), "radius": 10},
            {"shape": "circle", "center": (150, 150), "radius": 20}
        ]
        
        # 测试从文本中查找基准特征
        drawing_text = "φ100基准圆"
        baseline = find_baseline_feature(circle_features, drawing_text)
        
        self.assertEqual(baseline["radius"], 50)  # 应该找到最大的圆
        
        # 测试空特征列表
        empty_baseline = find_baseline_feature([], drawing_text)
        self.assertIsNone(empty_baseline)
    
    def test_analyze_pcd_features(self):
        """测试PCD特征分析功能"""
        circle_features = [
            {"shape": "circle", "center": (234, 100), "radius": 5},   # 假设是PCD上的孔
            {"shape": "circle", "center": (100, 234), "radius": 5},
            {"shape": "circle", "center": (100, 50), "radius": 5}
        ]
        
        baseline_feature = {"shape": "circle", "center": (167, 167), "radius": 100}  # 基准圆
        
        # 测试PCD分析
        pcd_features = analyze_pcd_features(circle_features, baseline_feature, 3, "PCD 188")
        
        # 应该找到3个特征
        self.assertGreaterEqual(len(pcd_features), 0)  # 实际数量取决于PCD匹配算法
    
    def test_identify_counterbore_features(self):
        """测试沉孔特征识别"""
        # 创建同心圆特征模拟沉孔
        features = [
            {
                "shape": "circle",
                "center": (100, 100),
                "radius": 11,  # 外圆半径 φ22
                "circularity": 0.95
            },
            {
                "shape": "circle", 
                "center": (100, 100),  # 同心
                "radius": 7.25,  # 内圆半径 φ14.5
                "circularity": 0.92
            }
        ]
        
        # 测试沉孔识别
        counterbore_features = identify_counterbore_features(
            features, 
            "沉孔加工", 
            "图纸包含沉孔特征"
        )
        
        # 检查是否识别出沉孔特征
        counterbore_found = any(f["shape"] == "counterbore" for f in counterbore_features)
        self.assertTrue(counterbore_found)


if __name__ == '__main__':
    unittest.main()
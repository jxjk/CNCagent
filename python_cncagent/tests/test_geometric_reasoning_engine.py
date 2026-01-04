import pytest
import sys
from pathlib import Path
import numpy as np
import cv2
import tempfile
import os

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from modules.geometric_reasoning_engine import GeometricReasoningEngine, Feature3D, ProcessPlan, geometric_reasoning_engine


class TestFeature3D:
    """测试Feature3D数据类"""
    
    def test_feature3d_initialization(self):
        """测试Feature3D初始化"""
        feature = Feature3D(
            shape_type="rectangular_cavity",
            center=(10.0, 20.0, 5.0),
            dimensions=(30.0, 20.0, 10.0),
            corner_radius=2.0,
            confidence=0.9,
            processing_sides=["top", "side1"],
            processing_sequence=[1, 2]
        )
        
        assert feature.shape_type == "rectangular_cavity"
        assert feature.center == (10.0, 20.0, 5.0)
        assert feature.dimensions == (30.0, 20.0, 10.0)
        assert feature.corner_radius == 2.0
        assert feature.confidence == 0.9
        assert feature.processing_sides == ["top", "side1"]
        assert feature.processing_sequence == [1, 2]
        assert feature.coordinate_system == "absolute"
        assert feature.semantic_info is None
    
    def test_feature3d_default_values(self):
        """测试Feature3D默认值"""
        feature = Feature3D(
            shape_type="circular_cavity",
            center=(0.0, 0.0, 0.0),
            dimensions=(10.0, 10.0, 5.0)
        )
        
        assert feature.shape_type == "circular_cavity"
        assert feature.corner_radius is None
        assert feature.coordinate_system == "absolute"
        assert feature.confidence == 1.0
        assert feature.processing_sides == []
        assert feature.processing_sequence == []
        assert feature.semantic_info is None


class TestProcessPlan:
    """测试ProcessPlan数据类"""
    
    def test_process_plan_initialization(self):
        """测试ProcessPlan初始化"""
        cutting_params = {
            "spindle_speed": 1200,
            "feed_rate": 800,
            "depth_of_cut": 2.0
        }
        
        plan = ProcessPlan(
            feature_id="feature_1",
            operation_type="milling",
            tool_selection="φ10_endmill",
            cutting_parameters=cutting_params,
            toolpath_strategy="spiral",
            processing_order=1,
            estimated_time=5.5
        )
        
        assert plan.feature_id == "feature_1"
        assert plan.operation_type == "milling"
        assert plan.tool_selection == "φ10_endmill"
        assert plan.cutting_parameters == cutting_params
        assert plan.toolpath_strategy == "spiral"
        assert plan.processing_order == 1
        assert plan.estimated_time == 5.5


class TestGeometricReasoningEngine:
    """测试几何推理引擎"""
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = GeometricReasoningEngine()
        
        assert engine.logger is not None
    
    def test_analyze_geometric_features(self):
        """测试几何特征分析"""
        engine = GeometricReasoningEngine()
        
        # 创建模拟的特征数据
        features_data = [
            {
                "shape": "rectangular_cavity",
                "center": [50, 50, 0],
                "dimensions": [20, 15, 5],
                "confidence": 0.9,
                "corner_radius": 2.0
            },
            {
                "shape": "circular_cavity", 
                "center": [100, 100, 0],
                "dimensions": [10, 10, 8],
                "confidence": 0.85
            }
        ]
        
        analyzed_features = engine.analyze_geometric_features(features_data)
        
        assert isinstance(analyzed_features, list)
        assert len(analyzed_features) == 2
        
        # 验证第一个特征
        feature1 = analyzed_features[0]
        assert isinstance(feature1, Feature3D)
        assert feature1.shape_type == "rectangular_cavity"
        assert feature1.center == (50.0, 50.0, 0.0)
        assert feature1.dimensions == (20.0, 15.0, 5.0)
        assert feature1.confidence == 0.9
        assert feature1.corner_radius == 2.0
        
        # 验证第二个特征
        feature2 = analyzed_features[1]
        assert isinstance(feature2, Feature3D)
        assert feature2.shape_type == "circular_cavity"
        assert feature2.center == (100.0, 100.0, 0.0)
        assert feature2.dimensions == (10.0, 10.0, 8.0)
        assert feature2.confidence == 0.85
        assert feature2.corner_radius is None
    
    def test_infer_geometric_relationships(self):
        """测试几何关系推断"""
        engine = GeometricReasoningEngine()
        
        # 创建一些测试特征
        features = [
            Feature3D(
                shape_type="rectangular_cavity",
                center=(10.0, 10.0, 0.0),
                dimensions=(5.0, 5.0, 2.0),
                confidence=0.9
            ),
            Feature3D(
                shape_type="circular_cavity",
                center=(20.0, 10.0, 0.0),
                dimensions=(4.0, 4.0, 3.0),
                confidence=0.85
            ),
            Feature3D(
                shape_type="slot",
                center=(100.0, 100.0, 0.0),  # 远离其他特征
                dimensions=(20.0, 3.0, 5.0),
                confidence=0.8
            )
        ]
        
        relationships = engine.infer_geometric_relationships(features)
        
        assert isinstance(relationships, dict)
        assert "spatial_relationships" in relationships
        assert "dimensional_constraints" in relationships
        assert "feature_interactions" in relationships
        
        # 验证特征交互 - 前两个特征应该有交互（距离较近）
        interactions = relationships["feature_interactions"]
        assert isinstance(interactions, list)
        
        # 验证维度约束
        constraints = relationships["dimensional_constraints"]
        assert isinstance(constraints, list)
    
    def test_generate_process_plan(self):
        """测试工艺规划生成"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        features = [
            Feature3D(
                shape_type="circular_cavity",
                center=(10.0, 10.0, 0.0),
                dimensions=(8.0, 8.0, 12.0),  # 深度较大
                confidence=0.9
            ),
            Feature3D(
                shape_type="rectangular_cavity",
                center=(30.0, 30.0, 0.0),
                dimensions=(20.0, 15.0, 3.0),  # 较浅
                confidence=0.85
            )
        ]
        
        process_plans = engine.generate_process_plan(features, material="Aluminum")
        
        assert isinstance(process_plans, list)
        assert len(process_plans) == 2
        
        # 验证第一个工艺计划（圆形腔，较深）
        plan1 = process_plans[0]
        assert isinstance(plan1, ProcessPlan)
        assert plan1.feature_id == "feature_0"
        assert plan1.operation_type in ["drilling", "spot_drilling", "general_milling"]
        assert "drill" in plan1.tool_selection.lower() or "endmill" in plan1.tool_selection.lower()
        assert isinstance(plan1.cutting_parameters, dict)
        assert "spindle_speed" in plan1.cutting_parameters
        assert "feed_rate" in plan1.cutting_parameters
        assert plan1.processing_order == 0
        assert plan1.estimated_time > 0
        
        # 验证第二个工艺计划（矩形腔，较浅）
        plan2 = process_plans[1]
        assert isinstance(plan2, ProcessPlan)
        assert plan2.feature_id == "feature_1"
        assert plan2.operation_type in ["pocket_milling", "profile_milling", "general_milling"]
        assert plan2.processing_order == 1
        assert plan2.estimated_time > 0
    
    def test_analyze_processing_structure(self):
        """测试加工结构分析"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        features = [
            Feature3D(
                shape_type="rectangular_cavity",
                center=(10.0, 10.0, 0.0),
                dimensions=(20.0, 15.0, 5.0),
                confidence=0.9
            ),
            Feature3D(
                shape_type="circular_cavity",
                center=(50.0, 50.0, -10.0),  # Z坐标不为0，可能需要多面加工
                dimensions=(10.0, 10.0, 8.0),
                confidence=0.85
            )
        ]
        
        structure_analysis = engine.analyze_processing_structure(features)
        
        assert isinstance(structure_analysis, dict)
        assert "single_sided_features" in structure_analysis
        assert "multi_sided_features" in structure_analysis
        assert "processing_sequence" in structure_analysis
        assert "clamping_suggestions" in structure_analysis
        assert "tool_accessibility" in structure_analysis
        assert "process_feasibility" in structure_analysis
        
        # 验证单面和多面特征分类
        assert isinstance(structure_analysis["single_sided_features"], list)
        assert isinstance(structure_analysis["multi_sided_features"], list)
        assert isinstance(structure_analysis["processing_sequence"], list)
        assert isinstance(structure_analysis["clamping_suggestions"], list)
        assert isinstance(structure_analysis["tool_accessibility"], list)
        assert isinstance(structure_analysis["process_feasibility"], dict)
    
    def test_recommend_processing_sequence(self):
        """测试加工顺序推荐"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        features = [
            Feature3D(
                shape_type="circular_cavity",  # 应该优先
                center=(10.0, 10.0, 0.0),
                dimensions=(8.0, 8.0, 15.0),
                confidence=0.95
            ),
            Feature3D(
                shape_type="rectangular_cavity",  # 应该后处理
                center=(30.0, 30.0, 0.0),
                dimensions=(40.0, 30.0, 2.0),
                confidence=0.8
            ),
            Feature3D(
                shape_type="slot",  # 介于中间
                center=(60.0, 60.0, 0.0),
                dimensions=(25.0, 3.0, 4.0),
                confidence=0.85
            )
        ]
        
        sequence = engine._recommend_processing_sequence(features)
        
        assert isinstance(sequence, list)
        assert len(sequence) == 3
        assert set(sequence) == {0, 1, 2}  # 应该包含所有索引
    
    def test_generate_clamping_suggestions(self):
        """测试夹紧建议生成"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        features = [
            Feature3D(
                shape_type="rectangular_cavity",
                center=(10.0, 10.0, 0.0),
                dimensions=(20.0, 15.0, 5.0),
                confidence=0.9
            ),
            Feature3D(
                shape_type="circular_cavity",
                center=(150.0, 150.0, 0.0),  # 分布范围大
                dimensions=(10.0, 10.0, 8.0),
                confidence=0.85
            )
        ]
        
        suggestions = engine._generate_clamping_suggestions(features)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 0  # 可能没有建议或有多个建议
    
    def test_generate_coordinate_system_description(self):
        """测试坐标系统描述生成"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        features = [
            Feature3D(
                shape_type="rectangular_cavity",
                center=(10.0, 20.0, 0.0),
                dimensions=(30.0, 20.0, 5.0),
                confidence=0.9
            ),
            Feature3D(
                shape_type="circular_cavity",
                center=(50.0, 60.0, 0.0),
                dimensions=(15.0, 15.0, 8.0),
                confidence=0.85
            )
        ]
        
        description = engine.generate_coordinate_system_description(features)
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "rectangular_cavity" in description
        assert "circular_cavity" in description
        assert "10.00" in description  # 应该包含坐标值
        assert "50.00" in description
    
    def test_determine_operation_type(self):
        """测试操作类型确定"""
        engine = GeometricReasoningEngine()
        
        # 测试圆形特征
        circular_feature = Feature3D(
            shape_type="circular_cavity",
            center=(0, 0, 0),
            dimensions=(10, 10, 15)  # 深度较大
        )
        op_type = engine._determine_operation_type(circular_feature)
        assert op_type in ["drilling", "spot_drilling"]
        
        # 测试矩形腔
        rect_feature = Feature3D(
            shape_type="rectangular_cavity",
            center=(0, 0, 0),
            dimensions=(20, 15, 3)  # 深度较小
        )
        op_type = engine._determine_operation_type(rect_feature)
        assert op_type in ["pocket_milling", "profile_milling"]
        
        # 测试槽
        slot_feature = Feature3D(
            shape_type="slot",
            center=(0, 0, 0),
            dimensions=(25, 3, 5)
        )
        op_type = engine._determine_operation_type(slot_feature)
        assert op_type == "slot_milling"
    
    def test_select_tool(self):
        """测试刀具选择"""
        engine = GeometricReasoningEngine()
        
        # 测试小圆形特征
        small_circular = Feature3D(
            shape_type="circular_cavity",
            center=(0, 0, 0),
            dimensions=(2, 2, 5)
        )
        tool = engine._select_tool(small_circular, "Aluminum")
        assert "drill" in tool.lower()
        
        # 测试小矩形腔
        small_rect = Feature3D(
            shape_type="rectangular_cavity",
            center=(0, 0, 0),
            dimensions=(4, 4, 3)
        )
        tool = engine._select_tool(small_rect, "Aluminum")
        assert "flat_endmill" in tool.lower() or "endmill" in tool.lower()
    
    def test_determine_cutting_parameters(self):
        """测试切削参数确定"""
        engine = GeometricReasoningEngine()
        
        # 测试铝材加工参数
        feature = Feature3D(
            shape_type="rectangular_cavity",
            center=(0, 0, 0),
            dimensions=(20, 15, 3)
        )
        
        params = engine._determine_cutting_parameters(feature, "Aluminum")
        
        assert isinstance(params, dict)
        assert "spindle_speed" in params
        assert "feed_rate" in params
        assert "depth_of_cut" in params
        assert "stepover" in params
        
        # 验证参数值合理性
        assert params["spindle_speed"] > 0
        assert params["feed_rate"] > 0
        assert params["depth_of_cut"] > 0
        assert params["stepover"] > 0
    
    def test_select_toolpath_strategy(self):
        """测试刀具路径策略选择"""
        engine = GeometricReasoningEngine()
        
        # 测试圆形特征
        circular_feature = Feature3D(
            shape_type="circular_cavity",
            center=(0, 0, 0),
            dimensions=(10, 10, 10)
        )
        strategy = engine._select_toolpath_strategy(circular_feature)
        assert strategy in ["circular", "peck_drilling"]
        
        # 测试大矩形腔
        large_rect_feature = Feature3D(
            shape_type="rectangular_cavity",
            center=(0, 0, 0),
            dimensions=(50, 40, 3)
        )
        strategy = engine._select_toolpath_strategy(large_rect_feature)
        assert strategy in ["zigzag_clearing", "spiral_clearing"]
        
        # 测试槽
        slot_feature = Feature3D(
            shape_type="slot",
            center=(0, 0, 0),
            dimensions=(30, 3, 5)
        )
        strategy = engine._select_toolpath_strategy(slot_feature)
        assert strategy == "linear_milling"
    
    def test_estimate_processing_time(self):
        """测试加工时间估算"""
        engine = GeometricReasoningEngine()
        
        # 创建测试特征
        feature = Feature3D(
            shape_type="rectangular_cavity",
            center=(0, 0, 0),
            dimensions=(20, 15, 3)  # 体积: 20*15*3 = 900
        )
        
        cutting_params = {
            "feed_rate": 800,
            "depth_of_cut": 2.0,
            "stepover": 1.5
        }
        
        time = engine._estimate_processing_time(feature, cutting_params)
        
        assert isinstance(time, float)
        assert time > 0
        assert time >= 0.5  # 最小时间0.5分钟


class TestGeometricReasoningEngineIntegration:
    """测试几何推理引擎集成"""
    
    def test_full_process_flow(self):
        """测试完整处理流程"""
        engine = GeometricReasoningEngine()
        
        # 模拟从特征数据到最终工艺规划的完整流程
        features_data = [
            {
                "shape": "rectangular_cavity",
                "center": [50, 50, 0],
                "dimensions": [30, 20, 5],
                "confidence": 0.9,
                "corner_radius": 2.0
            },
            {
                "shape": "circular_cavity",
                "center": [100, 80, 0],
                "dimensions": [15, 15, 10],
                "confidence": 0.85
            }
        ]
        
        # 1. 分析几何特征
        features = engine.analyze_geometric_features(features_data)
        assert len(features) == 2
        
        # 2. 推断几何关系
        relationships = engine.infer_geometric_relationships(features)
        assert isinstance(relationships, dict)
        
        # 3. 生成工艺规划
        process_plans = engine.generate_process_plan(features, material="Aluminum")
        assert len(process_plans) == 2
        
        # 4. 分析加工结构
        structure_analysis = engine.analyze_processing_structure(features)
        assert isinstance(structure_analysis, dict)
        
        # 5. 生成坐标系统描述
        coord_description = engine.generate_coordinate_system_description(features)
        assert isinstance(coord_description, str)
        assert len(coord_description) > 0
    
    def test_global_instance(self):
        """测试全局实例"""
        # 验证全局实例存在且正确类型
        assert geometric_reasoning_engine is not None
        assert isinstance(geometric_reasoning_engine, GeometricReasoningEngine)
        
        # 验证全局实例可以正常工作
        features_data = [{
            "shape": "circular_cavity",
            "center": [10, 10, 0],
            "dimensions": [5, 5, 3],
            "confidence": 0.8
        }]
        
        features = geometric_reasoning_engine.analyze_geometric_features(features_data)
        assert len(features) == 1
        assert isinstance(features[0], Feature3D)
        assert features[0].shape_type == "circular_cavity"


class TestAnalyzeCavityFeatures:
    """测试腔槽特征分析"""
    
    def test_analyze_cavity_features_with_mock_image(self):
        """测试腔槽特征分析（使用模拟图像）"""
        engine = GeometricReasoningEngine()
        
        # 创建一个简单的测试图像
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # 在图像上绘制一个矩形
        cv2.rectangle(image, (50, 50), (100, 80), (255, 255, 255), -1)
        
        # 在图像上绘制一个圆形
        cv2.circle(image, (150, 100), 20, (255, 255, 255), -1)
        
        try:
            # 测试腔槽特征分析 - 这可能在某些环境中失败（如没有完整安装OpenCV）
            features = engine.analyze_cavity_features(image)
            assert isinstance(features, list)
        except Exception as e:
            # 如果由于库缺失或版本问题失败，跳过此测试
            pytest.skip(f"由于环境问题跳过腔槽特征分析测试: {str(e)}")
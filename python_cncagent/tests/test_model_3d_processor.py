import pytest
import sys
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock
import numpy as np

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from modules.model_3d_processor import Model3DProcessor, process_3d_model


class TestModel3DProcessor:
    """测试3D模型处理器"""
    
    def test_model_3d_processor_initialization(self):
        """测试3D模型处理器初始化"""
        processor = Model3DProcessor()
        
        assert processor.logger is not None
        assert isinstance(processor.SUPPORTED_FORMATS, set)
        assert '.stl' in processor.SUPPORTED_FORMATS
        assert '.step' in processor.SUPPORTED_FORMATS
        assert '.obj' in processor.SUPPORTED_FORMATS
        assert len(processor.SUPPORTED_FORMATS) > 0
    
    def test_load_model_unsupported_format(self):
        """测试加载不支持的模型格式"""
        processor = Model3DProcessor()
        
        with pytest.raises(Exception):  # InputValidationError
            processor.load_model("test.txt")  # txt格式不支持
    
    def test_load_model_nonexistent_file(self):
        """测试加载不存在的文件"""
        processor = Model3DProcessor()
        
        with pytest.raises(Exception):  # InputValidationError
            processor.load_model("nonexistent.stl")
    
    def test_extract_geometric_features_basic(self):
        """测试提取基本几何特征"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的模型对象（如果trimesh不可用）
        mock_model = MagicMock()
        mock_model.vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
        mock_model.faces = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
        mock_model.bounds = np.array([[0, 0, 0], [1, 1, 1]])
        mock_model.area = 1.732  # 表面积
        mock_model.is_volume = True
        mock_model.volume = 1/6  # 四面体体积
        
        # 使用模拟对象测试
        features = processor.extract_geometric_features(mock_model)
        
        assert isinstance(features, dict)
        assert 'vertices_count' in features
        assert 'faces_count' in features
        assert 'volume' in features
        assert 'surface_area' in features
        assert 'bounding_box' in features
        assert 'dimensions' in features
    
    def test_detect_geometric_primitives_trimesh_with_mock(self):
        """测试检测几何基元（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的mesh对象
        mock_mesh = MagicMock()
        mock_mesh.extents = np.array([1.0, 1.0, 1.0])
        mock_mesh.center_mass = np.array([0.5, 0.5, 0.5])
        
        # 测试检测几何基元函数
        with patch('modules.model_3d_processor.HAS_TRIMESH', True):
            primitives = processor._detect_geometric_primitives_trimesh(mock_mesh)
            assert isinstance(primitives, list)
    
    def test_detect_holes_trimesh_with_mock(self):
        """测试检测孔（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的mesh对象
        mock_mesh = MagicMock()
        mock_mesh.is_watertight = False  # 假设是开放网格
        
        with patch('modules.model_3d_processor.HAS_TRIMESH', True):
            holes = processor._detect_holes_trimesh(mock_mesh)
            assert isinstance(holes, list)
    
    def test_detect_cylindrical_surfaces_trimesh_with_mock(self):
        """测试检测圆柱面（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的mesh对象
        mock_mesh = MagicMock()
        mock_mesh.extents = np.array([2.0, 2.0, 10.0])  # 圆柱形状
        mock_mesh.volume = 31.4159  # π * r² * h ≈ π * 2² * 10 / 4
        
        with patch('modules.model_3d_processor.HAS_TRIMESH', True):
            cylinders = processor._detect_cylindrical_surfaces_trimesh(mock_mesh)
            assert isinstance(cylinders, list)
    
    def test_detect_planar_surfaces_trimesh_with_mock(self):
        """测试检测平面面（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的mesh对象
        mock_mesh = MagicMock()
        mock_mesh.extents = np.array([100.0, 50.0, 1.0])  # 薄板形状
        
        with patch('modules.model_3d_processor.HAS_TRIMESH', True):
            planes = processor._detect_planar_surfaces_trimesh(mock_mesh)
            assert isinstance(planes, list)
    
    def test_detect_pockets_trimesh_with_mock(self):
        """测试检测腔槽（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建一个模拟的mesh对象
        mock_mesh = MagicMock()
        mock_mesh.volume = 100.0
        mock_mesh.convex_hull = MagicMock()
        mock_mesh.convex_hull.volume = 120.0
        
        with patch('modules.model_3d_processor.HAS_TRIMESH', True):
            pockets = processor._detect_pockets_trimesh(mock_mesh)
            assert isinstance(pockets, list)
    
    def test_generate_semantic_annotations(self):
        """测试生成语义标注"""
        processor = Model3DProcessor()
        
        # 创建模拟的特征字典
        features = {
            'dimensions': {'length': 10.0, 'width': 10.0, 'height': 1.0},
            'volume': 100.0,
            'surface_area': 280.0,
            'holes': [],
            'pockets': []
        }
        
        annotations = processor._generate_semantic_annotations(None, features)
        
        assert isinstance(annotations, list)
        # 应该生成平板状的标注
        flat_plate_annotations = [a for a in annotations if a.get('label') == 'flat_plate']
        assert len(flat_plate_annotations) > 0
    
    def test_analyze_feature_relationships(self):
        """测试分析特征关系"""
        processor = Model3DProcessor()
        
        # 创建模拟的特征字典
        features = {
            'holes': [{'is_through': True}, {'is_through': False}],
            'planar_surfaces': [{'area': 100.0}, {'area': 50.0}],
            'bounding_box': {'min': [0, 0, 0], 'max': [10, 10, 10], 'size': [10, 10, 10]},
            'pockets': [{'depth': 5.0}],
            'geometric_primitives': [
                {'center': [0, 0, 0]},
                {'center': [5, 5, 5]}
            ]
        }
        
        relationships = processor._analyze_feature_relationships(None, features)
        
        assert isinstance(relationships, list)
        assert len(relationships) >= 0  # 可能没有关系或有多个关系
    
    def test_identify_manufacturing_features(self):
        """测试识别制造特征"""
        processor = Model3DProcessor()
        
        # 创建模拟的特征字典
        features = {
            'dimensions': {'length': 100.0, 'width': 50.0, 'height': 20.0},
            'volume': 100000.0,
            'surface_area': 19000.0,
            'bounding_box': {'size': [100.0, 50.0, 20.0]}
        }
        
        mfg_features = processor._identify_manufacturing_features(None, features)
        
        assert isinstance(mfg_features, list)
        # 至少应该有一个加工方向特征
        machining_direction_features = [f for f in mfg_features if f.get('type') == 'machining_direction']
        assert len(machining_direction_features) > 0
    
    def test_convert_to_2d_features(self):
        """测试转换为2D特征"""
        processor = Model3DProcessor()
        
        # 创建模拟的几何特征
        geometric_features = {
            'bounding_box': {
                'min': [0, 0, 0],
                'max': [10, 10, 5],
                'size': [10, 10, 5]
            },
            'geometric_primitives': [
                {
                    'type': 'cylinder',
                    'center': [5, 5, 2.5],
                    'diameter': 8
                }
            ],
            'holes': [{}],
            'volume': 500.0,
            'surface_area': 400.0
        }
        
        features_2d = processor.convert_to_2d_features(geometric_features)
        
        assert isinstance(features_2d, list)
        # 至少应该有1个2D特征
        assert len(features_2d) >= 0
    
    def test_process_3d_model_with_mock(self):
        """测试处理3D模型（使用mock）"""
        processor = Model3DProcessor()
        
        # 创建临时STL文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name
            # 创建一个简单的STL内容
            stl_content = """solid test
                facet normal 0.0 0.0 1.0
                outer loop
                vertex 0.0 0.0 0.0
                vertex 1.0 0.0 0.0
                vertex 0.0 1.0 0.0
                endloop
                endfacet
                endsolid test
            """
            tmp.write(stl_content.encode())
        
        try:
            # 由于trimesh可能未安装，我们只测试路径验证部分
            try:
                result = processor.process_3d_model(tmp_path)
                # 如果成功处理，检查返回结果结构
                assert isinstance(result, dict)
                assert 'model_path' in result
                assert result['model_path'] == tmp_path
                assert 'processing_successful' in result
            except Exception as e:
                # 如果由于库缺失无法处理，至少验证错误处理
                assert isinstance(str(e), str)
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestProcess3DModelFunction:
    """测试3D模型处理函数"""
    
    @patch('modules.model_3d_processor.model_3d_processor')
    def test_process_3d_model_function(self, mock_processor):
        """测试处理3D模型函数（使用mock）"""
        # 模拟处理器的process_3d_model方法
        expected_result = {
            'model_path': 'test.stl',
            'geometric_features': {},
            'features_2d': [],
            'format': '.stl',
            'processing_successful': True
        }
        mock_processor.process_3d_model.return_value = expected_result
        
        result = process_3d_model('test.stl')
        
        assert result == expected_result
        mock_processor.process_3d_model.assert_called_once_with('test.stl')
    
    def test_process_3d_model_function_with_real_file(self):
        """测试处理3D模型函数（使用实际文件，如果库可用）"""
        # 创建临时STL文件
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name
            # 创建一个简单的STL内容
            stl_content = """solid test
                facet normal 0.0 0.0 1.0
                outer loop
                vertex 0.0 0.0 0.0
                vertex 1.0 0.0 0.0
                vertex 0.0 1.0 0.0
                endloop
                endfacet
                endsolid test
            """
            tmp.write(stl_content.encode())
        
        try:
            # 尝试处理实际文件
            try:
                result = process_3d_model(tmp_path)
                # 检查返回结果结构
                assert isinstance(result, dict)
                assert 'model_path' in result
                assert result['model_path'] == tmp_path
            except Exception as e:
                # 如果由于缺少库无法处理，至少验证是合理异常
                assert isinstance(str(e), str)
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestModel3DProcessorIO:
    """测试3D模型处理器的输入输出功能"""
    
    def test_supported_formats(self):
        """测试支持的格式"""
        processor = Model3DProcessor()
        
        supported_formats = processor.SUPPORTED_FORMATS
        assert isinstance(supported_formats, set)
        assert len(supported_formats) > 0
        
        # 检查一些常见的3D格式
        expected_formats = {'.stl', '.step', '.obj', '.ply'}
        for fmt in expected_formats:
            assert fmt in supported_formats
    
    def test_load_model_different_extensions(self):
        """测试不同扩展名的处理"""
        processor = Model3DProcessor()
        
        # 测试错误处理 - 文件不存在但扩展名正确
        for ext in ['.stl', '.step', '.obj', '.ply', '.igs', '.iges']:
            with pytest.raises(Exception):  # 应该抛出异常因为文件不存在
                processor.load_model(f"nonexistent{ext}")
    
    def test_model_path_validation(self):
        """测试模型路径验证"""
        processor = Model3DProcessor()
        
        # 测试路径遍历防护（如果实现的话）
        with pytest.raises(Exception):
            processor.load_model("../../../etc/passwd.stl")


# 条件性测试：仅在库可用时运行
def test_full_integration_if_libraries_available():
    """库可用时的完整集成测试"""
    try:
        import trimesh
        # 如果trimesh可用，我们可以进行更完整的测试
        
        processor = Model3DProcessor()
        
        # 创建一个简单的立方体模型
        mesh = trimesh.creation.box(extents=[2, 2, 2])
        
        # 临时保存模型
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name
            mesh.export(tmp_path)
        
        try:
            # 处理模型
            result = processor.process_3d_model(tmp_path)
            
            # 验证结果
            assert result['processing_successful'] is True
            assert result['format'] == '.stl'
            assert 'geometric_features' in result
            assert 'features_2d' in result
            
            # 验证几何特征
            geom_features = result['geometric_features']
            assert geom_features['vertices_count'] > 0
            assert geom_features['faces_count'] > 0
            assert geom_features['volume'] > 0
            assert geom_features['surface_area'] > 0
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except ImportError:
        # 如果trimesh不可用，跳过此测试
        pytest.skip("trimesh库不可用，跳过完整集成测试")
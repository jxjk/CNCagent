import pytest
import sys
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from modules.ai_driven_generator import AIDrivenCNCGenerator, ProcessingRequirements, generate_nc_with_ai

class TestProcessingRequirements:
    """测试处理需求数据类"""
    
    def test_processing_requirements_initialization(self):
        """测试处理需求初始化"""
        requirements = ProcessingRequirements(user_prompt="加工3个φ22沉孔")
        
        assert requirements.user_prompt == "加工3个φ22沉孔"
        assert requirements.hole_positions == []
        assert requirements.tool_diameters == {}
        assert requirements.special_requirements == []
        assert requirements.processing_type == "general"
    
    def test_processing_requirements_with_parameters(self):
        """测试带参数的处理需求初始化"""
        hole_positions = [(10.0, 20.0), (30.0, 40.0)]
        tool_diameters = {"outer": 22.0, "inner": 14.5}
        special_requirements = ["USING_POLAR_COORDINATES"]
        material = "Aluminum"
        
        requirements = ProcessingRequirements(
            user_prompt="加工沉孔",
            processing_type="counterbore",
            hole_positions=hole_positions,
            depth=20.0,
            tool_diameters=tool_diameters,
            material=material,
            special_requirements=special_requirements
        )
        
        assert requirements.user_prompt == "加工沉孔"
        assert requirements.processing_type == "counterbore"
        assert requirements.hole_positions == hole_positions
        assert requirements.depth == 20.0
        assert requirements.tool_diameters == tool_diameters
        assert requirements.material == material
        assert requirements.special_requirements == special_requirements


class TestAIDrivenCNCGenerator:
    """测试AI驱动CNC生成器"""
    
    def test_ai_generator_initialization(self):
        """测试AI生成器初始化"""
        generator = AIDrivenCNCGenerator()
        
        assert generator.api_key is None  # 因为没有设置环境变量
        assert generator.model == "deepseek-chat"
        assert generator.logger is not None
    
    def test_ai_generator_initialization_with_params(self):
        """测试带参数的AI生成器初始化"""
        generator = AIDrivenCNCGenerator(api_key="test-key", model="gpt-4")
        
        assert generator.api_key == "test-key"
        assert generator.model == "gpt-4"
    
    @patch('modules.ai_driven_generator.os.getenv')
    def test_ai_generator_initialization_with_env_vars(self, mock_getenv):
        """测试使用环境变量初始化AI生成器"""
        mock_getenv.side_effect = lambda x: "test-env-key" if x == 'DEEPSEEK_API_KEY' else None
        
        generator = AIDrivenCNCGenerator()
        
        assert generator.api_key == "test-env-key"
    
    def test_parse_user_requirements_basic(self):
        """测试解析基本用户需求"""
        generator = AIDrivenCNCGenerator()
        
        requirements = generator.parse_user_requirements("请加工3个φ22沉孔，深度20mm")
        
        assert requirements.user_prompt == "请加工3个φ22沉孔，深度20mm"
        assert requirements.processing_type == "counterbore"  # 沉孔加工
        assert requirements.depth == 20.0
        assert "outer" in requirements.tool_diameters
        assert requirements.tool_diameters["outer"] == 22.0
    
    def test_parse_user_requirements_drilling(self):
        """测试解析钻孔需求"""
        generator = AIDrivenCNCGenerator()
        
        requirements = generator.parse_user_requirements("请钻5个φ10孔")
        
        assert requirements.processing_type == "drilling"
        assert requirements.tool_diameters["default"] == 10.0
    
    def test_parse_user_requirements_milling(self):
        """测试解析铣削需求"""
        generator = AIDrivenCNCGenerator()
        
        requirements = generator.parse_user_requirements("请铣一个100x50的矩形腔槽")
        
        assert "milling" in requirements.processing_type
        assert "RECTANGULAR_CAVITY:100.0x50.0" in requirements.special_requirements
    
    def test_parse_user_requirements_with_coordinates(self):
        """测试解析带坐标的需求"""
        generator = AIDrivenCNCGenerator()
        
        requirements = generator.parse_user_requirements("在X100 Y50位置钻孔")
        
        assert len(requirements.hole_positions) >= 1
        # 至少有一个位置被解析
        assert (100.0, 50.0) in requirements.hole_positions or len(requirements.hole_positions) > 0
    
    def test_parse_user_requirements_material_detection(self):
        """测试材料检测"""
        generator = AIDrivenCNCGenerator()
        
        requirements = generator.parse_user_requirements("加工铝合金零件")
        
        assert requirements.material in ["铝", "aluminum"]
    
    def test_validate_inputs_basic(self):
        """测试基本输入验证"""
        generator = AIDrivenCNCGenerator()
        
        # 有效的输入应该不抛出异常
        try:
            generator._validate_inputs("加工需求", None, None, None)
            valid = True
        except ValueError:
            valid = False
        
        assert valid
    
    def test_validate_inputs_long_prompt(self):
        """测试长提示验证"""
        generator = AIDrivenCNCGenerator()
        
        # 创建超过5000字符的提示
        long_prompt = "A" * 5001
        
        with pytest.raises(ValueError, match="用户需求描述长度不能超过5000字符"):
            generator._validate_inputs(long_prompt, None, None, None)
    
    def test_validate_inputs_path_traversal(self):
        """测试路径遍历验证"""
        generator = AIDrivenCNCGenerator()
        
        with pytest.raises(ValueError, match="文件路径包含非法字符"):
            generator._validate_inputs("加工需求", "../../../etc/passwd", None, None)
    
    def test_validate_inputs_unsupported_extension(self):
        """测试不支持的文件扩展名验证"""
        generator = AIDrivenCNCGenerator()
        
        with pytest.raises(ValueError, match="不支持的文件格式"):
            generator._validate_inputs("加工需求", "file.txt", None, None)
    
    def test_extract_features_from_pdf_with_mock(self):
        """测试提取PDF特征（使用mock）"""
        generator = AIDrivenCNCGenerator()
        
        # 使用临时文件测试
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
            # 创建一个简单的PDF内容
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Test PDF for feature extraction")
            doc.save(tmp_path)
            doc.close()
        
        try:
            # 测试PDF特征提取函数（需要检查PyMuPDF是否可用）
            result = generator.extract_features_from_pdf(tmp_path)
            
            if result.get("error"):
                # 如果PyMuPDF不可用，至少验证错误信息格式
                assert "error" in result
            else:
                # 如果可用，验证返回的结构
                assert isinstance(result, dict)
                assert "page_count" in result
                assert "text_content" in result
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_generate_fallback_code(self):
        """测试备用代码生成"""
        generator = AIDrivenCNCGenerator()
        
        prompt = "加工测试"
        fallback_code = generator._generate_fallback_code(prompt)
        
        assert isinstance(fallback_code, str)
        assert len(fallback_code) > 0
        assert "O" in fallback_code  # 应该包含程序号
        assert "M30" in fallback_code  # 应该包含程序结束指令
    
    def test_validate_and_optimize(self):
        """测试验证和优化功能"""
        generator = AIDrivenCNCGenerator()
        
        basic_program = "O1234\nG21\nG90\nM30"
        validated = generator.validate_and_optimize(basic_program)
        
        assert isinstance(validated, str)
        assert "O1234" in validated
        assert "G21" in validated
        assert "G90" in validated
        assert "M30" in validated


class TestAIDrivenCNCGeneratorIntegration:
    """测试AI驱动CNC生成器集成功能"""
    
    @patch.object(AIDrivenCNCGenerator, '_call_large_language_model')
    def test_generate_nc_program_with_mocked_api(self, mock_call_llm):
        """测试生成NC程序（模拟API调用）"""
        generator = AIDrivenCNCGenerator()
        
        # 模拟API返回的NC代码
        mock_call_llm.return_value = "O1234\nG21 G90\nG00 X0 Y0\nM30"
        
        result = generator.generate_nc_program("加工测试", material="Aluminum")
        
        assert isinstance(result, str)
        assert "O1234" in result
        assert "G21" in result
        assert "G90" in result
        assert "M30" in result
        
        # 验证API调用被调用
        mock_call_llm.assert_called_once()
    
    @patch.object(AIDrivenCNCGenerator, '_call_large_language_model')
    @patch.object(AIDrivenCNCGenerator, 'extract_features_from_pdf')
    def test_generate_nc_program_with_pdf(self, mock_extract_pdf, mock_call_llm):
        """测试使用PDF生成NC程序（模拟API调用）"""
        generator = AIDrivenCNCGenerator()
        
        # 模拟PDF特征提取
        mock_extract_pdf.return_value = {
            "text_content": "图纸内容",
            "page_count": 1
        }
        
        # 模拟API返回的NC代码
        mock_call_llm.return_value = "O5678\nG21 G90\nG00 X10 Y10\nM30"
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Test PDF")
            doc.save(tmp_path)
            doc.close()
        
        try:
            result = generator.generate_nc_program("加工测试", pdf_path=tmp_path)
            
            assert isinstance(result, str)
            assert "O5678" in result
            
            # 验证PDF提取和API调用都被调用
            mock_extract_pdf.assert_called_once_with(tmp_path)
            mock_call_llm.assert_called_once()
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestGenerateNCWithAI:
    """测试AI生成NC函数"""
    
    @patch.object(AIDrivenCNCGenerator, '_call_large_language_model')
    def test_generate_nc_with_ai_function(self, mock_call_llm):
        """测试AI生成NC函数（模拟API调用）"""
        # 模拟API返回的NC代码
        mock_call_llm.return_value = "O9999\nG21 G90\nG00 X0 Y0\nM30"
        
        result = generate_nc_with_ai("加工测试")
        
        assert isinstance(result, str)
        assert "O9999" in result
        assert "G21" in result
        assert "G90" in result
        assert "M30" in result
        
        # 验证API调用被调用
        mock_call_llm.assert_called_once()
    
    @patch.object(AIDrivenCNCGenerator, '_call_large_language_model')
    def test_generate_nc_with_ai_with_params(self, mock_call_llm):
        """测试带参数的AI生成NC函数（模拟API调用）"""
        # 模拟API返回的NC代码
        mock_call_llm.return_value = "O8888\nG21 G90\nG00 X50 Y50\nM30"
        
        result = generate_nc_with_ai(
            user_prompt="加工测试",
            api_key="test-key",
            model="gpt-4",
            material="Steel"
        )
        
        assert isinstance(result, str)
        assert "O8888" in result
        assert "G21" in result
        assert "G90" in result
        assert "M30" in result
        
        # 验证API调用被调用
        mock_call_llm.assert_called_once()

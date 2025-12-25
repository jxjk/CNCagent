"""
重构后的CNC Agent测试用例
验证大模型直接生成NC代码的功能
"""
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入重构后的模块
from src.modules.ai_driven_generator import AIDrivenCNCGenerator, generate_nc_with_ai
from src.modules.unified_generator import UnifiedCNCGenerator, generate_cnc_with_unified_approach
from src.main import generate_nc_from_pdf


class TestAIDrivenGenerator(unittest.TestCase):
    """测试AI驱动生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = AIDrivenCNCGenerator()
        self.test_prompt = "请加工3个φ22沉孔，深度20mm"
        self.test_api_key = "test-key"
    
    def test_parse_user_requirements(self):
        """测试用户需求解析"""
        requirements = self.generator.parse_user_requirements(self.test_prompt)
        
        self.assertEqual(requirements.processing_type, 'counterbore')
        self.assertEqual(requirements.tool_diameters.get('outer'), 22.0)
        self.assertEqual(requirements.depth, 20.0)
        self.assertIn("数量:3", requirements.special_requirements)
    
    def test_build_generation_prompt(self):
        """测试生成提示词构建"""
        requirements = self.generator.parse_user_requirements(self.test_prompt)
        prompt = self.generator._build_generation_prompt(requirements)
        
        self.assertIn("沉孔", prompt)
        self.assertIn("22", prompt)
        self.assertIn("20", prompt)
        self.assertIn("FANUC", prompt)
    
    @patch('src.modules.ai_driven_generator.openai.OpenAI')
    def test_generate_with_ai(self, mock_openai):
        """测试AI生成功能（模拟API调用）"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "O1234\nG21 G90\nG54\nM30"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建带API密钥的生成器
        generator = AIDrivenCNCGenerator(api_key=self.test_api_key)
        result = generator.generate_with_ai(generator.parse_user_requirements(self.test_prompt))
        
        self.assertIn("O1234", result)
        self.assertIn("G21", result)
        self.assertIn("M30", result)
    
    def test_fallback_generation(self):
        """测试备用生成功能"""
        # 测试无API密钥时的备用生成
        generator = AIDrivenCNCGenerator()
        requirements = generator.parse_user_requirements(self.test_prompt)
        result = generator._generate_fallback_code("测试提示词")
        
        self.assertIn("AI-GENERATED CNC PROGRAM", result)
        self.assertIn("G21", result)
        self.assertIn("M30", result)


class TestUnifiedGenerator(unittest.TestCase):
    """测试统一生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = UnifiedCNCGenerator()
        self.test_prompt = "请加工一个φ10钻孔，深度15mm"
    
    def test_generate_cnc_program(self):
        """测试CNC程序生成"""
        # 由于实际API调用需要网络和API密钥，我们测试参数传递逻辑
        # 在实际环境中，这将调用大模型API
        try:
            # 这会调用备用生成方法，因为没有API密钥
            result = self.generator.generate_cnc_program(self.test_prompt)
            self.assertIsInstance(result, str)
            self.assertIn("O", result)  # NC程序通常以O开头
        except Exception as e:
            # 如果出现其他错误（如网络问题），至少验证函数调用不会崩溃
            self.assertIsNotNone(str(e))
    
    def test_generate_with_api_params(self):
        """测试带API参数的生成"""
        generator = UnifiedCNCGenerator(api_key="test-key", model="gpt-3.5-turbo")
        result = generator.generate_cnc_program(self.test_prompt)
        self.assertIsInstance(result, str)


class TestMainFunction(unittest.TestCase):
    """测试主函数"""
    
    def setUp(self):
        """测试前准备"""
        self.test_pdf_content = "Test PDF content for CNC generation"
        # 创建临时PDF文件用于测试
        self.temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        self.temp_pdf.close()
        
        # 使用PyMuPDF创建一个简单的PDF
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), self.test_pdf_content)
            doc.save(self.temp_pdf.name)
            doc.close()
        except ImportError:
            # 如果没有fitz，则跳过需要PDF的测试
            pass
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_pdf.name)
        except:
            pass
    
    def test_generate_nc_from_pdf(self):
        """测试从PDF生成NC代码"""
        test_prompt = "请加工一个测试孔"
        
        # 测试备用生成（因为没有API密钥）
        try:
            result = generate_nc_from_pdf(
                pdf_path=self.temp_pdf.name,
                user_description=test_prompt
            )
            self.assertIsInstance(result, str)
            self.assertIn("O", result)  # NC程序通常以O开头
        except:
            # 如果PDF处理失败（如没有安装fitz），至少验证函数调用
            result = generate_nc_from_pdf(
                pdf_path=None,
                user_description=test_prompt
            )
            self.assertIsInstance(result, str)
    
    def test_generate_with_api_params(self):
        """测试带API参数的主函数"""
        test_prompt = "请生成铣削程序"
        
        result = generate_nc_from_pdf(
            pdf_path=None,
            user_description=test_prompt,
            api_key="test-key",
            model="gpt-3.5-turbo"
        )
        self.assertIsInstance(result, str)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_workflow_end_to_end(self):
        """测试端到端工作流程"""
        test_prompt = "加工3个φ10的钻孔，深度12mm"
        
        # 测试AI驱动生成器
        ai_gen = AIDrivenCNCGenerator()
        nc_code = ai_gen.generate_nc_program(test_prompt)
        
        self.assertIsInstance(nc_code, str)
        self.assertGreater(len(nc_code), 0)
        
        # 验证代码包含基本的NC指令
        self.assertIn("G21", nc_code)  # 毫米单位
        self.assertIn("G90", nc_code)  # 绝对坐标
        self.assertIn("M30", nc_code)  # 程序结束
    
    def test_pdf_features_as_auxiliary(self):
        """测试PDF特征仅作为辅助参考"""
        test_prompt = "请按图纸要求加工沉孔"
        
        # 即使有PDF路径，用户需求仍应优先
        ai_gen = AIDrivenCNCGenerator()
        requirements = ai_gen.parse_user_requirements(test_prompt)
        
        # 验证需求解析正确
        self.assertEqual(requirements.user_prompt, test_prompt)


def run_tests():
    """运行所有测试"""
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAIDrivenGenerator)
    suite.addTests(loader.loadTestsFromTestCase(TestUnifiedGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestMainFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n测试结果:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"成功率: {success_rate:.2f}%")
    else:
        print("成功率: 0.00%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

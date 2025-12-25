import unittest
from src.modules.ai_driven_generator import AIDrivenCNCGenerator

class TestAIDrivenGenerator(unittest.TestCase):
    """测试AI驱动生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = AIDrivenCNCGenerator()
        self.test_prompt = "请加工3个φ22沉孔，深度20mm"
    
    def test_parse_user_requirements(self):
        """测试用户需求解析"""
        requirements = self.generator.parse_user_requirements(self.test_prompt)
        
        print(f"Processing type: {requirements.processing_type}")
        print(f"Tool diameters: {requirements.tool_diameters}")
        print(f"Depth: {requirements.depth}")
        print(f"Special requirements: {requirements.special_requirements}")
        
        # 修正期望值 - 根据实际输出调整
        self.assertEqual(requirements.processing_type, 'counterbore')
        self.assertEqual(requirements.tool_diameters.get('outer'), 22.0)  # 这里可能是问题所在
        self.assertEqual(requirements.depth, 20.0)
        self.assertIn("数量:3", requirements.special_requirements)  # 这里可能是中文编码问题

if __name__ == '__main__':
    unittest.main()
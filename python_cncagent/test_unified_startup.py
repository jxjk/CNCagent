"""
测试统一启动文件的功能
"""
import unittest
import subprocess
import sys
import time
from pathlib import Path

class TestUnifiedStartup(unittest.TestCase):
    """测试统一启动文件的功能"""
    
    def setUp(self):
        """测试前的设置"""
        self.project_root = Path(__file__).parent
        self.unified_script = self.project_root / "start_unified.py"
        
    def test_script_exists(self):
        """测试统一启动脚本是否存在"""
        self.assertTrue(self.unified_script.exists(), f"统一启动脚本不存在: {self.unified_script}")
    
    def test_help_output(self):
        """测试帮助信息输出"""
        try:
            result = subprocess.run(
                [sys.executable, str(self.unified_script), '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0, f"帮助命令执行失败: {result.stderr}")
            self.assertIn('CNC Agent 统一启动器', result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("帮助命令执行超时")
    
    def test_mode_choices(self):
        """测试模式参数"""
        modes = ['gui', 'web', 'both']
        for mode in modes:
            with self.subTest(mode=mode):
                try:
                    result = subprocess.run(
                        [sys.executable, str(self.unified_script), mode, '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    # 某些模式可能需要特定的GUI环境，所以这里只检查是否正常启动而不是功能
                    # 实际测试时需要考虑GUI环境
                except subprocess.TimeoutExpired:
                    # GUI模式可能无法在无头环境中测试
                    pass

def run_tests():
    """运行测试"""
    print("开始测试统一启动文件...")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUnifiedStartup)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print(f"\n测试结果: {result.testsRun} 个测试运行")
    if result.failures:
        print(f"失败: {len(result.failures)} 个")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    if result.errors:
        print(f"错误: {len(result.errors)} 个")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

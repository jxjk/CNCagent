"""
GCode Generation模块的单元测试
测试FANUC NC程序生成功能
"""
import unittest
from src.modules.gcode_generation import (
    generate_fanuc_nc, _get_tool_number, 
    _generate_drilling_code, _generate_tapping_code_with_full_process,
    _generate_counterbore_code, _generate_milling_code
)

class TestGCodeGeneration(unittest.TestCase):
    
    def test_get_tool_number(self):
        """测试刀具编号获取功能"""
        tool_types = [
            ("center_drill", 1),
            ("drill_bit", 2),
            ("tap", 3),
            ("counterbore_tool", 4),
            ("end_mill", 5),
            ("unknown_tool", 5)  # 默认值
        ]
        
        for tool_type, expected_num in tool_types:
            with self.subTest(tool_type=tool_type):
                result = _get_tool_number(tool_type)
                if tool_type == "unknown_tool":
                    self.assertEqual(result, 5)  # 默认值
                else:
                    self.assertEqual(result, expected_num)
    
    def test_generate_drilling_code(self):
        """测试钻孔代码生成功能"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            },
            {
                "shape": "circle", 
                "center": (100.0, 100.0)
            }
        ]
        
        description_analysis = {
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "普通钻孔加工"
        }
        
        drilling_code = _generate_drilling_code(features, description_analysis)
        
        # 检查生成的代码包含必要的G代码指令
        code_str = "\n".join(drilling_code)
        self.assertIn("G83", code_str)  # 深孔钻削循环
        self.assertIn("M03", code_str)  # 主轴正转
        self.assertIn("M08", code_str)  # 冷却液开
        self.assertIn("G80", code_str)  # 取消固定循环
    
    def test_generate_tapping_code_with_full_process(self):
        """测试攻丝代码生成功能"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            }
        ]
        
        description_analysis = {
            "depth": 14.0,
            "description": "M10螺纹攻丝"
        }
        
        tapping_code = _generate_tapping_code_with_full_process(features, description_analysis)
        
        # 检查攻丝代码包含完整的工艺流程
        code_str = "\n".join(tapping_code)
        self.assertIn("PILOT DRILLING", code_str)  # 点孔工序
        self.assertIn("DRILLING OPERATION", code_str)  # 钻孔工序
        self.assertIn("TAPPING OPERATION", code_str)  # 攻丝工序
        self.assertIn("G84", code_str)  # 攻丝循环
    
    def test_generate_counterbore_code(self):
        """测试沉孔代码生成功能"""
        features = [
            {
                "shape": "counterbore",
                "center": (100.0, 100.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0
            }
        ]
        
        description_analysis = {
            "description": "φ22沉孔深20mm + φ14.5贯通底孔"
        }
        
        counterbore_code = _generate_counterbore_code(features, description_analysis)
        
        # 检查沉孔代码包含完整的工艺流程
        code_str = "\n".join(counterbore_code)
        self.assertIn("PILOT DRILLING", code_str)  # 点孔工序
        self.assertIn("DRILLING OPERATION", code_str)  # 钻孔工序
        self.assertIn("COUNTERBORE OPERATION", code_str)  # 锪孔工序
    
    def test_generate_fanuc_nc_drilling(self):
        """测试钻孔加工的完整NC程序生成"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            },
            {
                "shape": "circle",
                "center": (100.0, 100.0)
            }
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "钻孔加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 检查程序结构
        self.assertIn("O0001", nc_code)  # 程序号
        self.assertIn("G21", nc_code)    # 毫米单位
        self.assertIn("G90", nc_code)    # 绝对坐标
        self.assertIn("G83", nc_code)    # 深孔钻削
        self.assertIn("M30", nc_code)    # 程序结束
    
    def test_generate_fanuc_nc_tapping(self):
        """测试攻丝加工的完整NC程序生成"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            }
        ]
        
        description_analysis = {
            "processing_type": "tapping",
            "depth": 14.0,
            "description": "M10螺纹攻丝"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 检查程序包含攻丝相关指令
        self.assertIn("O0001", nc_code)  # 程序号
        self.assertIn("TAPPING", nc_code)  # 攻丝工序
        self.assertIn("G84", nc_code)    # 攻丝循环
    
    def test_generate_fanuc_nc_counterbore(self):
        """测试沉孔加工的完整NC程序生成"""
        features = [
            {
                "shape": "counterbore",
                "center": (100.0, 100.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0
            }
        ]
        
        description_analysis = {
            "processing_type": "counterbore",
            "description": "φ22沉孔深20mm + φ14.5贯通底孔"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 检查程序包含沉孔相关指令
        self.assertIn("O0001", nc_code)  # 程序号
        self.assertIn("COUNTERBORE", nc_code)  # 沉孔工序
        self.assertIn("G81", nc_code)    # 锪孔循环
    
    def test_generate_fanuc_nc_with_keywords(self):
        """测试通过关键词识别加工类型的NC程序生成"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            }
        ]
        
        # 测试通过"沉孔"关键词识别
        description_analysis = {
            "description": "φ22沉孔深20mm + φ14.5贯通底孔"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("COUNTERBORE", nc_code)
        
        # 测试通过"攻丝"关键词识别
        description_analysis = {
            "description": "M10螺纹攻丝"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("TAPPING", nc_code)
        
        # 测试通过"钻孔"关键词识别
        description_analysis = {
            "description": "普通钻孔"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("DRILLING", nc_code)


class TestGCodeGenerationEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_generate_with_empty_features(self):
        """测试空特征列表的处理"""
        features = []
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "钻孔加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 即使没有特征，也应生成基本的程序框架
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)
        self.assertIn("G90", nc_code)
    
    def test_generate_with_none_values(self):
        """测试None值的处理"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            }
        ]
        
        # 测试深度和进给率为None的情况
        description_analysis = {
            "processing_type": "drilling",
            "depth": None,
            "feed_rate": None,
            "description": "钻孔加工"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 应该使用默认值而不是报错
        self.assertIn("O0001", nc_code)
    
    def test_generate_tapping_with_different_thread_sizes(self):
        """测试不同螺纹规格的攻丝代码生成"""
        features = [
            {
                "shape": "circle",
                "center": (50.0, 50.0)
            }
        ]
        
        thread_specs = ["M3", "M4", "M5", "M6", "M8", "M10", "M12"]
        
        for thread_spec in thread_specs:
            with self.subTest(thread_spec=thread_spec):
                description_analysis = {
                    "depth": 10.0,
                    "description": f"{thread_spec}螺纹攻丝"
                }
                
                nc_code = generate_fanuc_nc(features, description_analysis)
                
                # 检查每种规格都能生成有效代码
                self.assertIsInstance(nc_code, str)
                self.assertGreater(len(nc_code), 0)
                self.assertIn("O0001", nc_code)


if __name__ == '__main__':
    unittest.main()

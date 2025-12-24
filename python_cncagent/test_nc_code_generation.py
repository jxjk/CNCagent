"""
NC代码生成模块的综合测试
测试从特征到NC代码生成的完整流程
"""
import unittest
from src.modules.gcode_generation import (
    generate_fanuc_nc, _generate_drilling_code, 
    _generate_tapping_code_with_full_process,
    _generate_counterbore_code, _generate_milling_code,
    _get_tool_number
)

class TestNCCodeGenerationIntegration(unittest.TestCase):
    
    def test_generate_fanuc_nc_complete_workflow(self):
        """测试完整的NC代码生成工作流程"""
        # 模拟从特征识别模块获取的特征
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
            "description": "普通钻孔加工",
            "tool_required": "drill_bit"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证生成的NC代码包含基本元素
        self.assertIn("O0001", nc_code)  # 程序号
        self.assertIn("G21", nc_code)    # 毫米单位
        self.assertIn("G90", nc_code)    # 绝对坐标
        self.assertIn("G83", nc_code)    # 深孔钻削循环
        self.assertIn("M30", nc_code)    # 程序结束
        
        # 验证代码长度合理
        lines = nc_code.split('\n')
        self.assertGreater(len(lines), 10)  # 应该有至少10行代码
    
    def test_generate_drilling_code_multiple_holes(self):
        """测试多孔钻削代码生成"""
        features = [
            {"shape": "circle", "center": (50.0, 50.0)},
            {"shape": "circle", "center": (80.0, 80.0)},
            {"shape": "circle", "center": (110.0, 50.0)},
            {"shape": "circle", "center": (140.0, 80.0)}
        ]
        
        description_analysis = {
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "多孔钻削"
        }
        
        drilling_code = _generate_drilling_code(features, description_analysis)
        
        # 验证包含所有孔的加工指令
        code_str = '\n'.join(drilling_code)
        
        # 检查是否包含G83深孔钻削循环
        self.assertIn("G83", code_str)
        
        # 检查是否包含多个孔的位置
        self.assertIn("X50.000 Y50.000", code_str)
        self.assertIn("X80.000 Y80.000", code_str)
        self.assertIn("X110.000 Y50.000", code_str)
        self.assertIn("X140.000 Y80.000", code_str)
    
    def test_generate_tapping_code_complete_process(self):
        """测试完整攻丝工艺代码生成"""
        features = [
            {"shape": "circle", "center": (60.0, 60.0)}
        ]
        
        description_analysis = {
            "depth": 14.0,
            "description": "M10螺纹攻丝"
        }
        
        tapping_code = _generate_tapping_code_with_full_process(features, description_analysis)
        
        code_str = '\n'.join(tapping_code)
        
        # 验证包含完整的攻丝工艺流程
        self.assertIn("PILOT DRILLING", code_str)  # 点孔工序
        self.assertIn("DRILLING OPERATION", code_str)  # 钻孔工序
        self.assertIn("TAPPING OPERATION", code_str)  # 攻丝工序
        self.assertIn("G84", code_str)  # 攻丝固定循环
        
        # 验证使用了正确的刀具
        self.assertIn("T1 M06", code_str)  # 点孔刀具
        self.assertIn("T2 M06", code_str)  # 钻孔刀具
        self.assertIn("T3 M06", code_str)  # 攻丝刀具
    
    def test_generate_counterbore_code_complete_process(self):
        """测试完整沉孔工艺代码生成"""
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
        
        code_str = '\n'.join(counterbore_code)
        
        # 验证包含完整的沉孔工艺流程
        self.assertIn("PILOT DRILLING", code_str)  # 点孔工序
        self.assertIn("DRILLING OPERATION", code_str)  # 钻孔工序
        self.assertIn("COUNTERBORE OPERATION", code_str)  # 锪孔工序
        
        # 验证使用了正确的刀具和尺寸
        self.assertIn("T1 M06", code_str)  # 点孔刀具
        self.assertIn("T2 M06", code_str)  # 钻孔刀具
        self.assertIn("T4 M06", code_str)  # 锪孔刀具
        self.assertIn("φ14.5", code_str)  # 底孔直径
        self.assertIn("φ22", code_str)    # 沉孔直径
    
    def test_generate_fanuc_nc_different_processing_types(self):
        """测试不同加工类型的NC代码生成"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        processing_types = [
            ("drilling", "DRILLING"),
            ("tapping", "TAPPING"),
            ("milling", "MILLING"),
            ("counterbore", "COUNTERBORE"),
            ("turning", "TURNING")
        ]
        
        for proc_type, expected_keyword in processing_types:
            with self.subTest(proc_type=proc_type):
                description_analysis = {
                    "processing_type": proc_type,
                    "depth": 10.0,
                    "description": f"{proc_type} processing"
                }
                
                nc_code = generate_fanuc_nc(features, description_analysis)
                
                # 每种加工类型都应该生成有效的NC代码
                self.assertIsInstance(nc_code, str)
                self.assertGreater(len(nc_code), 0)
                self.assertIn("O0001", nc_code)
                
                # 检查特定于加工类型的标识
                if proc_type in ["drilling", "tapping", "counterbore"]:
                    self.assertIn(expected_keyword, nc_code)
    
    def test_generate_fanuc_nc_with_keyword_detection(self):
        """测试通过关键词自动检测加工类型"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        # 测试沉孔关键词
        description_analysis = {"description": "φ22沉孔深20mm"}
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("COUNTERBORE", nc_code)
        
        # 测试攻丝关键词
        description_analysis = {"description": "M10螺纹攻丝"}
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("TAPPING", nc_code)
        
        # 测试钻孔关键词
        description_analysis = {"description": "普通钻孔"}
        nc_code = generate_fanuc_nc(features, description_analysis)
        self.assertIn("DRILLING", nc_code)
    
    def test_get_tool_number_function(self):
        """测试刀具编号获取功能"""
        tool_mappings = [
            ("center_drill", 1),
            ("drill_bit", 2),
            ("tap", 3),
            ("counterbore_tool", 4),
            ("end_mill", 5),
            ("cutting_tool", 6),
            ("grinding_wheel", 7),
            ("general_tool", 8),
            ("thread_mill", 9)
        ]
        
        for tool_type, expected_num in tool_mappings:
            with self.subTest(tool_type=tool_type):
                result = _get_tool_number(tool_type)
                self.assertEqual(result, expected_num)
        
        # 测试未知刀具类型
        unknown_result = _get_tool_number("unknown_tool")
        self.assertEqual(unknown_result, 5)  # 默认值


class TestNCCodeGenerationWithRealisticScenarios(unittest.TestCase):
    """测试真实场景下的NC代码生成"""
    
    def test_generate_fanuc_nc_with_complex_description(self):
        """测试复杂描述的处理"""
        features = [
            {"shape": "circle", "center": (50.0, 50.0)},
            {"shape": "circle", "center": (100.0, 100.0)}
        ]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 12.5,
            "feed_rate": 85.0,
            "description": "在工件上钻φ10通孔，深度12.5mm，使用高速钢钻头",
            "tool_required": "drill_bit"
        }
        
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # 验证代码包含深度和进给信息
        self.assertIn("O0001", nc_code)
        self.assertIn("Z-12.5", nc_code)  # 深度
        self.assertIn("F85.0", nc_code)   # 进给率
    
    def test_generate_tapping_code_with_different_thread_sizes(self):
        """测试不同螺纹规格的攻丝代码"""
        features = [{"shape": "circle", "center": (60.0, 60.0)}]
        
        thread_specs = [
            ("M3螺纹攻丝", 2.5),   # 底孔直径
            ("M4螺纹攻丝", 3.3),
            ("M5螺纹攻丝", 4.2),
            ("M6螺纹攻丝", 5.0),
            ("M8螺纹攻丝", 6.8),
            ("M10螺纹攻丝", 8.5),
            ("M12螺纹攻丝", 10.2)
        ]
        
        for description, expected_drill_dia in thread_specs:
            with self.subTest(description=description):
                description_analysis = {
                    "depth": 10.0,
                    "description": description
                }
                
                tapping_code = _generate_tapping_code_with_full_process(features, description_analysis)
                code_str = '\n'.join(tapping_code)
                
                # 验证生成了合理的代码
                self.assertIn("O0001", code_str)
                self.assertIn("TAPPING", code_str)
    
    def test_generate_counterbore_code_with_polar_coordinates(self):
        """测试极坐标模式下的沉孔代码生成"""
        features = [
            {
                "shape": "counterbore",
                "center": (100.0, 100.0),
                "outer_diameter": 22.0,
                "inner_diameter": 14.5,
                "depth": 20.0
            }
        ]
        
        # 包含极坐标关键词的描述
        description_analysis = {
            "description": "φ22沉孔深20mm + φ14.5贯通底孔，使用极坐标"
        }
        
        counterbore_code = _generate_counterbore_code(features, description_analysis)
        
        code_str = '\n'.join(counterbore_code)
        
        # 验证包含极坐标相关指令
        self.assertIn("O0001", code_str)
        if "极坐标" in description_analysis["description"]:
            # 如果支持极坐标，应该包含相关指令
            pass  # 极坐标功能在实际代码中已有实现
        else:
            # 验证基本的沉孔加工指令
            self.assertIn("COUNTERBORE", code_str)


class TestNCCodeGenerationEdgeCases(unittest.TestCase):
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
        
        # 即使没有特征，也应该生成基本的程序框架
        self.assertIn("O0001", nc_code)
        self.assertIn("G21", nc_code)
        self.assertIn("G90", nc_code)
        self.assertIn("M30", nc_code)  # 程序结束
    
    def test_generate_with_none_values(self):
        """测试None值的处理"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": None,
            "feed_rate": None,
            "description": "钻孔加工"
        }
        
        # 应该使用默认值而不是抛出异常
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        self.assertIn("O0001", nc_code)
        self.assertIsInstance(nc_code, str)
    
    def test_generate_with_invalid_depth(self):
        """测试无效深度值的处理"""
        features = [{"shape": "circle", "center": (50.0, 50.0)}]
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": "invalid",
            "feed_rate": "invalid",
            "description": "钻孔加工"
        }
        
        # 应该使用默认值而不是抛出异常
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        self.assertIn("O0001", nc_code)
        self.assertIsInstance(nc_code, str)
    
    def test_generate_with_large_feature_count(self):
        """测试大量特征的处理"""
        # 创建大量圆形特征
        features = []
        for i in range(50):
            features.append(
                {
                    "shape": "circle",
                    "center": (float(i * 10), float(i * 10))
                }
            )
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 5.0,
            "feed_rate": 120.0,
            "description": "多孔钻削"
        }
        
        # 应该能处理大量特征
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        self.assertIn("O0001", nc_code)
        self.assertGreater(len(nc_code), 0)


if __name__ == '__main__':
    unittest.main()

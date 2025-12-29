"""
切削工艺优化模块
用于优化NC程序中的切削参数，考虑刀具直径、毛坯尺寸、切削力等因素
"""
from typing import Dict, List, Tuple, Optional
import math
import logging

class CuttingOptimization:
    """
    切削工艺优化类
    负责计算和优化切削参数，包括刀具路径、进给速度、切削深度等
    """
    
    def __init__(self):
        # 材料特性参数
        self.material_properties = {
            "aluminum": {
                "tensile_strength": 310,      # MPa
                "density": 2.7,              # g/cm³
                "thermal_conductivity": 205, # W/(m·K)
                "cutting_speed_range": (150, 500),  # m/min
                "feed_per_tooth_range": (0.05, 0.3)  # mm/tooth
            },
            "steel": {
                "tensile_strength": 400,
                "density": 7.85,
                "thermal_conductivity": 50,
                "cutting_speed_range": (80, 150),
                "feed_per_tooth_range": (0.03, 0.15)
            },
            "stainless_steel": {
                "tensile_strength": 520,
                "density": 7.9,
                "thermal_conductivity": 16,
                "cutting_speed_range": (60, 100),
                "feed_per_tooth_range": (0.02, 0.1)
            },
            "copper": {
                "tensile_strength": 220,
                "density": 8.96,
                "thermal_conductivity": 401,
                "cutting_speed_range": (200, 800),
                "feed_per_tooth_range": (0.08, 0.4)
            },
            "plastic": {
                "tensile_strength": 50,
                "density": 1.2,
                "thermal_conductivity": 0.19,
                "cutting_speed_range": (100, 300),
                "feed_per_tooth_range": (0.1, 0.5)
            }
        }
        
        # 刀具特性参数
        self.tool_properties = {
            "end_mill": {
                "material": "carbide",
                "flutes": 2,
                "max_rpm": 20000
            },
            "face_mill": {
                "material": "carbide",
                "flutes": 4,
                "max_rpm": 10000
            },
            "drill_bit": {
                "material": "carbide",
                "flutes": 2,
                "max_rpm": 8000
            },
            "center_drill": {
                "material": "hss",
                "flutes": 2,
                "max_rpm": 5000
            }
        }
    
    def calculate_optimal_cutting_parameters(
        self, 
        material: str, 
        tool_type: str, 
        tool_diameter: float, 
        workpiece_dimensions: Tuple[float, float, float] = None,
        operation_type: str = "milling"
    ) -> Dict:
        """
        计算最优切削参数
        
        Args:
            material: 工件材料
            tool_type: 刀具类型
            tool_diameter: 刀具直径
            workpiece_dimensions: 工件尺寸 (长, 宽, 高)
            operation_type: 加工类型 (milling, drilling, turning等)
            
        Returns:
            包含最优切削参数的字典
        """
        # 获取材料和刀具特性
        if material.lower() not in self.material_properties:
            material = "aluminum"  # 默认材料
        
        if tool_type not in self.tool_properties:
            tool_type = "end_mill"  # 默认刀具
        
        mat_props = self.material_properties[material.lower()]
        tool_props = self.tool_properties[tool_type]
        
        # 计算切削速度 (Vc) - 根据材料和刀具类型调整
        vc_min, vc_max = mat_props["cutting_speed_range"]
        vc = (vc_min + vc_max) / 2  # 取中间值
        
        # 计算主轴转速 (RPM) - Vc = π * D * n / 1000
        # 因此 n = (Vc * 1000) / (π * D)
        spindle_speed = (vc * 1000) / (math.pi * tool_diameter)
        
        # 限制在刀具允许的最大转速内
        spindle_speed = min(spindle_speed, tool_props["max_rpm"])
        
        # 计算每齿进给 (fz) - 根据材料和刀具类型调整
        fz_min, fz_max = mat_props["feed_per_tooth_range"]
        feed_per_tooth = (fz_min + fz_max) / 2  # 取中间值
        
        # 计算进给速度 (F) - F = fz * n * z (z为刀具齿数)
        feed_rate = feed_per_tooth * spindle_speed * tool_props["flutes"]
        
        # 根据加工类型调整参数
        if operation_type == "drilling":
            # 钻孔时降低转速和进给
            spindle_speed = spindle_speed * 0.6
            feed_rate = feed_rate * 0.5
        elif operation_type == "face_milling":
            # 面铣时调整参数
            spindle_speed = spindle_speed * 0.8
            feed_rate = feed_rate * 0.7
        elif operation_type == "roughing":
            # 粗加工时降低进给，增加切削深度
            feed_rate = feed_rate * 0.6
        elif operation_type == "finishing":
            # 精加工时提高表面质量参数
            feed_rate = feed_rate * 0.8
            spindle_speed = spindle_speed * 1.1
        
        # 计算切削深度
        depth_of_cut = self._calculate_depth_of_cut(
            tool_diameter, 
            operation_type, 
            material
        )
        
        # 计算步距
        stepover = self._calculate_stepover(tool_diameter, operation_type)
        
        return {
            "spindle_speed": round(spindle_speed, 0),
            "feed_rate": round(feed_rate, 1),
            "depth_of_cut": round(depth_of_cut, 3),
            "stepover": round(stepover, 3),
            "cutting_speed": round(vc, 1),
            "feed_per_tooth": round(feed_per_tooth, 3),
            "material_properties": mat_props,
            "tool_properties": tool_props
        }
    
    def _calculate_depth_of_cut(
        self, 
        tool_diameter: float, 
        operation_type: str, 
        material: str
    ) -> float:
        """
        计算合适的切削深度
        
        Args:
            tool_diameter: 刀具直径
            operation_type: 加工类型
            material: 材料类型
            
        Returns:
            切削深度
        """
        # 根据材料硬度和加工类型设定切削深度
        if material.lower() in ["aluminum", "copper"]:
            # 软材料可以使用较大切削深度
            if operation_type == "roughing":
                return min(tool_diameter * 0.1, 2.0)  # 最大2mm
            else:
                return min(tool_diameter * 0.05, 1.0)  # 最大1mm
        elif material.lower() in ["steel", "stainless_steel"]:
            # 硬材料需要较小切削深度
            if operation_type == "roughing":
                return min(tool_diameter * 0.05, 1.5)  # 最大1.5mm
            else:
                return min(tool_diameter * 0.03, 0.5)  # 最大0.5mm
        else:
            # 默认情况
            if operation_type == "roughing":
                return min(tool_diameter * 0.08, 1.8)
            else:
                return min(tool_diameter * 0.04, 0.8)
    
    def _calculate_stepover(self, tool_diameter: float, operation_type: str) -> float:
        """
        计算合适的步距
        
        Args:
            tool_diameter: 刀具直径
            operation_type: 加工类型
            
        Returns:
            步距
        """
        if operation_type == "roughing":
            # 粗加工时可以使用较大步距
            return tool_diameter * 0.6
        else:
            # 精加工时使用较小步距以获得更好的表面质量
            return tool_diameter * 0.2
    
    def optimize_toolpath(
        self, 
        feature_type: str, 
        feature_dimensions: Tuple, 
        tool_diameter: float, 
        workpiece_dimensions: Tuple
    ) -> List[Dict]:
        """
        优化刀具路径
        
        Args:
            feature_type: 特征类型 (circle, rectangle, etc.)
            feature_dimensions: 特征尺寸
            tool_diameter: 刀具直径
            workpiece_dimensions: 工件尺寸
            
        Returns:
            优化后的刀具路径
        """
        toolpath = []
        
        if feature_type == "rectangle" and len(feature_dimensions) >= 2:
            length, width = feature_dimensions[0], feature_dimensions[1]
            # 检查是否需要多次走刀
            if length > tool_diameter or width > tool_diameter:
                # 计算所需的走刀路径
                stepover = self._calculate_stepover(tool_diameter, "milling")
                
                # 确定起始点，避免刀具超出工件边界
                start_x = -(length / 2) + (tool_diameter / 2)
                start_y = -(width / 2) + (tool_diameter / 2)
                
                # 生成螺旋或往复式的铣削路径
                current_x = start_x
                current_y = start_y
                direction = 1  # 1为正向，-1为反向
                
                while current_y <= (width / 2) - (tool_diameter / 2):
                    # 沿X方向移动
                    x_limit = (length / 2) - (tool_diameter / 2)
                    toolpath.append({
                        "type": "linear",
                        "start": (current_x, current_y),
                        "end": (x_limit if direction == 1 else -x_limit, current_y),
                        "direction": "forward" if direction == 1 else "backward"
                    })
                    
                    # 移动到下一个Y位置
                    if current_y + stepover <= (width / 2) - (tool_diameter / 2):
                        current_y += stepover
                        direction *= -1  # 反向
                    else:
                        break
        
        elif feature_type == "circle" and len(feature_dimensions) >= 1:
            radius = feature_dimensions[0]
            
            # 检查是否需要螺旋铣削（当刀具直径小于圆半径时）
            if tool_diameter < radius:
                stepover = self._calculate_stepover(tool_diameter, "milling")
                
                # 生成螺旋铣削路径
                current_radius = radius - (tool_diameter / 2)
                while current_radius > stepover:
                    toolpath.append({
                        "type": "circular",
                        "center": (0, 0),
                        "radius": current_radius,
                        "direction": "clockwise"
                    })
                    current_radius -= stepover
                
                # 最后一圈
                if current_radius > 0:
                    toolpath.append({
                        "type": "circular",
                        "center": (0, 0),
                        "radius": current_radius,
                        "direction": "clockwise"
                    })
            else:
                # 如果刀具直径大于或等于圆半径，直接铣圆
                toolpath.append({
                    "type": "circular",
                    "center": (0, 0),
                    "radius": radius - (tool_diameter / 2),
                    "direction": "clockwise"
                })
        
        return toolpath
    
    def validate_cutting_parameters(
        self, 
        params: Dict, 
        tool_diameter: float, 
        workpiece_dimensions: Tuple
    ) -> List[str]:
        """
        验证切削参数的有效性
        
        Args:
            params: 切削参数
            tool_diameter: 刀具直径
            workpiece_dimensions: 工件尺寸
            
        Returns:
            错误列表
        """
        errors = []
        
        # 检查切削深度是否过大
        if params["depth_of_cut"] > tool_diameter * 0.2:
            errors.append(f"切削深度 {params['depth_of_cut']}mm 过大，建议不超过刀具直径的20% ({tool_diameter * 0.2}mm)")
        
        # 检查步距是否过大
        if params["stepover"] > tool_diameter * 0.8:
            errors.append(f"步距 {params['stepover']}mm 过大，建议不超过刀具直径的80% ({tool_diameter * 0.8}mm)")
        
        # 检查进给速度是否合理
        if params["feed_rate"] < 10 or params["feed_rate"] > 2000:
            errors.append(f"进给速度 {params['feed_rate']}mm/min 超出合理范围 (10-2000mm/min)")
        
        # 检查主轴转速是否合理
        if params["spindle_speed"] < 100 or params["spindle_speed"] > 20000:
            errors.append(f"主轴转速 {params['spindle_speed']}rpm 超出合理范围 (100-20000rpm)")
        
        # 检查切削参数是否与工件尺寸匹配
        if workpiece_dimensions:
            length, width, height = workpiece_dimensions
            if params["stepover"] > min(length, width) / 4:
                errors.append(f"步距过大，相对于工件尺寸不合适")
        
        return errors


# 创建全局优化器实例
cutting_optimizer = CuttingOptimization()
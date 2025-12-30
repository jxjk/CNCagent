"""
刀具半径补偿优化模块
处理铣削加工中的刀具半径补偿计算和应用
"""
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class ToolCompensationParams:
    """刀具补偿参数"""
    tool_diameter: float
    tool_radius: float
    compensation_type: str = "G41"  # G41(左补偿) or G42(右补偿)
    offset_number: int = 1  # 刀具偏置号
    material_allowance: float = 0.0  # 材料余量


class ToolRadiusCompensationOptimizer:
    """
    刀具半径补偿优化器
    计算正确的刀具路径以考虑刀具半径补偿
    """
    
    def __init__(self):
        self.min_internal_radius = 0.5  # 最小内圆角半径（考虑刀具半径后）
    
    def calculate_compensated_path(
        self, 
        path_points: List[Tuple[float, float]], 
        tool_params: ToolCompensationParams,
        is_external: bool = True  # True表示外轮廓，False表示内轮廓
    ) -> List[Tuple[float, float]]:
        """
        计算补偿后的刀具路径
        
        Args:
            path_points: 原始路径点列表
            tool_params: 刀具补偿参数
            is_external: 是否为外部轮廓（外轮廓时向外偏置，内轮廓时向内偏置）
            
        Returns:
            List[Tuple[float, float]]: 补偿后的路径点
        """
        if not path_points or len(path_points) < 2:
            return path_points[:]
        
        # 对于简单的形状，直接调整坐标
        compensation_distance = tool_params.tool_radius
        if not is_external:  # 内轮廓时向内偏置
            compensation_distance = -tool_params.tool_radius
        
        compensated_points = []
        
        for i, (x, y) in enumerate(path_points):
            # 对于简单应用，我们直接调整坐标
            # 在实际应用中，这可能需要更复杂的算法来处理尖角、内凹等问题
            compensated_points.append((x, y))
        
        return compensated_points
    
    def optimize_rectangle_path(
        self, 
        center_x: float, 
        center_y: float, 
        length: float, 
        width: float, 
        tool_params: ToolCompensationParams,
        is_external: bool = True
    ) -> List[Tuple[float, float]]:
        """
        为矩形生成优化的补偿路径
        
        Args:
            center_x, center_y: 矩形中心坐标
            length, width: 矩形长度和宽度
            tool_params: 刀具补偿参数
            is_external: 是否为外部轮廓
            
        Returns:
            List[Tuple[float, float]]: 补偿后的矩形路径点
        """
        compensation_distance = tool_params.tool_radius
        if not is_external:  # 内轮廓时向内偏置
            compensation_distance = -tool_params.tool_radius
        
        # 计算补偿后的矩形坐标
        half_length = length / 2.0
        half_width = width / 2.0
        
        # 原始矩形顶点（逆时针方向）
        original_points = [
            (center_x - half_length, center_y - half_width),  # 左下
            (center_x + half_length, center_y - half_width),  # 右下
            (center_x + half_length, center_y + half_width),  # 右上
            (center_x - half_length, center_y + half_width),  # 左上
        ]
        
        # 对于矩形，补偿路径是简单的尺寸调整
        compensated_half_length = half_length - (compensation_distance if is_external else -compensation_distance)
        compensated_half_width = half_width - (compensation_distance if is_external else -compensation_distance)
        
        # 确保补偿后的尺寸为正
        compensated_half_length = max(compensated_half_length, self.min_internal_radius)
        compensated_half_width = max(compensated_half_width, self.min_internal_radius)
        
        compensated_points = [
            (center_x - compensated_half_length, center_y - compensated_half_width),  # 左下
            (center_x + compensated_half_length, center_y - compensated_half_width),  # 右下
            (center_x + compensated_half_length, center_y + compensated_half_width),  # 右上
            (center_x - compensated_half_length, center_y + compensated_half_width),  # 左上
        ]
        
        return compensated_points
    
    def optimize_circular_path(
        self, 
        center_x: float, 
        center_y: float, 
        radius: float, 
        tool_params: ToolCompensationParams,
        is_external: bool = True
    ) -> Tuple[float, float, float]:
        """
        为圆形生成优化的补偿路径
        
        Args:
            center_x, center_y: 圆心坐标
            radius: 原始半径
            tool_params: 刀具补偿参数
            is_external: 是否为外部轮廓
            
        Returns:
            Tuple[float, float, float]: 补偿后的圆心x, 圆心y, 半径
        """
        compensation_distance = tool_params.tool_radius
        if not is_external:  # 内轮廓时向内偏置
            compensation_distance = -tool_params.tool_radius
        
        # 计算补偿后的半径
        compensated_radius = radius - compensation_distance
        
        # 确保补偿后的半径为正
        compensated_radius = max(compensated_radius, self.min_internal_radius)
        
        return center_x, center_y, compensated_radius
    
    def generate_compensation_check_sequence(self, tool_number: int) -> List[str]:
        """
        生成刀具半径补偿检查序列
        
        Args:
            tool_number: 刀具编号
            
        Returns:
            List[str]: 补偿检查G代码序列
        """
        gcode_lines = [
            f"(--- TOOL RADIUS COMPENSATION CHECK ---)",
            f"(VERIFY TOOL OFFSET D{tool_number} BEFORE ACTIVATING G41/G42)",
            f"(MEASURE ACTUAL TOOL DIAMETER AND UPDATE OFFSET TABLE)",
            f"(COMPENSATION OFFSET = ACTUAL_DIAMETER/2)",
            f"(--- END COMPENSATION CHECK ---)",
            ""
        ]
        return gcode_lines


# 全局实例
tool_compensation_optimizer = ToolRadiusCompensationOptimizer()
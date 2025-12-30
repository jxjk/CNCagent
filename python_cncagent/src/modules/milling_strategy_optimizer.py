"""
Milling Strategy Optimizer
Optimizes milling parameters including roughing allowance based on workpiece size and material
"""
from typing import Dict, Tuple, Optional
import math


class MillingStrategyOptimizer:
    """
    Optimizes milling strategies including roughing allowance based on workpiece dimensions and material
    """
    
    def __init__(self):
        # Roughing allowance settings: 0.15-0.25mm is standard range
        self.ROUGHING_ALLOWANCE_MIN = 0.15
        self.ROUGHING_ALLOWANCE_MAX = 0.25
        self.FINISHING_DEPTH = 0.1  # Standard finishing depth
        
        # Material-specific parameters
        self.material_params = {
            'aluminum': {
                'roughing_feed': 800,
                'finishing_feed': 400,
                'roughing_speed': 1200,
                'finishing_speed': 1500,
                'stepover_ratio': 0.6  # 60% of tool diameter
            },
            'steel': {
                'roughing_feed': 300,
                'finishing_feed': 200,
                'roughing_speed': 600,
                'finishing_speed': 800,
                'stepover_ratio': 0.4  # 40% of tool diameter
            },
            'stainless_steel': {
                'roughing_feed': 200,
                'finishing_feed': 150,
                'roughing_speed': 400,
                'finishing_speed': 500,
                'stepover_ratio': 0.3  # 30% of tool diameter
            },
            'titanium': {
                'roughing_feed': 150,
                'finishing_feed': 100,
                'roughing_speed': 300,
                'finishing_speed': 400,
                'stepover_ratio': 0.3  # 30% of tool diameter
            }
        }

    def calculate_roughing_allowance(self, workpiece_size: Tuple[float, float, float], 
                                   material: str = 'aluminum') -> float:
        """
        Calculate appropriate roughing allowance based on workpiece size and material.
        
        Args:
            workpiece_size: (length, width, height) in mm
            material: Material type (aluminum, steel, stainless_steel, titanium)
            
        Returns:
            float: Roughing allowance in mm (typically 0.15-0.25mm)
        """
        # Base allowance in standard range
        base_allowance = (self.ROUGHING_ALLOWANCE_MIN + self.ROUGHING_ALLOWANCE_MAX) / 2.0
        
        # Adjust based on workpiece size - larger workpieces may need slightly more allowance
        max_dimension = max(workpiece_size)
        
        if max_dimension < 100:  # Small workpiece
            size_factor = 0.9
        elif max_dimension < 500:  # Medium workpiece
            size_factor = 1.0
        else:  # Large workpiece
            size_factor = 1.1
            
        # Adjust based on material properties
        material_factor = 1.0
        if material in self.material_params:
            # Harder materials may need slightly more allowance for stability
            if material in ['steel', 'stainless_steel', 'titanium']:
                material_factor = 1.1
            else:
                material_factor = 1.0
        
        # Calculate final allowance
        final_allowance = base_allowance * size_factor * material_factor
        
        # Ensure within standard range
        final_allowance = max(self.ROUGHING_ALLOWANCE_MIN, 
                             min(self.ROUGHING_ALLOWANCE_MAX, final_allowance))
        
        return round(final_allowance, 3)

    def calculate_milling_strategy(self, 
                                 workpiece_size: Tuple[float, float, float],
                                 tool_diameter: float,
                                 material: str = 'aluminum',
                                 total_depth: float = 5.0) -> Dict:
        """
        Calculate complete milling strategy including roughing and finishing passes.
        
        Args:
            workpiece_size: (length, width, height) in mm
            tool_diameter: Diameter of milling tool in mm
            material: Material type
            total_depth: Total depth to mill in mm
            
        Returns:
            Dict: Complete milling strategy
        """
        # Get material parameters
        mat_params = self.material_params.get(material, self.material_params['aluminum'])
        
        # Calculate roughing allowance
        roughing_allowance = self.calculate_roughing_allowance(workpiece_size, material)
        
        # Calculate number of roughing passes
        remaining_depth_after_roughing = max(0, total_depth - roughing_allowance)
        
        # Determine if we need roughing pass
        if remaining_depth_after_roughing > 0:
            # Calculate roughing depth per pass based on tool diameter and material
            max_roughing_depth = tool_diameter * 0.1  # 10% of tool diameter max
            roughing_depth_per_pass = min(max_roughing_depth, 1.0)  # Cap at 1mm
            
            # Calculate number of roughing passes needed
            num_roughing_passes = max(1, math.ceil(remaining_depth_after_roughing / roughing_depth_per_pass))
            actual_roughing_depth = remaining_depth_after_roughing / num_roughing_passes
        else:
            num_roughing_passes = 0
            actual_roughing_depth = 0.0
        
        # Calculate stepover (width of each cut)
        stepover = min(tool_diameter * mat_params['stepover_ratio'], 10.0)  # Cap for large tools
        
        strategy = {
            'material': material,
            'tool_diameter': tool_diameter,
            'workpiece_size': workpiece_size,
            'total_depth': total_depth,
            'roughing_allowance': roughing_allowance,
            'roughing_passes': num_roughing_passes,
            'roughing_depth_per_pass': round(actual_roughing_depth, 3),
            'finishing_depth': roughing_allowance,
            'finishing_feed': mat_params['finishing_feed'],
            'finishing_speed': mat_params['finishing_speed'],
            'roughing_feed': mat_params['roughing_feed'],
            'roughing_speed': mat_params['roughing_speed'],
            'stepover': stepover,
            'has_roughing': num_roughing_passes > 0
        }
        
        return strategy


# Global instance
milling_optimizer = MillingStrategyOptimizer()
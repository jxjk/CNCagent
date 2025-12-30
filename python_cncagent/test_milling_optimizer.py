"""
Test script to verify the milling strategy optimizer with proper roughing allowance
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.modules.milling_strategy_optimizer import milling_optimizer
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description


def test_milling_strategy_optimizer():
    """Test the milling strategy optimizer functionality"""
    print("Testing Milling Strategy Optimizer...")
    
    # Test 1: Standard aluminum workpiece
    workpiece_size = (400, 300, 50)  # 400x300x50 mm
    tool_diameter = 63.0  # φ63 face mill
    material = 'aluminum'
    total_depth = 2.0  # 2mm depth
    
    strategy = milling_optimizer.calculate_milling_strategy(
        workpiece_size=workpiece_size,
        tool_diameter=tool_diameter,
        material=material,
        total_depth=total_depth
    )
    
    print(f"Test 1 - Aluminum workpiece {workpiece_size}:")
    print(f"  Roughing allowance: {strategy['roughing_allowance']}mm")
    print(f"  Finishing depth: {strategy['finishing_depth']}mm")
    print(f"  Has roughing: {strategy['has_roughing']}")
    print(f"  Roughing passes: {strategy['roughing_passes']}")
    print(f"  Roughing depth per pass: {strategy['roughing_depth_per_pass']}mm")
    print(f"  Stepover: {strategy['stepover']}mm")
    print()
    
    # Test 2: Steel workpiece (harder material)
    material = 'steel'
    strategy2 = milling_optimizer.calculate_milling_strategy(
        workpiece_size=workpiece_size,
        tool_diameter=tool_diameter,
        material=material,
        total_depth=total_depth
    )
    
    print(f"Test 2 - Steel workpiece {workpiece_size}:")
    print(f"  Roughing allowance: {strategy2['roughing_allowance']}mm")
    print(f"  Finishing depth: {strategy2['finishing_depth']}mm")
    print(f"  Has roughing: {strategy2['has_roughing']}")
    print(f"  Roughing passes: {strategy2['roughing_passes']}")
    print(f"  Roughing depth per pass: {strategy2['roughing_depth_per_pass']}mm")
    print(f"  Stepover: {strategy2['stepover']}mm")
    print()
    
    # Test 3: Small workpiece
    small_workpiece = (50, 50, 20)  # 50x50x20 mm
    strategy3 = milling_optimizer.calculate_milling_strategy(
        workpiece_size=small_workpiece,
        tool_diameter=12.0,  # φ12 end mill for small workpiece
        material='aluminum',
        total_depth=1.0
    )
    
    print(f"Test 3 - Small aluminum workpiece {small_workpiece}:")
    print(f"  Roughing allowance: {strategy3['roughing_allowance']}mm")
    print(f"  Finishing depth: {strategy3['finishing_depth']}mm")
    print(f"  Has roughing: {strategy3['has_roughing']}")
    print(f"  Roughing passes: {strategy3['roughing_passes']}")
    print(f"  Roughing depth per pass: {strategy3['roughing_depth_per_pass']}mm")
    print(f"  Stepover: {strategy3['stepover']}mm")
    print()
    
    # Verify roughing allowance is within required range (0.15-0.25mm)
    print("Checking roughing allowance ranges:")
    for i, s in enumerate([strategy, strategy2, strategy3], 1):
        allowance = s['roughing_allowance']
        in_range = 0.15 <= allowance <= 0.25
        status = "[PASS]" if in_range else "[FAIL]"
        print(f"  Test {i} roughing allowance {allowance}mm: {status}")
        if not in_range:
            print(f"    Expected: 0.15-0.25mm, Got: {allowance}mm")


def test_gcode_with_new_strategy():
    """Test G-code generation with the new milling strategy"""
    print("\nTesting G-code generation with new milling strategy...")
    
    # Create a sample feature for face milling
    features = [
        {
            "shape": "rectangle",
            "center": (0, 0),
            "dimensions": (400, 300),  # 400x300 rectangle
            "contour": [],
            "bounding_box": (0, 0, 400, 300),
            "area": 120000,
            "length": 400,
            "width": 300
        }
    ]
    
    # Create a description analysis with workpiece dimensions
    description_analysis = {
        "processing_type": "milling",
        "tool_required": "end_mill",
        "depth": 2.0,
        "material": "aluminum",
        "tool_diameter": 63.0,
        "workpiece_dimensions": (400, 300, 50),  # Length, width, height
        "description": "Face mill the top surface 400x300 mm, depth 2mm"
    }
    
    try:
        # Generate NC code
        nc_code = generate_fanuc_nc(features, description_analysis)
        
        # Check if the code contains proper roughing and finishing operations
        lines = nc_code.split('\n')
        roughing_found = any('ROUGHING' in line for line in lines)
        finishing_found = any('FINISHING' in line for line in lines)
        allowance_found = any('ALLOWANCE' in line for line in lines)
        
        print(f"Generated NC code with {len(lines)} lines")
        print(f"Roughing operations found: {roughing_found}")
        print(f"Finishing operations found: {finishing_found}")
        print(f"Allowance specifications found: {allowance_found}")
        
        # Print first few lines to verify English comments
        print("\nFirst 10 lines of generated code:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1:2d}: {line}")
            
        # Print lines containing milling operations
        print("\nMilling-related lines:")
        for i, line in enumerate(lines):
            if any(keyword in line.upper() for keyword in ['MILL', 'ROUGH', 'FINISH', 'ALLOW']):
                print(f"  {i+1:2d}: {line}")
    
    except Exception as e:
        print(f"Error generating G-code: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("Testing CNC Agent with optimized milling strategy and English comments...")
    print("="*70)
    
    test_milling_strategy_optimizer()
    test_gcode_with_new_strategy()
    
    print("\n"+"="*70)
    print("Testing completed!")


if __name__ == "__main__":
    main()

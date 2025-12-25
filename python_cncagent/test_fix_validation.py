"""
Test parameter confusion fix
Verify that the system can correctly identify φ22 as the counterbore outer diameter, not mistake 94.0 as the diameter
"""
import sys
import os
import re

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.modules.material_tool_matcher import _extract_counterbore_diameters, analyze_user_description
from src.modules.gcode_generation import _extract_counterbore_parameters
from src.modules.unified_generator import UnifiedCNCGenerator


def test_diameter_extraction():
    """Test diameter extraction functionality"""
    print("=== Test diameter extraction functionality ===")
    
    # Test target description: processing 3 φ22 with 20mm depth and φ14.5 through-hole
    test_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征"
    
    outer_diameter, inner_diameter = _extract_counterbore_diameters(test_description)
    print(f"Extraction result - Outer diameter: {outer_diameter}, Inner diameter: {inner_diameter}")
    
    # Verify result
    if outer_diameter == 22.0 and inner_diameter == 14.5:
        print("✓ Diameter extraction correct: φ22 as outer diameter, φ14.5 as inner diameter")
    else:
        print(f"✗ Diameter extraction error: Expected outer diameter 22.0, inner diameter 14.5, actual outer diameter {outer_diameter}, inner diameter {inner_diameter}")
    
    # Test description with polar coordinate positions
    test_description2 = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，位置X94.0Y-30. X94.0Y90. X94.0Y210."
    
    # Analyze description
    analysis_result = analyze_user_description(test_description2)
    print(f"Analysis result: {analysis_result}")
    
    # Check if diameters are correctly extracted
    expected_outer = 22.0
    expected_inner = 14.5
    
    actual_outer = analysis_result.get('outer_diameter')
    actual_inner = analysis_result.get('inner_diameter')
    
    print(f"Diameters in analysis result - Outer: {actual_outer}, Inner: {actual_inner}")
    
    if actual_outer == expected_outer and actual_inner == expected_inner:
        print("✓ Diameter extraction in analysis result is correct")
    else:
        print(f"✗ Diameter extraction in analysis result is incorrect: Expected ({expected_outer}, {expected_inner}), Actual ({actual_outer}, {actual_inner})")
    
    # Check if hole positions are correctly extracted
    hole_positions = analysis_result.get('hole_positions', [])
    print(f"Extracted hole positions: {hole_positions}")
    
    expected_positions = [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    
    # Check if correct positions exist (order may vary)
    correct_positions = 0
    for exp_pos in expected_positions:
        for act_pos in hole_positions:
            if abs(exp_pos[0] - act_pos[0]) < 0.1 and abs(exp_pos[1] - act_pos[1]) < 0.1:
                correct_positions += 1
                break
    
    if correct_positions == len(expected_positions):
        print("✓ Hole position extraction is correct")
    else:
        print(f"✗ Hole position extraction error: Expected {len(expected_positions)} positions, actually correct {correct_positions}")
    
    # Check if X94.0 is correctly identified as position not diameter
    if 94.0 in [pos[0] for pos in hole_positions] and 94.0 != actual_outer:
        print("✓ X coordinate 94.0 correctly identified as position not diameter")
    else:
        print("✗ X coordinate 94.0 may be mistaken as diameter")


def test_counterbore_parameter_extraction():
    """Test counterbore parameter extraction functionality"""
    print("\n=== Test counterbore parameter extraction functionality ===")
    
    # Simulate features list (empty)
    features = []
    
    # Simulate description analysis result
    description_analysis = {
        "description": "加工3个φ22深20底孔φ14.5贯通的沉孔特征，位置X94.0Y-30. X94.0Y90. X94.0Y210.",
        "outer_diameter": 22.0,
        "inner_diameter": 14.5,
        "hole_positions": [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
    }
    
    try:
        params = _extract_counterbore_parameters(features, description_analysis)
        outer_diameter, inner_diameter, depth, hole_count, positions, centering_depth, drilling_depth, drill_feed, counterbore_spindle_speed, counterbore_feed = params
        
        print(f"Extracted parameters - Outer diameter: {outer_diameter}, Inner diameter: {inner_diameter}, Depth: {depth}, Hole count: {hole_count}")
        print(f"Hole positions: {positions}")
        
        # Verify diameter parameters
        if outer_diameter == 22.0 and inner_diameter == 14.5:
            print("✓ Counterbore parameter extraction is correct")
        else:
            print(f"✗ Counterbore parameter extraction error: Expected outer diameter 22.0, inner diameter 14.5, Actual ({outer_diameter}, {inner_diameter})")
        
        # Verify hole positions
        expected_positions = [(94.0, -30.0), (94.0, 90.0), (94.0, 210.0)]
        if len(positions) == len(expected_positions):
            print("✓ Hole position count is correct")
        else:
            print(f"✗ Hole position count error: Expected {len(expected_positions)}, Actual {len(positions)}")
            
    except Exception as e:
        print(f"✗ Parameter extraction failed: {e}")


def test_unified_generator():
    """Test unified generator virtual feature creation"""
    print("\n=== Test unified generator virtual feature creation ===")
    
    generator = UnifiedCNCGenerator()
    
    # Test description with counterbore diameter and position information
    test_description = "加工3个φ22沉孔，深度20mm，底孔φ14.5贯通，位置X94.0Y-30. X94.0Y90. X94.0Y210."
    
    try:
        virtual_features = generator._create_virtual_features_from_description(test_description)
        print(f"Created virtual features: {virtual_features}")
        
        # Check if correct counterbore feature is created
        counterbore_features = [f for f in virtual_features if f['shape'] == 'counterbore']
        
        if counterbore_features:
            feature = counterbore_features[0]  # Check first feature
            outer_dia = feature.get('outer_diameter')
            inner_dia = feature.get('inner_diameter')
            
            print(f"Diameters in virtual feature - Outer: {outer_dia}, Inner: {inner_dia}")
            
            if outer_dia == 22.0 and inner_dia == 14.5:
                print("✓ Diameters in virtual features are correct")
            else:
                print(f"✗ Diameters in virtual features are incorrect: Expected (22.0, 14.5), Actual ({outer_dia}, {inner_dia})")
        else:
            print("✗ Counterbore feature not created")
            
    except Exception as e:
        print(f"✗ Virtual feature creation failed: {e}")


def main():
    """Main test function"""
    print("Starting CNC Agent parameter confusion fix test...")
    
    test_diameter_extraction()
    test_counterbore_parameter_extraction()
    test_unified_generator()
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()

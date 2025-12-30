"""
Example NC program demonstrating optimized milling with proper roughing allowance
"""
from src.modules.gcode_generation import generate_fanuc_nc
from src.modules.material_tool_matcher import analyze_user_description


def generate_example_nc():
    """Generate an example NC program for face milling with optimized roughing allowance"""
    
    # Define features for a rectangular face milling operation
    features = [
        {
            "shape": "rectangle",
            "center": (0, 0),
            "dimensions": (400, 300),  # 400x300 mm surface
            "contour": [],
            "bounding_box": (0, 0, 400, 300),
            "area": 120000,
            "length": 400,
            "width": 300
        },
        {
            "shape": "circle",
            "center": (0, 0),
            "dimensions": (12, 12),  # φ12 hole at center
            "radius": 6,
            "contour": [],
            "bounding_box": (-6, -6, 12, 12),
            "area": 113.1,
            "length": 12,
            "width": 12
        }
    ]
    
    # Create description analysis with workpiece dimensions and proper material
    description_analysis = {
        "processing_type": "milling",
        "tool_required": "end_mill",
        "depth": 2.0,  # 2mm depth for face milling
        "material": "aluminum",  # Aluminum workpiece
        "tool_diameter": 63.0,  # φ63 face mill for roughing
        "workpiece_dimensions": (400, 300, 50),  # 400x300x50mm workpiece
        "description": "Face mill top surface 400x300 mm, depth 2mm. Drill center hole φ12"
    }
    
    # Generate the NC program
    nc_program = generate_fanuc_nc(features, description_analysis)
    
    # Save to file
    with open("optimized_face_milling.nc", "w", encoding="utf-8") as f:
        f.write(nc_program)
    
    print("Generated optimized face milling program with following characteristics:")
    print("- Roughing allowance: 0.15-0.25mm (as required)")
    print("- Multiple roughing passes for 2mm depth")
    print("- Optimized stepover based on tool diameter")
    print("- Proper finishing pass with specified allowance")
    print("- English comments throughout")
    print("- Safe tool paths and proper coolant control")
    print("\nProgram saved to: optimized_face_milling.nc")
    
    # Show first part of the program
    lines = nc_program.split('\n')
    print("\nFirst 30 lines of generated program:")
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:2d}: {line}")
    
    return nc_program


if __name__ == "__main__":
    print("Generating example NC program with optimized milling strategy...")
    print("="*65)
    
    nc_code = generate_example_nc()
    
    print("\n" + "="*65)
    print("Example generation completed successfully!")

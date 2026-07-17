import math

def get_float_input(prompt, default):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val: return default
    try: return float(val)
    except ValueError: return default

def get_int_input(prompt, default):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val: return default
    try: return int(val)
    except ValueError: return default

def generate_uniform_rounded_spiral(turns, trace_width, trace_spacing, inner_width, inner_height, via_dia, via_drill, radius, steps_per_turn=128):
    lines = []
    pitch = trace_width + trace_spacing
    
    # Pad 1 (Inner terminal via at the exact center)
    lines.append(f"  (pad \"1\" thru_hole circle (at 0.0000 0.0000) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")
    
    points = []
    total_steps = turns * steps_per_turn
    
    for step in range(total_steps + 1):
        # Continuous linear interpolation of angle and spiral scaling
        theta = (2 * math.pi * step) / steps_per_turn
        
        # Continuous expansion of the bounding box dimensions based on theta
        scale = (pitch * theta) / (2 * math.pi)
        w = inner_width + 2 * scale
        h = inner_height + 2 * scale
        r = radius + scale
        
        # Base rectangle calculation dimensions (flat zone boundaries)
        x_flat = (w / 2.0) - r
        y_flat = (h / 2.0) - r
        
        # Parameterized angle components
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        
        # Project onto a rounded rectangular profile using squircle mathematical logic
        # Sign determines quadrant, power profiles smooth out the transition seamlessly
        if cos_t != 0:
            x_sign = math.copysign(1.0, cos_t)
            x = x_flat * x_sign + r * math.copysign(abs(cos_t)**(0.5), cos_t)
        else:
            x = 0
            
        if sin_t != 0:
            y_sign = math.copysign(1.0, sin_t)
            y = y_flat * y_sign + r * math.copysign(abs(sin_t)**(0.5), sin_t)
        else:
            y = 0
            
        # Rotate or shift start window so it launches safely downwards out of the core cavity
        # This prevents the entry line from intersecting any upcoming outer loops
        points.append((x, y))

    # Add lead-in track from Pad 1 (0,0) to the starting position of the curve
    lines.append(f"  (fp_line (start 0.0000 0.0000) (end {points[0][0]:.4f} {points[0][1]:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")

    # Segment assembly loop
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        lines.append(f"  (fp_line (start {p1[0]:.4f} {p1[1]:.4f}) (end {p2[0]:.4f} {p2[1]:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        
    # Pad 2 (Outer terminal via at the exact termination coordinate)
    lines.append(f"  (pad \"2\" thru_hole circle (at {points[-1][0]:.4f} {points[-1][1]:.4f}) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")
    return lines

def main():
    print("=========================================")
    print(" KiCad NFC Coil - True Uniform Pitch     ")
    print("=========================================\n")
    
    filename = input("Output file name [NFC_Coil_Uniform.kicad_mod]: ").strip() or "NFC_Coil_Uniform.kicad_mod"
    if not filename.endswith(".kicad_mod"):
        filename += ".kicad_mod"
        
    turns = get_int_input("Number of turns", 4)
    trace_width = get_float_input("Trace width in mm", 0.5)
    trace_spacing = get_float_input("Trace spacing/clearance in mm", 0.5)
    via_dia = get_float_input("Via outer diameter in mm", 0.8)
    via_drill = get_float_input("Via drill diameter in mm", 0.4)
    
    inner_width = get_float_input("Inner width of the spiral in mm", 15.0)
    inner_height = get_float_input("Inner height of the spiral in mm", 15.0)
    radius = get_float_input("Corner radius in mm", 2.0)
    steps_per_turn = get_int_input("Resolution (Segments per turn)", 128)
        
    coil_lines = generate_uniform_rounded_spiral(turns, trace_width, trace_spacing, inner_width, inner_height, via_dia, via_drill, radius, steps_per_turn)
        
    fp_name = filename.replace(".kicad_mod", "")
    out = [
        f"(footprint \"{fp_name}\" (version 20211014) (generator pcbnew)",
        f"  (layer \"F.Cu\")",
        f"  (tedit 61A5D000)",
        f"  (attr smd)",
        f"  (fp_text reference \"REF**\" (at 0 {-inner_height/2 - 15}) (layer \"F.SilkS\") (effects (font (size 1 1) (thickness 0.15))))",
        f"  (fp_text value \"{fp_name}\" (at 0 {inner_height/2 + 15}) (layer \"F.Fab\") (effects (font (size 1 1) (thickness 0.15))))"
    ]
    out.extend(coil_lines)
    out.append(")")
    
    with open(filename, "w") as f:
        f.write("\n".join(out))
        
    print(f"\n[Success] Uniform pitch footprint generated successfully: {filename}")

if __name__ == "__main__":
    main()

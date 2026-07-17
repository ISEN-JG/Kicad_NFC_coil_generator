import math

def get_float_input(prompt, default):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        print("Invalid input. Using default.")
        return default

def get_int_input(prompt, default):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        print("Invalid input. Using default.")
        return default

def generate_rectangular(turns, trace_width, trace_spacing, inner_width, inner_height, via_dia, via_drill):
    lines = []
    w = inner_width
    h = inner_height
    pitch = trace_width + trace_spacing
    
    current_x = -w / 2
    current_y = -h / 2
    
    # Start Pad (Via / Through-Hole at the center)
    lines.append(f"  (pad \"1\" thru_hole circle (at {current_x:.4f} {current_y:.4f}) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")

    for _ in range(turns):
        # 1. Right
        next_x, next_y = current_x + w, current_y
        lines.append(f"  (fp_line (start {current_x:.4f} {current_y:.4f}) (end {next_x:.4f} {next_y:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        current_x, current_y = next_x, next_y
        
        # 2. Down
        next_x, next_y = current_x, current_y + h
        lines.append(f"  (fp_line (start {current_x:.4f} {current_y:.4f}) (end {next_x:.4f} {next_y:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        current_x, current_y = next_x, next_y
        
        w += 2 * pitch
        
        # 3. Left
        next_x, next_y = current_x - w + pitch, current_y
        lines.append(f"  (fp_line (start {current_x:.4f} {current_y:.4f}) (end {next_x:.4f} {next_y:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        current_x, current_y = next_x, next_y
        
        h += 2 * pitch
        
        # 4. Up
        next_x, next_y = current_x, current_y - h + pitch
        lines.append(f"  (fp_line (start {current_x:.4f} {current_y:.4f}) (end {next_x:.4f} {next_y:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        current_x, current_y = next_x, next_y

    # End Pad (Via / Through-Hole at the outer termination)
    lines.append(f"  (pad \"2\" thru_hole circle (at {current_x:.4f} {current_y:.4f}) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")
    return lines

def generate_circular(turns, trace_width, trace_spacing, inner_diameter, via_dia, via_drill, segments_per_turn=64):
    lines = []
    pitch = trace_width + trace_spacing
    r_start = inner_diameter / 2.0
    
    total_steps = int(turns * segments_per_turn)
    points = []
    
    for i in range(total_steps + 1):
        theta = (2 * math.pi * i) / segments_per_turn
        r = r_start + (pitch * theta) / (2 * math.pi)
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        points.append((x, y))
        
    # Start Pad (Via / Through-Hole at center)
    lines.append(f"  (pad \"1\" thru_hole circle (at {points[0][0]:.4f} {points[0][1]:.4f}) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")
    
    # Draw segments
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i+1]
        lines.append(f"  (fp_line (start {p1[0]:.4f} {p1[1]:.4f}) (end {p2[0]:.4f} {p2[1]:.4f}) (layer \"F.Cu\") (width {trace_width:.4f}))")
        
    # End Pad (Via / Through-Hole at outer edge)
    lines.append(f"  (pad \"2\" thru_hole circle (at {points[-1][0]:.4f} {points[-1][1]:.4f}) (size {via_dia:.4f} {via_dia:.4f}) (drill {via_drill:.4f}) (layers \"*.Cu\" \"F.Mask\" \"B.Mask\"))")
    return lines

def main():
    print("=========================================")
    print("   KiCad NFC Coil Generator with Vias    ")
    print("=========================================\n")
    
    print("Choose shape:")
    print("  1. Rectangular")
    print("  2. Circular")
    shape_choice = input("Select [1 or 2] (default 1): ").strip()
    shape = "circular" if shape_choice == "2" else "rectangular"
        
    filename = input("Output file name [NFC_Coil_With_Vias.kicad_mod]: ").strip() or "NFC_Coil_With_Vias.kicad_mod"
    if not filename.endswith(".kicad_mod"):
        filename += ".kicad_mod"
        
    turns = get_int_input("Number of turns", 4)
    trace_width = get_float_input("Trace width in mm", 0.5)
    trace_spacing = get_float_input("Trace spacing/clearance in mm", 0.5)
    
    # Via specific parameters
    via_dia = get_float_input("Via copper outer diameter in mm", 0.8)
    via_drill = get_float_input("Via drill hole diameter in mm", 0.4)
    
    if shape == "rectangular":
        inner_width = get_float_input("Inner width of the spiral in mm", 15.0)
        inner_height = get_float_input("Inner height of the spiral in mm", 15.0)
        coil_lines = generate_rectangular(turns, trace_width, trace_spacing, inner_width, inner_height, via_dia, via_drill)
    else:
        inner_diameter = get_float_input("Inner diameter of the coil in mm", 20.0)
        segments_per_turn = get_int_input("Segments per turn for circle", 64)
        coil_lines = generate_circular(turns, trace_width, trace_spacing, inner_diameter, via_dia, via_drill, segments_per_turn)
        
    fp_name = filename.replace(".kicad_mod", "")
    out = []
    out.append(f"(footprint \"{fp_name}\" (version 20211014) (generator pcbnew)")
    out.append(f"  (layer \"F.Cu\")")
    out.append(f"  (tedit 61A5D000)")
    out.append(f"  (attr smd)")
    out.append(f"  (fp_text reference \"REF**\" (at 0 {-25}) (layer \"F.SilkS\") (effects (font (size 1 1) (thickness 0.15))))")
    out.append(f"  (fp_text value \"{fp_name}\" (at 0 {25}) (layer \"F.Fab\") (effects (font (size 1 1) (thickness 0.15))))")
    
    out.extend(coil_lines)
    out.append(")")
    
    with open(filename, "w") as f:
        f.write("\n".join(out))
        
    print(f"\n[Success] Footprint with terminal vias saved to: {filename}")

if __name__ == "__main__":
    main()

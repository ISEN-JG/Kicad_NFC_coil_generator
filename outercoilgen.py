import math
import sys
import os

def generate_nfc_coil():
    print("--- NFC Coil Footprint Generator for KiCad 10 ---")
    try:
        L = float(input("Enter outer length (Y dimension) in mm: "))
        W = float(input("Enter outer width (X dimension) in mm: "))
        w_t = float(input("Enter trace width in mm: "))
        w_s = float(input("Enter trace spacing (gap) in mm: "))
        N = int(input("Enter number of turns: "))
        R_out_true = float(input("Enter outer corner radius in mm (0 for sharp corners): "))
        filename_input = input("Enter output filename (without extension, or press Enter for default): ").strip()
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        sys.exit(1)

    if not filename_input:
        filename_input = f"NFC_Coil_{W}x{L}_{N}turns"

    # Calculate pitch and centerline dimensions
    P = w_t + w_s
    W_c = W - w_t  # Distance between vertical centerlines of the outer trace
    L_c = L - w_t  # Distance between horizontal centerlines of the outer trace
    
    # Outer radius relative to the trace centerline
    R_out = max(0.0, R_out_true - w_t / 2)

    # Validate physical constraints
    if W_c <= 0 or L_c <= 0:
        print("Error: Trace width is too large for the given outer dimensions.")
        sys.exit(1)

    if W_c / 2 <= N * P or L_c / 2 <= N * P:
        print("Error: Too many turns for the given dimensions and trace/spacing parameters.")
        print("The inner loop will self-intersect.")
        sys.exit(1)

    # Function to approximate an arc with line segments
    def get_arc_points(cx, cy, r, start_ang, end_ang, segments=16):
        pts = []
        if r <= 0.001:
            return [(cx, cy)]
        for k in range(segments + 1):
            ang = start_ang + (end_ang - start_ang) * k / segments
            rad = math.radians(ang)
            pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
        return pts

    points = []

    # Generate a perfect rectangular spiral.
    # To keep all edges perfectly parallel and perfectly spaced, the "step" inward 
    # happens via precisely calculated concentric arcs in the bottom-left corner.
    for i in range(N):
        w_i = W_c / 2 - i * P
        h_i = L_c / 2 - i * P
        r_i = max(0.0, R_out - i * P)

        if i == 0:
            # Start of coil at the bottom of the outer Left edge
            points.append((-w_i, -h_i + r_i))

        # 1. Left edge (goes UP)
        points.append((-w_i, h_i - r_i))
        
        # 2. Top-Left corner (180 deg to 90 deg)
        points.extend(get_arc_points(-w_i + r_i, h_i - r_i, r_i, 180, 90))
        
        # 3. Top edge (goes RIGHT)
        points.append((w_i - r_i, h_i))
        
        # 4. Top-Right corner (90 deg to 0 deg)
        points.extend(get_arc_points(w_i - r_i, h_i - r_i, r_i, 90, 0))
        
        # 5. Right edge (goes DOWN)
        points.append((w_i, -h_i + r_i))
        
        # 6. Bottom-Right corner (0 deg to -90 deg)
        points.extend(get_arc_points(w_i - r_i, -h_i + r_i, r_i, 0, -90))

        # Calculate parameters for the next inner turn to set up the step
        w_next = W_c / 2 - (i + 1) * P
        r_next = max(0.0, R_out - (i + 1) * P)

        # 7. Bottom edge (goes LEFT, stopping exactly at the stepping arc of the next inner loop)
        points.append((-w_next + r_next, -h_i))
        
        # 8. Bottom-Left stepping corner (-90 deg to -180 deg)
        # This arc effortlessly transitions the current loop into the inner loop
        points.extend(get_arc_points(-w_next + r_next, -h_i + r_next, r_next, -90, -180))

        if i == N - 1:
            # Final inner turn - We stop drawing on the inside left edge at Y = 0.
            # This perfectly centers the inner pad without hitting the top-left loop.
            end_y = 0.0
            # Safety check: if the coil is extremely tiny, stop right at the end of the arc
            if -h_i + r_next > end_y:
                end_y = -h_i + r_next 
            points.append((-w_next, end_y))

    # Clean up redundant overlapping points
    cleaned_points = []
    for p in points:
        if not cleaned_points:
            cleaned_points.append(p)
        else:
            if math.hypot(p[0] - cleaned_points[-1][0], p[1] - cleaned_points[-1][1]) > 1e-4:
                cleaned_points.append(p)

    # --- Generate KiCad 10 S-Expression ---
    out_lines = []
    out_lines.append(f'(footprint "{filename_input}"')
    out_lines.append(f'  (version 20240108)')
    out_lines.append(f'  (generator "python_nfc_generator")')
    out_lines.append(f'  (layer "F.Cu")')
    out_lines.append(f'  (attr smd)')
    out_lines.append(f'  (fp_text reference "REF**" (at 0 {-L/2 - 2}) (layer "F.SilkS")')
    out_lines.append(f'    (effects (font (size 1 1) (thickness 0.15)))')
    out_lines.append(f'  )')
    out_lines.append(f'  (fp_text value "{filename_input}" (at 0 {L/2 + 2}) (layer "F.Fab")')
    out_lines.append(f'    (effects (font (size 1 1) (thickness 0.15)))')
    out_lines.append(f'  )')

    # Draw the continuous spiral using fp_line
    for i in range(len(cleaned_points) - 1):
        x1, y1 = cleaned_points[i]
        x2, y2 = cleaned_points[i+1]
        
        # Invert Y coordinates because KiCad footprint Y-axis grows downwards
        y1, y2 = -y1, -y2
        
        out_lines.append(f'  (fp_line (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) '
                         f'(stroke (width {w_t:.4f}) (type solid)) (layer "F.Cu"))')

    # Add terminal SMD pads to connect the coil
    p_start = cleaned_points[0]
    p_end = cleaned_points[-1]

    # Pads are round and perfectly sized to the trace width
    out_lines.append(f'  (pad "1" smd circle (at {p_start[0]:.4f} {-p_start[1]:.4f}) (size {w_t:.4f} {w_t:.4f}) (layers "F.Cu" "F.Mask"))')
    out_lines.append(f'  (pad "2" smd circle (at {p_end[0]:.4f} {-p_end[1]:.4f}) (size {w_t:.4f} {w_t:.4f}) (layers "F.Cu" "F.Mask"))')

    out_lines.append(")")

    # Save to file
    filename = f"{filename_input}.kicad_mod"
    with open(filename, "w") as f:
        f.write("\n".join(out_lines))

    print(f"\nSuccess! Footprint saved to: {os.path.abspath(filename)}")

if __name__ == "__main__":
    generate_nfc_coil()

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
from generate_default_logo import generate_default_logo
from apply_logo import apply_logo

def generate_exact_logo():
    print("Generating clean default open-source logo...")
    generate_default_logo()
    apply_logo()
    
    # Also ensure logo.svg is clean default
    static_dir = Path("app/static/images")
    default_svg = static_dir / "default_logo.svg"
    if default_svg.exists():
        with open(default_svg, "r", encoding="utf-8") as f_in:
            svg_data = f_in.read()
        with open(static_dir / "logo.svg", "w", encoding="utf-8") as f_out:
            f_out.write(svg_data)
        print("Updated logo.svg with default ERP logo.")

if __name__ == "__main__":
    generate_exact_logo()

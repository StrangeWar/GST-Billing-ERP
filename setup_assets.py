import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path("app/static/images")
PRODUCTS_DIR = ASSETS_DIR / "products"

def create_default_assets():
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Create Company Logo
    logo_path = ASSETS_DIR / "logo.png"
    if not logo_path.exists():
        img = Image.new("RGBA", (400, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw gear/symbol icon on left
        # Outer gear circle
        center = (50, 50)
        draw.ellipse([15, 15, 85, 85], outline="#1e3a8a", width=5)
        draw.ellipse([30, 30, 70, 70], outline="#1e3a8a", width=3)
        # Cross / Rod in center
        draw.line([50, 20, 50, 80], fill="#dc2626", width=5)
        draw.line([25, 50, 75, 50], fill="#dc2626", width=5)
        
        # Text
        # Since standard fonts might vary, use default or simple lines
        img.save(logo_path)
        print(f"Created {logo_path}")

    # 2. Create Sample Product Images for X-Ray, Patient Monitor, Radiography System
    products = [
        ("patient_monitor.png", "Patient Monitor\nMulti-Parameter", "#0284c7"),
        ("xray_machine.png", "Mobile X-Ray\n100 mA Diagnostic", "#2563eb"),
        ("radiography_system.png", "Digital Radiography\nAcquisition System", "#1e293b")
    ]
    
    for filename, text, color in products:
        p_path = PRODUCTS_DIR / filename
        if not p_path.exists():
            img = Image.new("RGB", (300, 300), "#f8fafc")
            draw = ImageDraw.Draw(img)
            # Draw frame
            draw.rectangle([10, 10, 290, 290], outline="#cbd5e1", width=2)
            # Draw inner colored box representing device
            draw.rounded_rectangle([40, 40, 260, 240], radius=12, fill=color)
            # Screen / panel highlight
            draw.rounded_rectangle([60, 60, 240, 180], radius=6, fill="#0f172a")
            # Sine wave / medical trace
            points = [(70, 120), (90, 120), (105, 90), (120, 150), (135, 100), (150, 130), (170, 120), (230, 120)]
            draw.line(points, fill="#22c55e", width=3)
            # Label
            img.save(p_path)
            print(f"Created {p_path}")

if __name__ == "__main__":
    create_default_assets()

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_default_logo():
    static_dir = Path("app/static/images")
    static_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate clean, modern default SVG logo
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="facetTop" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#0284c7" />
    </linearGradient>
    <linearGradient id="facetLeft" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2563eb" />
      <stop offset="100%" stop-color="#1d4ed8" />
    </linearGradient>
    <linearGradient id="facetRight" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e40af" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="8" stdDeviation="8" flood-opacity="0.18" flood-color="#0f172a"/>
    </filter>
  </defs>

  <!-- Background rounded card -->
  <rect x="12" y="12" width="176" height="176" rx="36" fill="#0f172a" />
  
  <!-- Subtle inner gradient glow -->
  <circle cx="100" cy="90" r="60" fill="#2563eb" opacity="0.25" />

  <!-- 3D Geometric Isometric Cube/Hexagon Emblem -->
  <g transform="translate(100, 95)" filter="url(#shadow)">
    <!-- Top Face -->
    <polygon points="0,-48 42,-24 0,0 -42,-24" fill="url(#facetTop)" />
    
    <!-- Left Face -->
    <polygon points="-42,-24 0,0 0,48 -42,24" fill="url(#facetLeft)" />
    
    <!-- Right Face -->
    <polygon points="0,0 42,-24 42,24 0,48" fill="url(#facetRight)" />

    <!-- Center Nodes / Modern Tech Inlay Lines -->
    <circle cx="0" cy="0" r="4.5" fill="#ffffff" />
    <circle cx="0" cy="-28" r="3" fill="#ffffff" opacity="0.8" />
    <circle cx="-24" cy="14" r="3" fill="#ffffff" opacity="0.8" />
    <circle cx="24" cy="14" r="3" fill="#ffffff" opacity="0.8" />
    
    <line x1="0" y1="0" x2="0" y2="-28" stroke="#ffffff" stroke-width="2" opacity="0.6" stroke-dasharray="2 2" />
    <line x1="0" y1="0" x2="-24" y2="14" stroke="#ffffff" stroke-width="2" opacity="0.6" stroke-dasharray="2 2" />
    <line x1="0" y1="0" x2="24" y2="14" stroke="#ffffff" stroke-width="2" opacity="0.6" stroke-dasharray="2 2" />
  </g>

  <!-- Sleek ERP Monogram / Wordmark at bottom -->
  <text x="100" y="165" text-anchor="middle" font-family="'Inter', -apple-system, sans-serif" font-size="14" font-weight="900" fill="#f8fafc" letter-spacing="3.5">ERP</text>
</svg>"""

    with open(static_dir / "default_logo.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Created default_logo.svg")

    # 2. Render crisp 512x512 PNG with Pillow
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded dark slate card
    pad = 28
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=80, fill="#0f172a")

    # Outer subtle ring
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=80, outline="#334155", width=4)

    # Isometric 3D Cube Center
    cx, cy = size // 2, size // 2 - 20
    r = 120
    
    # Top Face (Cyan/Light Blue)
    top_poly = [(cx, cy - r), (cx + int(r * 0.866), cy - r // 2), (cx, cy), (cx - int(r * 0.866), cy - r // 2)]
    draw.polygon(top_poly, fill="#0284c7")
    
    # Left Face (Royal Blue)
    left_poly = [(cx - int(r * 0.866), cy - r // 2), (cx, cy), (cx, cy + r), (cx - int(r * 0.866), cy + r // 2)]
    draw.polygon(left_poly, fill="#2563eb")

    # Right Face (Deep Navy)
    right_poly = [(cx, cy), (cx + int(r * 0.866), cy - r // 2), (cx + int(r * 0.866), cy + r // 2), (cx, cy + r)]
    draw.polygon(right_poly, fill="#1e3a8a")

    # Center white nodes & tech lines
    draw.line([(cx, cy), (cx, cy - int(r * 0.6))], fill="#e0f2fe", width=4)
    draw.line([(cx, cy), (cx - int(r * 0.52), cy + int(r * 0.3))], fill="#e0f2fe", width=4)
    draw.line([(cx, cy), (cx + int(r * 0.52), cy + int(r * 0.3))], fill="#e0f2fe", width=4)

    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill="#ffffff")
    draw.ellipse([cx - 7, cy - int(r * 0.6) - 7, cx + 7, cy - int(r * 0.6) + 7], fill="#bae6fd")
    draw.ellipse([cx - int(r * 0.52) - 7, cy + int(r * 0.3) - 7, cx - int(r * 0.52) + 7, cy + int(r * 0.3) + 7], fill="#bae6fd")
    draw.ellipse([cx + int(r * 0.52) - 7, cy + int(r * 0.3) - 7, cx + int(r * 0.52) + 7, cy + int(r * 0.3) + 7], fill="#bae6fd")

    # Text at bottom "E R P"
    try:
        font = ImageFont.truetype("arialbd.ttf", 38)
    except Exception:
        font = ImageFont.load_default()
        
    draw.text((cx, size - 85), "E R P", fill="#f8fafc", anchor="ms", font=font)

    # Save default_logo.png
    img.save(static_dir / "default_logo.png", format="PNG")
    print("Created default_logo.png")

if __name__ == "__main__":
    generate_default_logo()

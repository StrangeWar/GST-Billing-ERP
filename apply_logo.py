import sys
import shutil
from pathlib import Path
from PIL import Image

DST_DIR = Path("app/static/images")

def apply_logo(src_file: str = None):
    DST_DIR.mkdir(parents=True, exist_ok=True)
    dst_png = DST_DIR / "logo.png"
    dst_jpg = DST_DIR / "logo.jpg"
    
    if not src_file:
        if len(sys.argv) > 1:
            src_file = sys.argv[1]
        else:
            default_cand = DST_DIR / "default_logo.png"
            if default_cand.exists():
                src_file = str(default_cand)
            else:
                print("Usage: python apply_logo.py <path_to_image>")
                return
                
    src_path = Path(src_file)
    if not src_path.exists():
        print(f"Error: Source image file '{src_path}' not found.")
        return
        
    img = Image.open(src_path)
    # Save standard formats
    if img.mode in ("RGBA", "P"):
        img.convert("RGB").save(dst_jpg, quality=95)
    else:
        img.save(dst_jpg, quality=95)
    img.save(dst_png, format="PNG")
    print(f"Successfully applied company logo from '{src_path}' -> {dst_png}")

if __name__ == "__main__":
    apply_logo()

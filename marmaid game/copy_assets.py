import os
import shutil

def copy_assets():
    brain_dir = r"C:\Users\DeLL\.gemini\antigravity\brain\7ff622bd-79b9-4afd-a11f-ae1c1c9708d8"
    dest_dir = r"c:\Users\DeLL\Downloads\marmaid game\assets"
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created directory: {dest_dir}")
        
    mapping = {
        "bg_coral_palace_1782733855588.png": "bg_coral_palace.png",
        "bg_deep_abyss_1782733883316.png": "bg_deep_abyss.png",
        "bg_pearl_cave_1782733915912.png": "bg_pearl_cave.png",
        "bg_sunset_surface_1782733940086.png": "bg_sunset_surface.png",
        "char1_aria_1782733957145.png": "char_aria.png",
        "char2_naida_1782733989006.png": "char_naida.png"
    }
    
    for src_name, dest_name in mapping.items():
        src_path = os.path.join(brain_dir, src_name)
        dest_path = os.path.join(dest_dir, dest_name)
        
        if os.path.exists(src_path):
            shutil.copy(src_path, dest_path)
            print(f"Copied {src_name} -> {dest_name}")
        else:
            print(f"Warning: Source file {src_path} not found!")

if __name__ == "__main__":
    copy_assets()

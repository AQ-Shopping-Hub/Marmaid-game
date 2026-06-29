import sys
import subprocess

def install_dependencies():
    print("Checking dependencies...")
    try:
        import pygame
        print("pygame is installed.")
    except ImportError:
        print("pygame not found. Installing pygame...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
        import pygame
        print("pygame installed successfully!")

    try:
        from PIL import Image
        print("pillow (PIL) is installed.")
    except ImportError:
        print("pillow not found. Installing pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image
        print("pillow installed successfully!")

def make_transparent(input_path, output_path, bg_color=(255, 255, 255), tolerance=20):
    """
    Converts a solid color background (default white) to transparent.
    """
    from PIL import Image
    try:
        img = Image.open(input_path).convert("RGBA")
        datas = img.getdata()
        
        new_data = []
        for item in datas:
            # Check if pixel color is close to background color within tolerance
            is_bg = True
            for i in range(3):
                if abs(item[i] - bg_color[i]) > tolerance:
                    is_bg = False
                    break
            
            if is_bg:
                new_data.append((255, 255, 255, 0)) # transparent
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"Processed: {input_path} -> {output_path}")
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

if __name__ == "__main__":
    install_dependencies()
    import os
    assets_dir = r"c:\Users\DeLL\Downloads\marmaid game\assets"
    
    # Process Aria
    make_transparent(
        os.path.join(assets_dir, "char_aria.png"),
        os.path.join(assets_dir, "char_aria_trans.png"),
        bg_color=(255, 255, 255),
        tolerance=15
    )
    # Process Naida
    make_transparent(
        os.path.join(assets_dir, "char_naida.png"),
        os.path.join(assets_dir, "char_naida_trans.png"),
        bg_color=(255, 255, 255),
        tolerance=15
    )


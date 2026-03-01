import os
import glob
import shutil

base_dir = r"c:\Users\mete2\OneDrive\Masaüstü\test"
target_dir = os.path.join(base_dir, "ekran_projesi")

def list_images():
    print(f"\n[INFO] Listing all images in {base_dir}...")
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.svg']
    all_images = []
    for ext in extensions:
        all_images.extend(glob.glob(os.path.join(base_dir, ext)))
    
    if all_images:
        print("[OK] Found images:")
        for img in all_images:
            print(f"   - {os.path.basename(img)}")
            # Try to guess if it's the logo based on file size or name being short
            # Copy all images to target dir just in case for now (user said they put logos there)
            try:
                shutil.copy2(img, os.path.join(target_dir, os.path.basename(img)))
            except: pass
    else:
        print("[WARN] No images found in the directory.")

if __name__ == "__main__":
    list_images()

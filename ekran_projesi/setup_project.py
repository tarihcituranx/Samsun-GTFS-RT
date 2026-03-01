import shutil
import os
import glob
import sys

# Force UTF-8 stdout if possible, but let's just avoid fancy chars
# sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"c:\Users\mete2\OneDrive\Masaüstü\test"
target_dir = os.path.join(base_dir, "ekran_projesi")
db_source = os.path.join(base_dir, "samsun_v25.db")
db_target = os.path.join(target_dir, "samsun_screen.db")

def setup_files():
    # 1. Copy Database
    if os.path.exists(db_source):
        try:
            shutil.copy2(db_source, db_target)
            print(f"[OK] Database copied to {db_target}")
        except Exception as e:
            print(f"[ERROR] Copy failed: {e}")
    else:
        print(f"[ERROR] Source DB not found: {db_source}")

    # 2. Find Logos in base_dir
    print(f"\n[INFO] Searching for logos in {base_dir}...")
    logos = []
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.svg']
    for ext in extensions:
        logos.extend(glob.glob(os.path.join(base_dir, ext)))
    
    found_logos = [l for l in logos if 'samulas' in os.path.basename(l).lower() or 'sbb' in os.path.basename(l).lower() or 'logo' in os.path.basename(l).lower()]
    
    if found_logos:
        print(f"[OK] Found potential logos: {[os.path.basename(l) for l in found_logos]}")
        # Copy logos to target dir
        for logo in found_logos:
            try:
                dst = os.path.join(target_dir, os.path.basename(logo))
                shutil.copy2(logo, dst)
                print(f"   Copied {os.path.basename(logo)} -> {dst}")
            except Exception as e:
                print(f"   Failed to copy {os.path.basename(logo)}: {e}")
    else:
        print("[WARN] No logos found with keywords (samulas, sbb, logo)")

if __name__ == "__main__":
    setup_files()

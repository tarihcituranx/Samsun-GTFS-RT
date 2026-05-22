import sys
sys.stdout.reconfigure(encoding='utf-8')

endpoints = ["def get_tum_duraklar", "def proxy_odak", "def proxy_samair_araclar"]

with open('samsun.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for ep in endpoints:
    found = False
    for i, line in enumerate(lines, 1):
        if ep in line:
            print(f"\n--- Found {ep} at line {i} ---")
            # Print the next 35 lines
            for j in range(i-1, min(i+45, len(lines))):
                print(f"{j+1}: {lines[j].strip()}")
            found = True
            break
    if not found:
        print(f"\nCould not find {ep}")

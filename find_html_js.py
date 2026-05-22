import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('test.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if '</style>' in line:
            print(f"{i}: {line.strip()}")

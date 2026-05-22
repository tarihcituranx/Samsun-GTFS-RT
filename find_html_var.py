with open('samsun.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'HTML =' in line or 'HTML = """' in line:
            print(f'HTML variable definition starts at line {i}: {line.strip()[:100]}')

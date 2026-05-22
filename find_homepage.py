with open('samsun.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if '@app.get("/")' in line or 'test.html' in line:
            clean_line = line.strip().encode('ascii', errors='replace').decode('ascii')
            print(f'{i}: {clean_line}')

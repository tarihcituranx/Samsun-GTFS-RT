with open('samsun.py', 'r', encoding='utf-8') as f:
    content = f.read()
    # Find start of HTML = '''
    start = content.find("HTML = '''")
    if start == -1:
        start = content.find('HTML = """')
    
    if start != -1:
        end = content.find("'''", start + 10)
        if end == -1:
            end = content.find('"""', start + 10)
        
        if end != -1:
            html_content = content[start:end+3]
            print(f"HTML variable length in samsun.py: {len(html_content)} characters")
            
            # Check test.html length
            try:
                with open('test.html', 'r', encoding='utf-8') as tf:
                    test_content = tf.read()
                    print(f"test.html length: {len(test_content)} characters")
            except Exception as e:
                print(f"Error reading test.html: {e}")
        else:
            print("Could not find end of HTML variable")
    else:
        print("Could not find start of HTML variable")

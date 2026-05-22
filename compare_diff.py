import difflib

with open('samsun.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("HTML = '''")
if start == -1:
    start = content.find('HTML = """')

if start != -1:
    end = content.find("'''", start + 10)
    if end == -1:
        end = content.find('"""', start + 10)
    
    if end != -1:
        # Extract the actual HTML string content
        html_in_py = content[start + 10 : end]
        with open('test.html', 'r', encoding='utf-8') as tf:
            test_html_content = tf.read()
            
        print("Comparing HTML in python with test.html...")
        if html_in_py.strip() == test_html_content.strip():
            print("They are identical!")
        else:
            print("They are different.")
            # Print first 100 characters of differences
            diff = list(difflib.unified_diff(
                html_in_py.splitlines(keepends=True),
                test_html_content.splitlines(keepends=True),
                fromfile='samsun.py (HTML)',
                tofile='test.html',
                n=2
            ))
            print(f"Diff lines count: {len(diff)}")
            print("".join(diff[:20]))
else:
    print("Could not find HTML variable in samsun.py")

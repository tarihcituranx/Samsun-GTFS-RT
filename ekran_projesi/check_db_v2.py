import sqlite3

DB_PATH = r"c:\Users\mete2\OneDrive\Masaüstü\test\ekran_projesi\samsun_screen.db"

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)

    # Check hat_durak table columns
    try:
        cursor.execute("PRAGMA table_info(hat_durak);")
        columns = cursor.fetchall()
        print("\nColumns in hat_durak:", [c[1] for c in columns])
        
        # Sample data
        cursor.execute("SELECT * FROM hat_durak LIMIT 5;")
        rows = cursor.fetchall()
        print("\nSample rows in hat_durak:", rows)
        
        # Check specific line
        print("\nChecking for '26/17':")
        cursor.execute("SELECT COUNT(*) FROM hat_durak WHERE hat='26/17';")
        count = cursor.fetchone()[0]
        print(f"Rows for 26/17: {count}")
        
        if count == 0:
            print("Trying to find similar lines...")
            cursor.execute("SELECT DISTINCT hat FROM hat_durak WHERE hat LIKE '%26/17%' LIMIT 20;")
            lines = cursor.fetchall()
            print("Lines matching 26/17:", [l[0] for l in lines])

    except Exception as e:
        print(f"Error accessing hat_durak: {e}")

    conn.close()

if __name__ == "__main__":
    check_db()

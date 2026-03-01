import sqlite3

db_path = r"c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check hat_durak
    cursor.execute("SELECT count(*) FROM hat_durak")
    print(f"Row count in hat_durak: {cursor.fetchone()[0]}")
    
    # Sample data
    cursor.execute("SELECT DISTINCT hat FROM hat_durak LIMIT 5")
    print("Sample lines:", cursor.fetchall())
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")

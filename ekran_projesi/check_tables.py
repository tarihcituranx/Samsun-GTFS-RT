import sqlite3

db_path = r"c:\Users\mete2\OneDrive\Masaüstü\test\samsun_screen.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check for hat/route related tables
for t in tables:
    table_name = t[0]
    if 'hat' in table_name.lower() or 'route' in table_name.lower() or 'durak' in table_name.lower():
        print(f"\n{table_name} columns:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")

conn.close()

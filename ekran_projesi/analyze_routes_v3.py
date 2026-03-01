import sqlite3
import pandas as pd
import os

db_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db'

def find_longest_route_v3():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        
        # Query to count stops per route and get route details
        query = """
        SELECT h.code, h.name, h.tip, count(hd.durak_id) as stop_count
        FROM hat h
        JOIN hat_durak hd ON h.code = hd.hat
        GROUP BY h.code
        ORDER BY stop_count DESC
        LIMIT 10
        """
        
        print(f"Executing query on {db_path}...")
        df = pd.read_sql_query(query, conn)
        print("Top 10 Routes by Stop Count:")
        print(df)
        
        # Also specifically check for Tram lines
        print("\nChecking for Tram lines:")
        tram_query = """
        SELECT h.code, h.name, h.tip, count(hd.durak_id) as stop_count
        FROM hat h
        JOIN hat_durak hd ON h.code = hd.hat
        WHERE h.tip LIKE '%tramvay%' OR h.name LIKE '%tramvay%' OR h.name LIKE '%raylı%'
        GROUP BY h.code
        ORDER BY stop_count DESC
        """
        df_tram = pd.read_sql_query(tram_query, conn)
        print(df_tram)

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_longest_route_v3()

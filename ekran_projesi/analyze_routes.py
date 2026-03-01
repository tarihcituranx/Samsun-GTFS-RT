import sqlite3
import pandas as pd

def find_longest_route():
    try:
        conn = sqlite3.connect(r'c:\Users\mete2\OneDrive\Masaüstü\test\samsun.db')
        
        # Query to count stops per route
        query = """
        SELECT r.route_short_name, r.route_long_name, count(rs.stop_id) as stop_count
        FROM routes r
        JOIN trips t ON r.route_id = t.route_id
        JOIN stop_times rs ON t.trip_id = rs.trip_id
        GROUP BY r.route_id
        ORDER BY stop_count DESC
        LIMIT 5
        """
        
        # If the above query is too complex or schema differs, let's try a simpler approach 
        # listing tables first to be sure of schema
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        # Assuming standard GTFS-like schema or the one used in samsun.py
        # Let's try to get route info.
        
        # We'll just read routes and stops to pandas and analyze if SQL fails
        try:
            df = pd.read_sql_query(query, conn)
            print("Longest Routes by Stop Count (Approximation based on single trip):")
            print(df)
        except Exception as e:
            print(f"Complex query failed: {e}")
            print("Attempting to list routes...")
            routes = pd.read_sql_query("SELECT * FROM routes LIMIT 5", conn)
            print(routes.columns)
            print(routes)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_longest_route()

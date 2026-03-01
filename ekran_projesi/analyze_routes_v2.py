import sqlite3
import pandas as pd
import os

db_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db'

def find_longest_route():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in DB:", [t[0] for t in tables])

        # Try to find routes with most stops if tables exist
        # Adjust table names based on what we find. 
        # Assuming table names based on typical GTFS or previous knowledge, but let's be dynamic.
        
        if 'hatlar' in [t[0] for t in tables]: # Example Turkish table name check
             query = "SELECT * FROM hatlar LIMIT 5"
             df = pd.read_sql_query(query, conn)
             print("Sample from 'hatlar':")
             print(df.head())
        elif 'routes' in [t[0] for t in tables]:
             # Standard GTFS check
             query = """
                SELECT r.route_id, r.route_short_name, r.route_long_name, count(st.stop_id) as stop_count
                FROM routes r
                LEFT JOIN trips t ON r.route_id = t.route_id
                LEFT JOIN stop_times st ON t.trip_id = st.trip_id
                GROUP BY r.route_id
                ORDER BY stop_count DESC
                LIMIT 5
             """
             try:
                 df = pd.read_sql_query(query, conn)
                 print("Longest Routes:")
                 print(df)
             except:
                 print("Complex query failed, dumping routes table head")
                 print(pd.read_sql_query("SELECT * FROM routes LIMIT 5", conn))
        
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_longest_route()

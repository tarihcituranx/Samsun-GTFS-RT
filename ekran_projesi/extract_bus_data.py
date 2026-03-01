import sqlite3
import json
import os

db_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db'
output_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\ekran_projesi\bus_stops.json'

def extract_bus_stops():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get Bus stops for line 26/17 B.EVLER-NİVERSİTE
        cursor = conn.cursor()
        
        # First verify the exact hat code/name
        # The previous output showed "26/17 B.EVLER..."
        # Let's search by code '26/17'
        cursor.execute("SELECT * FROM hat_durak WHERE hat LIKE '26/17%' OR hat = '26/17' ORDER BY sira")
        rows = cursor.fetchall()
        
        if not rows:
             print("No stops found for '26/17', trying looser match")
             cursor.execute("SELECT DISTINCT hat FROM hat_durak")
             all_lines = [r[0] for r in cursor.fetchall()]
             # Try to find the closest match
             match = next((l for l in all_lines if '26/17' in l), None)
             if match:
                 print(f"Using line: {match}")
                 cursor.execute("SELECT * FROM hat_durak WHERE hat = ? ORDER BY sira", (match,))
                 rows = cursor.fetchall()
        
        stops = []
        for row in rows:
            stops.append({
                'id': row['durak_id'],
                'name': row['ad'],
                'sequence': row['sira'],
                'lat': row['lat'],
                'lon': row['lon']
            })
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stops, f, ensure_ascii=False, indent=2)
            
        print(f"Extracted {len(stops)} stops to {output_path}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_bus_stops()

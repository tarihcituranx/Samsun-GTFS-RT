import sqlite3
import json
import os

db_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db'
output_path = r'c:\Users\mete2\OneDrive\Masaüstü\test\ekran_projesi\tram_stops.json'

def extract_tram_stops():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get Tram stops
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hat_durak WHERE hat = 'SAMULAŞ - TRAMVAY' ORDER BY sira")
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
    extract_tram_stops()

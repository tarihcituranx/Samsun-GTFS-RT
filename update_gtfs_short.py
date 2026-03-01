import sqlite3
import requests
import zipfile
import io

DB = 'samsun_v25.db'

def update_short_names():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Ensure column exists (samsun.py create_tables might not have run if db exists)
    try:
        c.execute("ALTER TABLE hat ADD COLUMN short_name TEXT DEFAULT ''")
    except:
        pass # column exists
        
    print("1. Fetching from Samulaş V1 API...")
    r = requests.get("https://samulas.com.tr/api/v1/lines/list?page=1&limit=500", timeout=10)
    v1_data = r.json().get('data', {}).get('data', [])
    updated = 0
    for d in v1_data:
        code = str(d.get('line_code', '')).strip()
        short = str(d.get('short_line_name', '')).strip()
        if code and short:
            c.execute("UPDATE hat SET short_name=? WHERE code=?", (short, code))
            updated += 1
    
    print(f"   -> Updated {updated} lines with direct V1 API short_names.")
    
    # Fallback regex for remaining
    c.execute("UPDATE hat SET short_name = SUBSTR(code, 1, INSTR(code, ' ') - 1) WHERE (short_name = '' OR short_name IS NULL) AND code LIKE '% %' AND (code LIKE 'H%' OR code LIKE 'R%' OR code LIKE 'E%')")
    c.execute("UPDATE hat SET short_name = code WHERE (short_name = '' OR short_name IS NULL)")
    conn.commit()
    print("   -> Applied Regex fallback for missing SAMAIR/R1 lines.")
    
    # Generate GTFS
    print("2. Generating GTFS ZIP...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # agency.txt
        agency_txt = "agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone\n"
        agency_txt += "samulas,Samulaş,https://samulas.com.tr,Europe/Istanbul,tr,444 1 619\n"
        zf.writestr("agency.txt", agency_txt)
        
        # routes.txt
        routes_txt = "route_id,agency_id,route_short_name,route_long_name,route_type,route_color,route_text_color\n"
        hatlar = c.execute("SELECT code, name, tip, short_name FROM hat").fetchall()
        for h in hatlar:
            route_type = {
                'otobus': '3', 'tramvay': '0', 'ring': '3', 'ekspres': '3',
                'havalimani': '3', 'ilce': '3', 'teleferik': '6', 'tekne': '4'
            }.get(h['tip'], '3')
            
            color = {
                'otobus': '1877F2', 'tramvay': 'E67E22', 'ring': 'F39C12', 'ekspres': '9B59B6',
                'havalimani': 'E74C3C', 'ilce': '1ABC9C', 'teleferik': 'E91E63', 'tekne': '3498DB'
            }.get(h['tip'], '1877F2')
            
            r_short = str(h['short_name']).strip() if h['short_name'] else h['code']
            routes_txt += f"{h['code']},samulas,{r_short},{h['name']},{route_type},{color},FFFFFF\n"
        zf.writestr("routes.txt", routes_txt)
        
    with open('samsun_gtfs_v25.zip', 'wb') as f:
        f.write(zip_buffer.getvalue())
    print("   -> Success! Saved to samsun_gtfs_v25.zip")

    conn.close()

if __name__ == "__main__":
    update_short_names()

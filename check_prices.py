import sqlite3

def check():
    conn = sqlite3.connect('samsun_v25.db')
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT * FROM fiyat").fetchall()
    print(f"Total price records: {len(res)}")
    for r in res[:20]:
        print(dict(r))
    
    # Check specifically for Tramvay or distance based
    print("\n--- TRAMVAY ---")
    res_tram = conn.execute("SELECT * FROM fiyat WHERE hat_adi LIKE '%TRAMVAY%' OR hat_code LIKE '%TRAM%'").fetchall()
    for r in res_tram:
        print(dict(r))

    conn.close()

if __name__ == "__main__":
    check()

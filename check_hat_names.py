import sqlite3

def check():
    conn = sqlite3.connect('samsun_v25.db')
    conn.row_factory = sqlite3.Row
    res = conn.execute("SELECT code, name FROM hat WHERE kat IN ('tekne', 'teleferik', 'tramvay', 'otobus')").fetchall()
    print(f"Total lines: {len(res)}")
    for r in res:
        if 'SAMSUNUM' in r['name'].upper() or 'ALTINKAYA' in r['name'].upper() or 'TELEFERİK' in r['name'].upper() or 'TRAMVAY' in r['name'].upper():
            print(f"Code: {r['code']}, Name: {r['name']}")
    conn.close()

if __name__ == "__main__":
    check()

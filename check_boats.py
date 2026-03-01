import sqlite3
try:
    conn = sqlite3.connect('samsun_v25.db')
    c = conn.cursor()
    print("--- LINES ---")
    rows = c.execute("SELECT code, name FROM hat WHERE name LIKE '%SAMSUNUM%' OR name LIKE '%FERİBOT%' OR name LIKE '%TELEFERİK%'").fetchall()
    for r in rows:
        print(r)
        print(f"  Duraklar for {r[0]}:")
        stops = c.execute("SELECT * FROM hat_durak WHERE hat=?", (r[0],)).fetchall()
        print(len(stops))
        print(f"  Seferler for {r[0]}:")
        trips = c.execute("SELECT * FROM sefer WHERE hat=?", (r[0],)).fetchall()
        print(len(trips))
        if trips: print(trips[:2])
except Exception as e:
    print(e)

#!/usr/bin/env python3
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('samsun_v25.db')
conn.row_factory = sqlite3.Row

print('=== SAMAIR SEFER TABLOSU ===')
cnt = conn.execute("SELECT COUNT(*) FROM samair_sefer").fetchone()[0]
print(f'Toplam: {cnt}')

rows = conn.execute('SELECT * FROM samair_sefer LIMIT 10').fetchall()
for r in rows:
    print(dict(r))

print()
print('=== HAT BAZINDA ===')
for hat_id in [1, 2, 3, 4]:
    cnt = conn.execute("SELECT COUNT(*) FROM samair_sefer WHERE hat=?", (hat_id,)).fetchone()[0]
    print(f'Hat {hat_id}: {cnt} sefer')

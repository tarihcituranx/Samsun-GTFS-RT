
import sqlite3

db = sqlite3.connect('samsun_v25.db')
cur = db.cursor()

# HAT tablosu
cur.execute("UPDATE hat SET code = REPLACE(code, 'SAMULA', 'SAMULAŞ') WHERE code LIKE '%SAMULA%'")
cur.execute("UPDATE hat SET name = REPLACE(name, 'SAMULA', 'SAMULAŞ') WHERE name LIKE '%SAMULA%'")

# HAT_DURAK tablosu
cur.execute("UPDATE hat_durak SET hat = REPLACE(hat, 'SAMULA', 'SAMULAŞ') WHERE hat LIKE '%SAMULA%'")

# SEFER tablosu
cur.execute("UPDATE sefer SET hat = REPLACE(hat, 'SAMULA', 'SAMULAŞ') WHERE hat LIKE '%SAMULA%'")

db.commit()
print("Düzeltme tamamlandı.")

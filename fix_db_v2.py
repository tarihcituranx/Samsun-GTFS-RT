
import sqlite3

db = sqlite3.connect('samsun_v25.db')
cur = db.cursor()

# HAT (SAMULA... ile başlayanları güncelle)
cur.execute("UPDATE hat SET code = 'SAMULAŞ - TRAMVAY' WHERE code LIKE 'SAMULA%TRAMVAY%'")
cur.execute("UPDATE hat SET name = 'SAMULAŞ - TRAMVAY' WHERE name LIKE 'SAMULA%TRAMVAY%'")
cur.execute("UPDATE hat SET code = 'SAMULAŞ EKSPRES' WHERE code LIKE 'SAMULA%EKSPRES%' AND code NOT LIKE '%G%D%' AND code NOT LIKE '%D%N%'")

# HAT_DURAK
cur.execute("UPDATE hat_durak SET hat = 'SAMULAŞ - TRAMVAY' WHERE hat LIKE 'SAMULA%TRAMVAY%'")
cur.execute("UPDATE hat_durak SET hat = 'SAMULAŞ EKSPRES' WHERE hat LIKE 'SAMULA%EKSPRES%' AND hat NOT LIKE '%G%D%' AND hat NOT LIKE '%D%N%'")

# SEFER
cur.execute("UPDATE sefer SET hat = 'SAMULAŞ - TRAMVAY' WHERE hat LIKE 'SAMULA%TRAMVAY%'")
cur.execute("UPDATE sefer SET hat = 'SAMULAŞ EKSPRES' WHERE hat LIKE 'SAMULA%EKSPRES%' AND hat NOT LIKE '%G%D%' AND hat NOT LIKE '%D%N%'")

db.commit()
print("Kapsamlı düzeltme tamamlandı.")

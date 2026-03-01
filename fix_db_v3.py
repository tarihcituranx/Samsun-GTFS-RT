
import sqlite3

db = sqlite3.connect('samsun_v25.db')
cur = db.cursor()

# 1. HAT_DURAK tablosunu güncelle (Bozuk -> Doğru)
cur.execute("UPDATE hat_durak SET hat = 'SAMULAŞ - TRAMVAY' WHERE hat LIKE 'SAMULA%TRAMVAY%' AND hat != 'SAMULAŞ - TRAMVAY'")
cur.execute("UPDATE hat_durak SET hat = 'SAMULAŞ EKSPRES' WHERE hat LIKE 'SAMULA%EKSPRES%' AND hat != 'SAMULAŞ EKSPRES' AND hat NOT LIKE '%G%D%' AND hat NOT LIKE '%D%N%'")

# 2. SEFER tablosunu güncelle
cur.execute("UPDATE sefer SET hat = 'SAMULAŞ - TRAMVAY' WHERE hat LIKE 'SAMULA%TRAMVAY%' AND hat != 'SAMULAŞ - TRAMVAY'")
cur.execute("UPDATE sefer SET hat = 'SAMULAŞ EKSPRES' WHERE hat LIKE 'SAMULA%EKSPRES%' AND hat != 'SAMULAŞ EKSPRES' AND hat NOT LIKE '%G%D%' AND hat NOT LIKE '%D%N%'")

# 3. HAT tablosundaki bozuk kayıtları sil (Çünkü doğrusu varsa onu kullanacağız)
# Önce doğrusu var mı diye kontrol etmeyip direkt bozukları silelim, çünkü ilişkili tabloları güncelledik.
# Ama eğer doğrusu YOKSA, silmek yerine UPDATE etmeliyiz.

# TRAMVAY İÇİN:
# Doğru kayıt var mı?
res = cur.execute("SELECT code FROM hat WHERE code = 'SAMULAŞ - TRAMVAY'").fetchone()
if res:
    # Varsa, bozuk olanları sil
    cur.execute("DELETE FROM hat WHERE code LIKE 'SAMULA%TRAMVAY%' AND code != 'SAMULAŞ - TRAMVAY'")
else:
    # Yoksa, bozuk olanı düzelt (Tek bir tane olduğu varsayımıyla)
    cur.execute("UPDATE hat SET code = 'SAMULAŞ - TRAMVAY', name = 'SAMULAŞ - TRAMVAY' WHERE code LIKE 'SAMULA%TRAMVAY%'")

# EKSPRES İÇİN:
res_exp = cur.execute("SELECT code FROM hat WHERE code = 'SAMULAŞ EKSPRES'").fetchone()
if res_exp:
    cur.execute("DELETE FROM hat WHERE code LIKE 'SAMULA%EKSPRES%' AND code != 'SAMULAŞ EKSPRES' AND code NOT LIKE '%G%D%' AND code NOT LIKE '%D%N%'")
else:
    cur.execute("UPDATE hat SET code = 'SAMULAŞ EKSPRES' WHERE code LIKE 'SAMULA%EKSPRES%' AND code NOT LIKE '%G%D%' AND code NOT LIKE '%D%N%'")

db.commit()
print("Çakışmasız düzeltme tamamlandı.")

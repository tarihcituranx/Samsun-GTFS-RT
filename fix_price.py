import sqlite3

c = sqlite3.connect('samsun_v25.db')
c.execute("UPDATE samair_durak SET fiyat='120.0' WHERE hat > 0")
c.commit()
for row in c.execute("SELECT hat, ad, fiyat FROM samair_durak WHERE hat > 0 LIMIT 5"):
    print(dict(row))
print('Price updated to 120.0 in DB!')
c.close()

import sqlite3

c = sqlite3.connect('samsun_v25.db')
c.execute("UPDATE samair_durak SET fiyat='120.0'")
c.commit()
print('Price updated to 120.0 in DB!')
c.close()

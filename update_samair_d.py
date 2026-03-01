from samsun import DB, APIClient, Collector
import logging

logging.basicConfig(level=logging.INFO)
db = DB('samsun_v25.db')
http = APIClient('samsun_v25.db')
c = Collector(db, http)
c._samair_duraklar()

res = db.get("SELECT hat, ad, fiyat FROM samair_durak WHERE hat > 0 LIMIT 5")
print("Updated samair_durak sample:")
for r in res:
    print(dict(r))

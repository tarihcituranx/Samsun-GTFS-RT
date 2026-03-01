from samsun import Database, Http, Collector
import logging

logging.basicConfig(level=logging.INFO)
db = Database()
http = Http()
c = Collector(db, http)
c._samair_duraklar()

res = db.get("SELECT ad, kod, fiyat FROM samair_durak WHERE hat > 0")
print({r['ad']: r['fiyat'] for r in res})

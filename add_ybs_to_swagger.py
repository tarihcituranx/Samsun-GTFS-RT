import json

with open('asis_samsun_swagger.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Global configuration notes
schema['info']['description'] += "\n\n### YBS Entegrasyonu\nSamsun Büyükşehir Belediyesinin ana projede (samsun.py) kullanılan tüm YBS (Yönetim Bilgi Sistemi) metodları bu şemaya yedeklenmiştir. YBS endpointleri genellikle `https://ybs.samsun.bel.tr/service/?method=...` formatında çalışır. Metod bazında özel açıklamalara dikkat ediniz."

ybs_server = [{"url": "https://ybs.samsun.bel.tr/service", "description": "YBS API Sunucusu"}]

# 1. getGuestToken
schema['paths']['/?method=getGuestToken'] = {
    "get": {
        "tags": ["YBS - Yetkilendirme"],
        "summary": "Misafir Token Al (Guest Token)",
        "description": "**ÖNEMLİ (Quirk):** YBS servislerinin büyük çoğunluğu her istekte güncel bir `token` parametresine ihtiyaç duyar. Bu token'ın süresi yaklaşık 200 saniye (3 dakika) kadardır. `samsun.py` içinde kendi thread-safe cache mekanizması (ybs_token metodu) ile yönetilir.",
        "servers": ybs_server,
        "responses": {
            "200": {
                "description": "Başarılı.",
                "content": {
                    "application/json": {
                        "example": {"token": "ikyRM7OdnfKl"}
                    }
                }
            }
        }
    }
}

# 2. samair_ucaksefersaatleri_public
schema['paths']['/?method=samair_ucaksefersaatleri_public'] = {
    "get": {
        "tags": ["YBS - Samair Havaalanı Servisleri"],
        "summary": "Havaalanı Sefer Saatleri",
        "description": "**ÖNEMLİ:** YBS endpointlerinde parametreler bazen boş dönebilir, tip yapısı dict veya list olarak karmaşık gelebilir. `samair_ucaksefersaatleri_public` metodu uçuş saatini ve otobüs kalkış detaylarını verir.",
        "servers": ybs_server,
        "parameters": [
            {"name": "submethod", "in": "query", "description": "Alt metod adı (Örn: HatlarList)", "schema": {"type": "string"}},
            {"name": "hatid", "in": "query", "description": "Hat kimliği (Örn: H1 için 3, Bafra için 8 vs.)", "schema": {"type": "integer"}},
            {"name": "token", "in": "query", "description": "Geçerli YBS Token'i", "schema": {"type": "string"}}
        ],
        "responses": {
            "200": {
                "description": "Başarılı.",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "SUCCESS", 
                            "data": [
                                {
                                    "id": 21793, 
                                    "hatid": 3, 
                                    "saat": "00:30:00", 
                                    "varis_saati": "01:45:00", 
                                    "tarih": "2026-02-27", 
                                    "ucak_firmasi": "AJET", 
                                    "ucak_saatleri": "03:30", 
                                    "formatted_date": "27 Şubat 2026 Cuma"
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
}

# 3. samair_duraklar_public
schema['paths']['/?method=samair_duraklar_public'] = {
    "get": {
        "tags": ["YBS - Samair Havaalanı Servisleri"],
        "summary": "Samair Durak Listesi",
        "description": "Samair otobüslerine ait durak koordinatlarını ve bilet fiyatlandırmalarını listeler.",
        "servers": ybs_server,
        "parameters": [
            {"name": "submethod", "in": "query", "description": "Alt metod adı (Örn: DuraklarList)", "schema": {"type": "string"}},
            {"name": "token", "in": "query", "description": "Geçerli YBS Token'i", "schema": {"type": "string"}}
        ],
        "responses": {
            "200": {
                "description": "Başarılı.",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "SUCCESS", 
                            "data": [
                                {
                                    "id": 1, 
                                    "durak_adi": "Rektörlük Tramvay İstasyonu", 
                                    "durak_lat": "36.225315980358843", 
                                    "durak_long": "41.3718854642756", 
                                    "durak_kodu": "31632", 
                                    "durak_fiyat": "130"
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
}


# 4. odakSamsun_Crud
schema['paths']['/?method=odakSamsun_Crud'] = {
    "get": {
        "tags": ["YBS - Odak (İlçe Hatlar)"],
        "summary": "Odak Samsun Hat ve Durak Verileri",
        "description": "**ÖNEMLİ (Header Quirk):** `odakSamsun_Crud` metodu çalışmak için HTTP isteklerinde `Referer: https://odak.samsun.bel.tr/` header alanına ihtiyaç duyar. Ayrıca alt metodu (HatlarAllList, HatlarList, GetHatDuraklar vb.) query ile belirtilir.",
        "servers": ybs_server,
        "parameters": [
            {"name": "submethod", "in": "query", "description": "HatlarAllList, HatlarList veya GetHatDuraklar", "schema": {"type": "string"}},
            {"name": "id", "in": "query", "description": "GetHatDuraklar çağırılırken hat ID gereklidir.", "schema": {"type": "integer"}},
            {"name": "token", "in": "query", "description": "Geçerli YBS Token'i", "schema": {"type": "string"}}
        ],
        "responses": {
            "200": {
                "description": "Başarılı.",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "SUCCESS",
                            "data": [
                                {
                                    "id": 6, 
                                    "durak_adi": "Toplu Taşıma Transfer Merkezi", 
                                    "durak_lat": None, 
                                    "durak_long": None, 
                                    "durak_kodu": "13831", 
                                    "durak_fiyat": "115,00",
                                    "durak_fiyat_ogr": "92,00"
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
}

with open('asis_samsun_swagger.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)
print("Updated.")

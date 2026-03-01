import json

try:
    with open('asis_samsun_swagger.json', 'r', encoding='utf-8') as f:
        schema = json.load(f)

    schema['paths']['/api/v1/lines/list'] = {
        "get": {
            "tags": ["Samulaş Web APIleri (V1)"],
            "summary": "Tüm Hatlar ve Kısa Kodları (Short Names)",
            "description": "Samulaş'ın yeni V1 API'si. Bu uç nokta, ASİS sistemine GTFS (Route Short Name) ve güzergahın ilk/son durak koordinatlarını sağlamak amacıyla 'zenginleştirici' (fallback/enhancer) olarak sisteme entegre edilmiştir.",
            "servers": [{"url": "https://samulas.com.tr"}],
            "parameters": [
                {"name": "page", "in": "query", "description": "Sayfa Numarası", "schema": {"type": "integer", "default": 1}},
                {"name": "limit", "in": "query", "description": "Sayfa Başına Kayıt Sayısı", "schema": {"type": "integer", "default": 500}}
            ],
            "responses": {
                "200": {
                    "description": "Başarılı.",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "success",
                                "statusCode": 200,
                                "data": {
                                    "data": [
                                        {
                                            "text": "R2 CEZAEVİ-EĞİTİM ARAŞTIRMA-BÜYÜK CAMİ",
                                            "id": 993,
                                            "line_code": "R2 CEZAEVİ-BÜYÜK CAMİ",
                                            "short_line_name": "R2",
                                            "first_station": {"station_name": "10052 - BÜYÜK CAMİ", "latitude": "41.294762", "longitude": "36.333906"},
                                            "last_station": {"station_name": "11872 - YENİ CEZAEVİ", "latitude": "41.259421", "longitude": "36.234579"}
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    with open('asis_samsun_swagger.json', 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print("Swagger belgesine V1 API başarıyla eklendi!")
except Exception as e:
    print(f"Hata oluştu: {e}")

import requests
import pandas as pd
import time
import json
import os

# Ayarlar
BASE_URL = "https://ybs.samsun.bel.tr/service/"
requests.packages.urllib3.disable_warnings()

def get_token():
    print("🔑 Token alınıyor...")
    try:
        payload = {'method': 'getGuestToken'}
        response = requests.post(BASE_URL, data=payload, verify=False)
        data = response.json()
        if 'token' in data: return data['token']
        if 'result' in data and 'token' in data['result']: return data['result']['token']
    except:
        pass
    return None

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        clean = str(price_str).replace(',', '.').replace('TL', '').strip()
        return float(clean)
    except:
        return 0.0

def get_all_details(token, hat_listesi):
    print(f"\n🚍 Toplam {len(hat_listesi)} hattın detayları çekiliyor...")
    print("   (Ladik, Şahinkaya, Ayvacık ve diğerleri dahil)\n")
    
    tum_veriler = []
    
    for _, row in hat_listesi.iterrows():
        hat_id = row['id']
        hat_adi = row['Hat Adı']
        
        print(f"   Reading ID: {hat_id} - {hat_adi}...")
        
        try:
            payload = {
                'method': 'odakSamsun_Crud',
                'submethod': 'GetHatDuraklar',
                'token': token,
                'id': hat_id
            }
            res = requests.get(BASE_URL, params=payload, verify=False)
            data = res.json()
            
            if 'data' in data and isinstance(data['data'], list):
                duraklar = data['data']
                for d in duraklar:
                    tum_veriler.append({
                        'Hat_ID': hat_id,
                        'Hat_Adi': hat_adi,
                        'Durak_Adi': d.get('durak_adi'),
                        'Tam_Fiyat': clean_price(d.get('durak_fiyat')),
                        'Ogrenci_Fiyat': clean_price(d.get('durak_fiyat_ogr')),
                        'Kalkis_Saati': d.get('saat'),
                        'Varis_Saati': d.get('varis_saati'),
                        'Durak_Kodu': d.get('durak_kodu')
                    })
            else:
                # Veri yoksa bile boş satır ekleyelim ki raporda görünsün
                tum_veriler.append({
                    'Hat_ID': hat_id,
                    'Hat_Adi': hat_adi,
                    'Durak_Adi': "Veri Yok / Sefer Yok",
                    'Tam_Fiyat': 0,
                    'Ogrenci_Fiyat': 0,
                    'Kalkis_Saati': "-",
                    'Varis_Saati': "-",
                    'Durak_Kodu': "-"
                })
                
        except Exception as e:
            print(f"   Hata (ID {hat_id}): {e}")
        
        time.sleep(0.2) 

    return tum_veriler

def main():
    # 1. Önce ID listesini dosyadan (veya API'den) alalım
    input_file = "Samsun_Odak_Turizm_Hatlari.xlsx"
    
    if os.path.exists(input_file):
        print(f"📂 '{input_file}' dosyasından hat listesi okunuyor...")
        df_hatlar = pd.read_excel(input_file)
    else:
        print("⚠️ Dosya bulunamadı, API'den canlı liste çekiliyor...")
        token = get_token()
        if not token: return
        # Manuel API çağrısı (Dosya yoksa)
        res = requests.get(BASE_URL, params={'method':'odakSamsun_Crud', 'submethod':'HatlarAllList', 'token':token}, verify=False)
        df_hatlar = pd.DataFrame(res.json().get('data', []))
        # Sütun isimlerini uyumlu hale getir
        if 'hat_adi' in df_hatlar.columns:
            df_hatlar.rename(columns={'hat_adi': 'Hat Adı'}, inplace=True)

    # 2. Token al
    token = get_token()
    if not token:
        print("❌ Token alınamadı.")
        return

    # 3. Tüm detayları çek
    all_data = get_all_details(token, df_hatlar)
    
    # 4. Kaydet
    if all_data:
        df_final = pd.DataFrame(all_data)
        
        output_file = "Samsun_Odak_Turizm_Fiyatlari_FULL.xlsx"
        df_final.to_excel(output_file, index=False)
        
        print("\n" + "="*50)
        print(f"✅ İŞLEM TAMAMLANDI!")
        print(f"📂 Dosya: {output_file}")
        print("="*50)
        # Ladik kontrolü
        ladik_check = df_final[df_final['Hat_Adi'].str.contains("Ladik", case=False, na=False)]
        if not ladik_check.empty:
            print(f"✅ Ladik hatları başarıyla eklendi ({len(ladik_check)} satır).")
        else:
            print("⚠️ Ladik hatları listede görünüyor ama detay çekilemedi.")
            
    else:
        print("Veri toplanamadı.")

if __name__ == "__main__":
    main()
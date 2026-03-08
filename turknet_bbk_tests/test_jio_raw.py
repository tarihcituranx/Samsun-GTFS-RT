import requests

headers = {
    'accept': 'application/json; charset=utf-8',
    'accept-language': 'tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
    'origin': 'https://www.jio.com.tr',
    'referer': 'https://www.jio.com.tr/internet-altyapi-hiz-sorgulama',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
    'x-xsrf-token': 'e:VfyY9G3LXjRq2z__rOu5JvIVbVPAfKHGNWewlXNE0YSOOn9fyq16ALAdkDmfZ6ygOfJNYtiM_yJdbYQ-Vg2RtkTLe1zhWRmhex5A00HVmvs.RDRpanh1Wl95Tm5ocDNjOA.ZBMxfm2jvXCER9XmQ0hLy8sORTJ_hN2oWkg7FeyM-28'
}

cookies = {
    '_fbp': 'fb.2.1772923702189.700786367473862801',
    'adonis-session': 's%3AeyJtZXNzYWdlIjoiY21taG8zdm1leXI3bjM0am1oa3Z1NWdvcCIsInB1cnBvc2UiOiJhZG9uaXMtc2Vzc2lvbiJ9.7s3bKFocN88aFA-8bysUgNfXyEOp0d2v-XnaI9XpwdQ',
    'XSRF-TOKEN': 'e%3AVfyY9G3LXjRq2z__rOu5JvIVbVPAfKHGNWewlXNE0YSOOn9fyq16ALAdkDmfZ6ygOfJNYtiM_yJdbYQ-Vg2RtkTLe1zhWRmhex5A00HVmvs.RDRpanh1Wl95Tm5ocDNjOA.ZBMxfm2jvXCER9XmQ0hLy8sORTJ_hN2oWkg7FeyM-28',
    'cmmho3vmeyr7n34jmhkvu5gop': 'e%3AawiWWvuEQG2Tb6ygPr-tuCnnupHolhwTFrFQW9CuYVnu51recQp2DGrqXOPHiHsWFenqiesp8s12OV-BWutkjd2HOaUWN-El0WN21SCKUuZBGZikaUsxg7y7VqmiYYJD.UmpJR1ZlSEQ4QVc4cnhabA.eA2_vduvqbIVXN2ja9tfM6n7XOBxyuvk7NoWUvl0HWA'
}

data = {
    'selectedCity': {'code': 34, 'value': 'İSTANBUL'},
    'selectedTown': {'code': '1183', 'value': 'BEŞİKTAŞ'},
    'selectedNeighbor': {'code': '40232', 'value': 'BEBEK MAHALLESİ', 'post_code': '34342'},
    'selectedStreet': {'code': '743926', 'value': 'AZİZ OGAN SOKAGI'},
    'selectedBuilding': {'code': '18023369', 'value': 'NO :13AKASYA APARTMANI'},
    'selectedHome': {'code': '15814309', 'value': 'Ic Kapi(Daire) No :3'}
}

response = requests.post(
    'https://www.jio.com.tr/api/v1/ttservice/tt_vae_query',
    cookies=cookies,
    headers=headers,
    json=data,
    verify=False
)
print('STATUS:', response.status_code)
print('BODY:', response.text)

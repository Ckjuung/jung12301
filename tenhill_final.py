import requests
import xmltodict
import pandas as pd
from datetime import datetime

# ✅ 설정
service_key = 'DBL9/jevAhTCfpDi5RqbnF61jt1lxJGlxxUSW/7mv4GB9bDJk6F1V+2izfb51UFSFtAGXxQ89Xy89pk4VFOMuQ=='
LAWD_CD = '11200'  # 성동구 (하왕십리동용)
LAWD_CD2 = '11710' # 송파구 (잠실동용)
DEAL_YMD = datetime.today().strftime("%Y%m")
TELEGRAM_TOKEN = '7360228257:AAF9V2WcMmm6zP9SW4HPeh2RGpS_f672gN4'
CHAT_ID = '459970561'

def fetch_and_alert(lawd_cd):
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        'serviceKey': service_key,
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': DEAL_YMD,
        'numOfRows': '1000',
        'pageNo': '1'
    }

    res = requests.get(url, params=params)
    data = xmltodict.parse(res.text)

    if 'response' not in data or 'body' not in data['response'] or 'items' not in data['response']['body']:
        print(f"❌ 응답 오류 (법정동코드 {lawd_cd})")
        return

    items = data['response']['body']['items']
    if not items or 'item' not in items:
        print(f"❌ 거래 없음 (법정동코드 {lawd_cd})")
        return

    raw = items['item']
    df = pd.DataFrame(raw if isinstance(raw, list) else [raw])
    df['excluUseAr'] = df['excluUseAr'].astype(float)

    # ✅ 조건별 필터
    cond_1 = (df['umdNm'] == '하왕십리동') &              (df['aptNm'].isin(['텐즈힐(1단지)', '하왕십리센트라스'])) &              (df['excluUseAr'].between(83.0, 85.99))

    cond_2 = (df['umdNm'] == '잠실동') & (df['aptNm'] == '우성4차')

    result = df[cond_1 | cond_2].copy()

    if result.empty:
        print("🔍 조건에 맞는 거래 없음")
        return

    result['거래금액(만원)'] = result['dealAmount'].str.replace(',', '').astype(int)
    for _, row in result.iterrows():
        message = (
            f"[실거래가 알림]\n"
            f"📅 {row['dealYear']}.{row['dealMonth']}.{row['dealDay']}\n"
            f"🏢 {row['aptNm']} | {row['umdNm']} | {row['excluUseAr']}㎡ | {row['floor']}층\n"
            f"💰 {row['거래금액(만원)']:,}만원"
        )
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(tg_url, data={'chat_id': CHAT_ID, 'text': message})

# 성동구 + 송파구 모두 조회
fetch_and_alert(LAWD_CD)
fetch_and_alert(LAWD_CD2)

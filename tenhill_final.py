import requests
import xmltodict
import pandas as pd
from datetime import datetime
import os
import json

# ✅ 설정
service_key = 'DBL9/jevAhTCfpDi5RqbnF61jt1lxJGlxxUSW/7mv4GB9bDJk6F1V+2izfb51UFSFtAGXxQ89Xy89pk4VFOMuQ=='
TELEGRAM_TOKEN = '7360228257:AAF9V2WcMmm6zP9SW4HPeh2RGpS_f672gN4'
CHAT_ID = '459970561'

# ✅ UID 중복 방지 저장소
SEEN_FILE = "seen.json"
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, 'r') as f:
        seen = set(json.load(f))
else:
    seen = set()

# ✅ 거래 수집 범위: 2025.01 ~ 현재
start = datetime(2025, 4, 1)
today = datetime.today()
months = []
while start <= today:
    months.append(start.strftime("%Y%m"))
    if start.month == 12:
        start = datetime(start.year + 1, 1, 1)
    else:
        start = datetime(start.year, start.month + 1, 1)

def fetch_data(lawd_cd):
    all_rows = []
    for deal_ymd in months:
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
        params = {
            'serviceKey': service_key,
            'LAWD_CD': lawd_cd,
            'DEAL_YMD': deal_ymd,
            'numOfRows': '1000',
            'pageNo': '1'
        }

        res = requests.get(url, params=params)
        data = xmltodict.parse(res.text)

        if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
            items = data['response']['body']['items']
            if items and 'item' in items:
                rows = items['item']
                if isinstance(rows, list):
                    all_rows.extend(rows)
                else:
                    all_rows.append(rows)
    return pd.DataFrame(all_rows)

# ✅ 대상 지역: 성동구 + 송파구
df1 = fetch_data("11200")  # 하왕십리동 (텐즈힐, 센트라스)
df2 = fetch_data("11710")  # 잠실동 (우성4차)

if df1.empty and df2.empty:
    print("❌ 전체 조회 결과 없음")
    exit()

df = pd.concat([df1, df2], ignore_index=True)
df['excluUseAr'] = df['excluUseAr'].astype(float)

# ✅ 필터 조건
cond_1 = (df['umdNm'] == '하왕십리동') &          (df['aptNm'].isin(['텐즈힐(1단지)', '하왕십리센트라스'])) &          (df['excluUseAr'].between(83.0, 85.99))

cond_2 = (df['umdNm'] == '잠실동') & (df['aptNm'] == '우성4차')

filtered = df[cond_1 | cond_2].copy()

# ✅ 거래 고유 UID 생성
filtered['uid'] = filtered['dealYear'] + filtered['dealMonth'] + filtered['dealDay'] +                   filtered['aptNm'] + filtered['excluUseAr'].astype(str) + filtered['floor']

# ✅ 새 거래 필터링
new_trades = filtered[~filtered['uid'].isin(seen)].copy()

if new_trades.empty:
    print("🔍 조건에 맞는 새 거래 없음")
else:
    new_trades['거래금액(만원)'] = new_trades['dealAmount'].str.replace(',', '').astype(int)
    for _, row in new_trades.iterrows():
        msg = (
            f"[실거래가 알림]\n"
            f"📅 {row['dealYear']}.{row['dealMonth']}.{row['dealDay']}\n"
            f"🏢 {row['aptNm']} | {row['umdNm']} | {row['excluUseAr']}㎡ | {row['floor']}층\n"
            f"💰 {row['거래금액(만원)']:,}만원"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg})
        seen.add(row['uid'])

    # ✅ 중복 방지 UID 저장
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

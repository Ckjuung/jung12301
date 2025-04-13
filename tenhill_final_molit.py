import requests, json, os
from datetime import datetime
from xml.etree import ElementTree as ET

API_KEY = 'DBL9/jevAhTCfpDi5RqbnF61jt1lxJGlxxUSW/7mv4GB9bDJk6F1V+2izfb51UFSFtAGXxQ89Xy89pk4VFOMuQ=='
BASE_URL = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
LAWD_CD = '11200'
SEEN_FILE = 'molit_seen.json'
TELEGRAM_TOKEN = '7360228257:AAF9V2WcMmm6zP9SW4HPeh2RGpS_f672gN4'
CHAT_ID = '459970561'

start = datetime(2025, 1, 1)
today = datetime.today()
month_list = []
while start <= today:
    ym = f'{start.year}{str(start.month).zfill(2)}'
    month_list.append(ym)
    if start.month == 12:
        start = datetime(start.year + 1, 1, 1)
    else:
        start = datetime(start.year, start.month + 1, 1)

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, 'r') as f:
        seen = set(json.load(f))
else:
    seen = set()

new_alerts = []

for ym in month_list:
    print(f'📅 조회 중: {ym}')
    params = {
        'serviceKey': API_KEY,
        'LAWD_CD': LAWD_CD,
        'DEAL_YMD': ym,
        'pageNo': 1,
        'numOfRows': 1000
    }

    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f'❌ 요청 실패: {e}')
        continue

    try:
        root = ET.fromstring(res.text)
    except ET.ParseError:
        print("❌ XML 파싱 오류")
        print(res.text[:300])
        continue

    items = root.findall('.//item')
    for item in items:
        apt = item.findtext('아파트', '')
        dong = item.findtext('법정동', '')
        area = float(item.findtext('전용면적', '0'))
        floor = item.findtext('층', '')
        price = item.findtext('거래금액', '').strip().replace(',', '')
        y = item.findtext('년')
        m = item.findtext('월').zfill(2)
        d = item.findtext('일').zfill(2)
        date = f'{y}.{m}.{d}'

        if apt != '텐즈힐(1단지)':
            continue
        if dong != '하왕십리동':
            continue
        if not (83.0 <= area <= 85.0):
            continue

        uid = f'{date}_{apt}_{area}_{floor}'
        print(f'🎯 거래 발견: {apt} | {area}㎡ | {dong} | {date} | {floor}층 | {price}만원')

        if uid not in seen:
            message = (
                f'[텐즈힐 실거래가 알림]\n'
                f'계약일: {date}\n'
                f'면적: {area}㎡ / 층: {floor}층\n'
                f'거래가: {price}만원\n'
                f'위치: {dong}'
            )
            tg_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
            tg_res = requests.post(tg_url, data={'chat_id': CHAT_ID, 'text': message})

            if tg_res.status_code == 200:
                print('✅ 텔레그램 전송 성공')
            else:
                print('❌ 텔레그램 전송 실패:', tg_res.status_code)
                print('🔁 응답:', tg_res.text)

            seen.add(uid)
            new_alerts.append(uid)

if new_alerts:
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

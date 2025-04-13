import requests
import xmltodict
import pandas as pd

# ✅ 설정값
service_key = 'DBL9/jevAhTCfpDi5RqbnF61jt1lxJGlxxUSW/7mv4GB9bDJk6F1V+2izfb51UFSFtAGXxQ89Xy89pk4VFOMuQ=='
LAWD_CD = '11200'
DEAL_YMD = '202503'
TELEGRAM_TOKEN = '7360228257:AAF9V2WcMmm6zP9SW4HPeh2RGpS_f672gN4'
CHAT_ID = '459970561'

# ✅ API 요청
url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
params = {
    'serviceKey': service_key,
    'LAWD_CD': LAWD_CD,
    'DEAL_YMD': DEAL_YMD,
    'numOfRows': '1000',
    'pageNo': '1'
}
response = requests.get(url, params=params)
data_dict = xmltodict.parse(response.text)

# ✅ 데이터 추출 및 필터링
if 'response' in data_dict and 'body' in data_dict['response'] and 'items' in data_dict['response']['body']:
    items = data_dict['response']['body']['items']
    if items and 'item' in items:
        item_data = items['item']
        df = pd.DataFrame(item_data if isinstance(item_data, list) else [item_data])
        df = df[df['umdNm'] == '하왕십리동'].copy()
        df['excluUseAr'] = df['excluUseAr'].astype(float)

        filtered_df = df[
            (df['aptNm'] == '텐즈힐(1단지)') &
            (df['excluUseAr'] >= 83.0) &
            (df['excluUseAr'] <= 85.99)
        ].copy()

        if not filtered_df.empty:
            filtered_df['거래금액(만원)'] = filtered_df['dealAmount'].str.replace(',', '').astype(int)
            for _, row in filtered_df.iterrows():
                message = (
                    f"[텐즈힐 실거래가 알림]\n"
                    f"📅 {row['dealYear']}.{row['dealMonth']}.{row['dealDay']}\n"
                    f"🏢 {row['aptNm']} | {row['excluUseAr']}㎡ | {row['floor']}층\n"
                    f"💰 {row['거래금액(만원)']}만원"
                )
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': CHAT_ID, 'text': message})
        else:
            print("🔍 조건에 맞는 거래 없음")
    else:
        print("❌ item 없음")
else:
    print("❌ API 응답 이상")

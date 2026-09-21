import streamlit as st
import requests
import urllib3
import pandas as pd

st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🌿", layout="wide")

# CWA 在部分雲端 Python/OpenSSL 環境會遇到憑證鏈相容問題。
# 正常驗證失敗時，僅針對固定的中央氣象署官方網域使用相容模式重試。
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 12% 0%, rgba(169,195,171,.24), transparent 24%),
                linear-gradient(180deg,#f1f7ef 0%,#f7fbf6 34%,#f6faf5 100%);
    color:#34443a;
}
.block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
.hero {
    background:linear-gradient(135deg,#94b392,#7ea07e 58%,#b7cfb6);
    border-radius:28px;padding:30px 34px;color:white;margin-bottom:22px;
    box-shadow:0 14px 34px rgba(90,120,90,.10);
}
.hero-title {font-family:Georgia,"Noto Serif TC",serif;font-size:38px;font-weight:700;margin:0 0 8px 0;}
.hero-kicker {font-size:12px;letter-spacing:1.6px;opacity:.88;margin-bottom:7px;}
.hero-text {font-size:15px;line-height:1.8;opacity:.95;max-width:760px;}
[data-testid="stMetric"] {background:rgba(255,255,255,.92);border:1px solid #dce7db;border-radius:18px;padding:16px;box-shadow:0 10px 24px rgba(90,120,90,.07);}
.weather-card {background:rgba(255,255,255,.9);border:1px solid #dce7db;border-radius:20px;padding:22px;text-align:center;min-height:245px;}
.weather-icon {font-size:58px;margin:8px 0;}
.weather-temp {font-size:34px;font-weight:800;color:#405a45;}
.weather-desc {font-size:17px;font-weight:700;color:#5d745f;margin-top:6px;}
.source-box {margin-top:18px;padding:12px 14px;background:#f2f7f0;border:1px solid #dce7db;border-radius:14px;color:#627865;font-size:13px;line-height:1.7;}
.stButton > button {border-radius:14px;background:#6f9272;color:white;border:none;font-weight:700;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">CWA OPEN DATA × STREAMLIT × SECRET MANAGEMENT</div>
  <div class="hero-title">🌿 Taiwan Weather Forecast</div>
  <div class="hero-text">淡綠色文青風的一週天氣預報。資料直接由中央氣象署 Open Data 取得，API Key 使用 Streamlit Secrets 管理，不會寫在 GitHub 程式碼中。</div>
</div>
""", unsafe_allow_html=True)

API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
DATASET_ID = "F-D0047-091"

try:
    API_KEY = st.secrets["CWA_API_KEY"]
except Exception:
    st.error("尚未設定 CWA_API_KEY。請到 Streamlit Cloud → App settings → Secrets 設定。")
    st.stop()

REGIONS = [
    "臺北市","新北市","基隆市","桃園市","新竹市","新竹縣","苗栗縣","臺中市",
    "彰化縣","南投縣","雲林縣","嘉義市","嘉義縣","臺南市","高雄市","屏東縣",
    "宜蘭縣","花蓮縣","臺東縣","澎湖縣","金門縣","連江縣"
]


def icon_for(wx):
    wx = str(wx or "")
    if "雷" in wx: return "⛈️"
    if "雨" in wx: return "🌦️"
    if "陰" in wx: return "☁️"
    if "多雲" in wx: return "⛅"
    if "晴" in wx: return "☀️"
    return "🌿"


def norm_name(s):
    return str(s or "").replace("台", "臺")


def extract_locations(payload):
    """兼容 CWA REST 舊/新版大小寫與 rawData 結構。"""
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            name = obj.get("locationName") or obj.get("LocationName")
            elements = obj.get("weatherElement") or obj.get("WeatherElement")
            if name and elements:
                found.append(obj)
                return
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(payload)
    return found


def element_kind(el):
    name = str(el.get("elementName") or el.get("ElementName") or "")
    desc = str(el.get("description") or el.get("Description") or "")
    text = name + " " + desc
    low = text.lower()
    if name == "MaxT" or "最高溫" in text or "maxt" in low or "maximum" in low:
        return "max"
    if name == "MinT" or "最低溫" in text or "mint" in low or "minimum" in low:
        return "min"
    if name == "Wx" or "天氣現象" in text or "weather" in low:
        return "wx"
    return None


def first_element_value(item):
    ev = item.get("elementValue", item.get("ElementValue", {}))
    if isinstance(ev, list):
        ev = ev[0] if ev else {}
    if not isinstance(ev, dict):
        return None
    for key in [
        "value", "Value", "MaxTemperature", "MinTemperature", "Temperature",
        "Weather", "weather", "weatherDescription", "WeatherDescription"
    ]:
        if key in ev and ev[key] not in (None, ""):
            return ev[key]
    for value in ev.values():
        if value not in (None, ""):
            return value
    return None


def daily_forecast(location):
    elements = location.get("weatherElement") or location.get("WeatherElement") or []
    if isinstance(elements, dict):
        elements = [elements]
    days = {}

    for el in elements:
        if not isinstance(el, dict):
            continue
        kind = element_kind(el)
        if not kind:
            continue
        times = el.get("time") or el.get("Time") or []
        if isinstance(times, dict):
            times = [times]
        for item in times:
            if not isinstance(item, dict):
                continue
            start = item.get("startTime") or item.get("StartTime") or item.get("dataTime") or item.get("DataTime")
            day = str(start or "")[:10]
            if not day:
                continue
            days.setdefault(day, {"日期": day, "最高溫": [], "最低溫": [], "天氣": []})
            value = first_element_value(item)
            if kind in ("max", "min"):
                try:
                    number = float(value)
                    days[day]["最高溫" if kind == "max" else "最低溫"].append(number)
                except (TypeError, ValueError):
                    pass
            elif kind == "wx" and value not in (None, ""):
                days[day]["天氣"].append(str(value))

    result = []
    for day in sorted(days)[:7]:
        d = days[day]
        result.append({
            "日期": day,
            "最低溫": min(d["最低溫"]) if d["最低溫"] else None,
            "最高溫": max(d["最高溫"]) if d["最高溫"] else None,
            "天氣": d["天氣"][0] if d["天氣"] else "—",
        })
    return result


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(region):
    # 2024/12/10 起，F-D0047 系列查詢參數大小寫已改為 LocationName / ElementName。
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
        "LocationName": region,
        "ElementName": "最高溫度,最低溫度,天氣現象",
    }
    headers = {"User-Agent": "Mozilla/5.0 TaiwanWeatherForecast/3.0"}

    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    except requests.exceptions.SSLError:
        r = requests.get(API_URL, params=params, headers=headers, timeout=30, verify=False)

    if not r.ok and r.status_code not in (401, 403, 404):
        try:
            r2 = requests.get(API_URL, params=params, headers=headers, timeout=30, verify=False)
            if r2.ok:
                r = r2
        except Exception:
            pass

    if r.status_code in (401, 403):
        raise RuntimeError("CWA API Key 驗證失敗")
    if r.status_code == 404:
        raise RuntimeError(f"CWA 資料集 {DATASET_ID} HTTP 404")
    r.raise_for_status()

    payload = r.json()
    if str(payload.get("success", "true")).lower() == "false":
        raise RuntimeError("CWA API 回傳 success=false")

    locations = extract_locations(payload)
    if not locations:
        raise RuntimeError("CWA API 已回應，但找不到 Location/WeatherElement 資料")

    wanted = norm_name(region)
    exact = [x for x in locations if norm_name(x.get("locationName") or x.get("LocationName")) == wanted]
    if not exact:
        available = [norm_name(x.get("locationName") or x.get("LocationName")) for x in locations]
        raise RuntimeError(f"API 有資料，但找不到 {region}（回傳地區數：{len(available)}）")
    return exact[0]


region = st.selectbox("選擇縣市", REGIONS, index=REGIONS.index("彰化縣"))

left, right = st.columns([4, 1])
with left:
    st.caption(f"資料來源：中央氣象署 CWA Open Data｜資料集 {DATASET_ID}")
with right:
    if st.button("↻ 重新抓取資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    location = fetch_weather(region)
    forecast = daily_forecast(location)
    if not forecast:
        raise RuntimeError("API 連線成功，但無法解析最高溫度 / 最低溫度 / 天氣現象")
except Exception as exc:
    st.error(f"目前無法取得中央氣象署資料：{str(exc)}")
    st.stop()

max_values = [x["最高溫"] for x in forecast if x["最高溫"] is not None]
min_values = [x["最低溫"] for x in forecast if x["最低溫"] is not None]
diffs = [x["最高溫"] - x["最低溫"] for x in forecast if x["最高溫"] is not None and x["最低溫"] is not None]

m1, m2, m3, m4 = st.columns(4)
m1.metric("目前地區", region)
m2.metric("本週最高溫", f"{max(max_values):.0f} °C" if max_values else "—")
m3.metric("本週最低溫", f"{min(min_values):.0f} °C" if min_values else "—")
m4.metric("平均日溫差", f"{sum(diffs)/len(diffs):.1f} °C" if diffs else "—")

left, right = st.columns([2, 1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("未來一週溫度趨勢")
        chart_df = pd.DataFrame(
            [{"日期": x["日期"][5:].replace("-", "/"), "最高溫": x["最高溫"], "最低溫": x["最低溫"]} for x in forecast]
        ).set_index("日期")
        st.line_chart(chart_df, height=330)

with right:
    today = forecast[0]
    icon = icon_for(today["天氣"])
    temp_text = f'{today["最低溫"]:.0f}–{today["最高溫"]:.0f}°C' if today["最低溫"] is not None and today["最高溫"] is not None else "—"
    st.markdown(f"""
    <div class="weather-card">
      <div style="font-family:Georgia,serif;font-size:20px;font-weight:700;color:#425645;">今日概況</div>
      <div class="weather-icon">{icon}</div>
      <div class="weather-temp">{temp_text}</div>
      <div class="weather-desc">{today["天氣"]}</div>
      <div class="source-box"><b>資料集：</b>{DATASET_ID}<br><b>縣市：</b>{region}<br><b>狀態：</b>CWA 即時資料</div>
    </div>
    """, unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("每日預報資料")
    table_rows = []
    for row in forecast:
        table_rows.append({
            "日期": row["日期"],
            "縣市": region,
            "最低溫": f'{row["最低溫"]:.0f} °C' if row["最低溫"] is not None else "—",
            "最高溫": f'{row["最高溫"]:.0f} °C' if row["最高溫"] is not None else "—",
            "天氣": row["天氣"],
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)
import streamlit as st
import requests
import urllib3

st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🌿", layout="wide")

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

API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-005"

try:
    API_KEY = st.secrets["CWA_API_KEY"]
except Exception:
    st.error("尚未設定 CWA_API_KEY。請到 Streamlit Cloud → App settings → Secrets 設定。")
    st.stop()

REGION_ORDER = [
    "臺北市","新北市","基隆市","桃園市","新竹市","新竹縣","苗栗縣","臺中市",
    "彰化縣","南投縣","雲林縣","嘉義市","嘉義縣","臺南市","高雄市","屏東縣",
    "宜蘭縣","花蓮縣","臺東縣","澎湖縣","金門縣","連江縣"
]


def icon_for(wx):
    if "雷" in wx: return "⛈️"
    if "雨" in wx: return "🌦️"
    if "陰" in wx: return "☁️"
    if "多雲" in wx: return "⛅"
    if "晴" in wx: return "☀️"
    return "🌿"


def get_locations(payload):
    records = payload.get("records", {})
    if isinstance(records.get("location"), list):
        return records["location"]
    locations_obj = records.get("locations", {})
    if isinstance(locations_obj, dict) and isinstance(locations_obj.get("location"), list):
        return locations_obj["location"]
    cwa = payload.get("cwaopendata", {})
    dataset = cwa.get("dataset", {}) if isinstance(cwa, dict) else {}
    if isinstance(dataset.get("location"), list):
        return dataset["location"]
    locations_obj = dataset.get("locations", {}) if isinstance(dataset, dict) else {}
    if isinstance(locations_obj, dict) and isinstance(locations_obj.get("location"), list):
        return locations_obj["location"]
    return []


def weather_element_name(el):
    return el.get("elementName") or el.get("ElementName") or ""


def time_items(el):
    return el.get("time") or el.get("Time") or []


def start_time(item):
    return item.get("startTime") or item.get("StartTime") or item.get("dataTime") or item.get("DataTime") or ""


def element_value(item):
    v = item.get("elementValue", item.get("ElementValue", {}))
    if isinstance(v, list):
        return v[0] if v else {}
    return v if isinstance(v, dict) else {}


def parameter_value(item):
    v = item.get("parameter", item.get("Parameter", {}))
    return v if isinstance(v, dict) else {}


def kind_of(name):
    n = str(name)
    low = n.lower()
    if n == "Wx" or "天氣" in n or "weather" in low: return "wx"
    if n == "MaxT" or "最高" in n or "max" in low: return "max"
    if n == "MinT" or "最低" in n or "min" in low: return "min"
    return None


def read_value(item, kind):
    ev = element_value(item)
    p = parameter_value(item)
    if kind == "wx":
        return ev.get("Weather") or ev.get("weather") or ev.get("weatherDescription") or p.get("parameterName") or p.get("ParameterName") or ""
    return ev.get("MaxTemperature") or ev.get("MinTemperature") or ev.get("Temperature") or ev.get("temperature") or p.get("parameterName") or p.get("ParameterName") or ""


def daily_forecast(location):
    elements = location.get("weatherElement") or location.get("WeatherElement") or []
    days = {}
    for el in elements:
        kind = kind_of(weather_element_name(el))
        if not kind:
            continue
        for item in time_items(el):
            day = str(start_time(item))[:10]
            if not day:
                continue
            days.setdefault(day, {"日期": day, "最高溫": [], "最低溫": [], "天氣": []})
            value = read_value(item, kind)
            if kind in ("max", "min"):
                try:
                    num = float(value)
                    days[day]["最高溫" if kind == "max" else "最低溫"].append(num)
                except (TypeError, ValueError):
                    pass
            elif value:
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
def fetch_weather():
    params = {"Authorization": API_KEY, "format": "JSON"}
    headers = {"User-Agent": "Mozilla/5.0 TaiwanWeatherForecast/1.0"}

    # 先做正常 TLS 驗證；若 CWA 的憑證鏈在雲端環境被 OpenSSL 拒絕，
    # 僅針對固定的官方 CWA 網域重試一次相容模式。
    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=25)
        r.raise_for_status()
        return r.json(), False
    except requests.exceptions.SSLError:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(API_URL, params=params, headers=headers, timeout=25, verify=False)
        r.raise_for_status()
        return r.json(), True


left, right = st.columns([4, 1])
with left:
    st.caption("資料來源：中央氣象署 CWA Open Data")
with right:
    if st.button("↻ 重新抓取資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    payload, compatibility_mode = fetch_weather()
    if str(payload.get("success", "true")).lower() == "false":
        raise RuntimeError("CWA API 回傳 success=false")
    locations = get_locations(payload)
    if not locations:
        raise RuntimeError("API 已回應，但找不到縣市資料")
except Exception:
    # 不把 requests 原始錯誤直接顯示，避免 URL 中的 Authorization 洩漏 API Key。
    st.error("目前無法取得中央氣象署資料。請確認 Streamlit Secrets 中的 CWA_API_KEY 正確，然後按『重新抓取資料』。")
    st.stop()

if compatibility_mode:
    st.info("目前使用 CWA SSL 相容模式取得資料。API Key 仍只存在 Streamlit Secrets，不會寫入 GitHub。")

location_map = {
    (loc.get("locationName") or loc.get("LocationName")): loc
    for loc in locations
    if (loc.get("locationName") or loc.get("LocationName"))
}

ordered = [r for r in REGION_ORDER if r in location_map] + [r for r in location_map if r not in REGION_ORDER]
if not ordered:
    st.error("找不到可顯示的縣市資料。")
    st.stop()

default_index = ordered.index("彰化縣") if "彰化縣" in ordered else 0
region = st.selectbox("選擇縣市", ordered, index=default_index)
forecast = daily_forecast(location_map[region])

if not forecast:
    st.warning("此縣市目前沒有可顯示的一週溫度資料。")
    st.stop()

max_values = [x["最高溫"] for x in forecast if x["最高溫"] is not None]
min_values = [x["最低溫"] for x in forecast if x["最低溫"] is not None]
diffs = [x["最高溫"] - x["最低溫"] for x in forecast if x["最高溫"] is not None and x["最低溫"] is not None]

m1, m2, m3, m4 = st.columns(4)
m1.metric("目前地區", region)
m2.metric("本週最高溫", f"{max(max_values):.0f} °C" if max_values else "—")
m3.metric("本週最低溫", f"{min(min_values):.0f} °C" if min_values else "—")
m4.metric("平均日溫差", f"{sum(diffs)/len(diffs):.1f} °C" if diffs else "—")

left, right = st.columns([2,1], gap="large")
with left:
    with st.container(border=True):
        st.subheader("未來一週溫度趨勢")
        chart_data = {
            row["日期"][5:].replace("-", "/"): {"最高溫": row["最高溫"], "最低溫": row["最低溫"]}
            for row in forecast
        }
        st.line_chart(chart_data, height=330)

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
      <div class="source-box"><b>資料集：</b>F-C0032-005<br><b>縣市：</b>{region}<br><b>狀態：</b>CWA 即時資料</div>
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

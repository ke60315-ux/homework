import streamlit as st
import requests
import urllib3

st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🌿", layout="wide")

# CWA 在部分雲端 Python/OpenSSL 環境會遇到憑證鏈相容問題。
# 這裡只針對固定的中央氣象署官方 API 網域使用相容模式。
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
.hero-text {font-size:15px;line-height:1.8;opacity:.95;max-width:800px;}
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
    API_KEY = str(st.secrets["CWA_API_KEY"]).strip()
except Exception:
    st.error("尚未設定 CWA_API_KEY。請到 Streamlit Cloud → App settings → Secrets 設定。")
    st.stop()

if not API_KEY:
    st.error("CWA_API_KEY 是空白的，請重新設定 Streamlit Secrets。")
    st.stop()

REGION_ORDER = [
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


def _collect_locations(container, output):
    """支援 CWA REST API 新舊兩種 records.locations 結構。"""
    if isinstance(container, dict):
        direct = container.get("location")
        if isinstance(direct, list):
            output.extend(x for x in direct if isinstance(x, dict))

        nested = container.get("locations")
        if isinstance(nested, list):
            for group in nested:
                _collect_locations(group, output)
        elif isinstance(nested, dict):
            _collect_locations(nested, output)
    elif isinstance(container, list):
        for item in container:
            _collect_locations(item, output)


def get_locations(payload):
    output = []
    if not isinstance(payload, dict):
        return output

    _collect_locations(payload.get("records", {}), output)

    cwa = payload.get("cwaopendata", {})
    if isinstance(cwa, dict):
        _collect_locations(cwa.get("dataset", {}), output)

    # 依縣市名稱去重
    result = {}
    for loc in output:
        name = loc.get("locationName") or loc.get("LocationName")
        if name and name not in result:
            result[name] = loc
    return list(result.values())


def weather_element_name(el):
    return el.get("elementName") or el.get("ElementName") or ""


def time_items(el):
    value = el.get("time") or el.get("Time") or []
    return value if isinstance(value, list) else []


def start_time(item):
    return item.get("startTime") or item.get("StartTime") or item.get("dataTime") or item.get("DataTime") or ""


def kind_of(name):
    n = str(name)
    low = n.lower()
    if n == "Wx" or "天氣" in n or "weather" in low: return "wx"
    if n == "MaxT" or "最高" in n or "max" in low: return "max"
    if n == "MinT" or "最低" in n or "min" in low: return "min"
    return None


def candidate_values(item):
    """F-C0032-005 常用 elementValue.value；舊格式則可能用 parameterName。"""
    values = []

    ev = item.get("elementValue", item.get("ElementValue"))
    if isinstance(ev, dict):
        ev = [ev]
    if isinstance(ev, list):
        for obj in ev:
            if not isinstance(obj, dict):
                continue
            for key in (
                "value", "Value", "Weather", "weather", "weatherDescription",
                "MaxTemperature", "MinTemperature", "Temperature", "temperature"
            ):
                value = obj.get(key)
                if value not in (None, ""):
                    values.append(value)

    param = item.get("parameter", item.get("Parameter"))
    if isinstance(param, dict):
        param = [param]
    if isinstance(param, list):
        for obj in param:
            if not isinstance(obj, dict):
                continue
            for key in ("parameterName", "ParameterName", "value", "Value"):
                value = obj.get(key)
                if value not in (None, ""):
                    values.append(value)

    return values


def read_value(item, kind):
    values = candidate_values(item)
    if not values:
        return ""

    if kind in ("max", "min"):
        for value in values:
            try:
                return float(str(value).strip())
            except (TypeError, ValueError):
                pass
        return ""

    # Wx 有時同時含「天氣文字」與「天氣代碼」，優先取非純數字內容。
    for value in values:
        text = str(value).strip()
        if text and not text.replace(".", "", 1).isdigit():
            return text
    return str(values[0]).strip()


def daily_forecast(location):
    elements = location.get("weatherElement") or location.get("WeatherElement") or []
    if not isinstance(elements, list):
        return []

    days = {}
    for el in elements:
        if not isinstance(el, dict):
            continue
        kind = kind_of(weather_element_name(el))
        if not kind:
            continue

        for item in time_items(el):
            if not isinstance(item, dict):
                continue
            raw_time = start_time(item)
            day = str(raw_time)[:10] if raw_time else ""
            if not day:
                continue

            days.setdefault(day, {"日期": day, "最高溫": [], "最低溫": [], "天氣": []})
            value = read_value(item, kind)

            if kind == "max" and isinstance(value, (int, float)):
                days[day]["最高溫"].append(float(value))
            elif kind == "min" and isinstance(value, (int, float)):
                days[day]["最低溫"].append(float(value))
            elif kind == "wx" and value:
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
    # CWA 官方文件支援把 Authorization 放在 HTTP header。
    # 這樣 API Key 不會出現在網址與 requests 錯誤訊息中。
    headers = {
        "Authorization": API_KEY,
        "Accept": "application/json",
        "User-Agent": "TaiwanWeatherForecast/1.0",
    }

    try:
        response = requests.get(
            API_URL,
            params={"format": "JSON"},
            headers=headers,
            timeout=30,
            verify=False,
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("連線 CWA 逾時")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("無法連線 CWA 主機")
    except requests.exceptions.RequestException:
        raise RuntimeError("CWA 網路連線失敗")

    if response.status_code in (401, 403):
        raise RuntimeError("CWA API Key 驗證失敗")
    if response.status_code != 200:
        raise RuntimeError(f"CWA API HTTP {response.status_code}")

    try:
        payload = response.json()
    except ValueError:
        raise RuntimeError("CWA 回應不是 JSON")

    if not isinstance(payload, dict):
        raise RuntimeError("CWA JSON 格式異常")

    if str(payload.get("success", "true")).lower() == "false":
        result = payload.get("result", {})
        message = ""
        if isinstance(result, dict):
            message = str(result.get("message") or "").strip()
        raise RuntimeError("CWA API 回傳失敗" + (f"：{message[:80]}" if message else ""))

    return payload


left, right = st.columns([4, 1])
with left:
    st.caption("資料來源：中央氣象署 CWA Open Data · F-C0032-005")
with right:
    if st.button("↻ 重新抓取資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    payload = fetch_weather()
    locations = get_locations(payload)
except RuntimeError as exc:
    st.error(f"目前無法取得中央氣象署資料：{exc}")
    st.caption("API Key 不會顯示在錯誤訊息或網址中。")
    st.stop()
except Exception:
    st.error("目前無法取得中央氣象署資料：發生未預期錯誤")
    st.stop()

if not locations:
    records = payload.get("records", {}) if isinstance(payload, dict) else {}
    locations_type = type(records.get("locations")).__name__ if isinstance(records, dict) else "unknown"
    st.error("CWA API 已成功連線，但目前程式找不到縣市資料。")
    st.caption(f"診斷資訊：records.locations type = {locations_type}")
    st.stop()

location_map = {
    (loc.get("locationName") or loc.get("LocationName")): loc
    for loc in locations
    if (loc.get("locationName") or loc.get("LocationName"))
}

ordered = [r for r in REGION_ORDER if r in location_map] + [r for r in location_map if r not in REGION_ORDER]
if not ordered:
    st.error("API 已連線，但沒有可顯示的縣市名稱。")
    st.stop()

default_index = ordered.index("彰化縣") if "彰化縣" in ordered else 0
region = st.selectbox("選擇縣市", ordered, index=default_index)
forecast = daily_forecast(location_map[region])

if not forecast:
    element_names = [weather_element_name(e) for e in (location_map[region].get("weatherElement") or []) if isinstance(e, dict)]
    st.error("CWA API 已連線，但預報欄位解析失敗。")
    st.caption("收到的 weatherElement：" + ", ".join(element_names[:10]))
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
      <div class="source-box"><b>資料集：</b>F-C0032-005<br><b>縣市：</b>{region}<br><b>狀態：</b>CWA API 已連線</div>
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

st.caption("🌿 Taiwan Weather Forecast · Data provided by Central Weather Administration")

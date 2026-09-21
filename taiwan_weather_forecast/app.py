import copy

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
import urllib3

st.set_page_config(
    page_title="Taiwan Weather Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -----------------------------------------------------------------------------
# Cyber / GIS theme
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --bg:#050b14;
    --panel:#091525;
    --panel2:#0c1c2e;
    --cyan:#00e5ff;
    --blue:#3d7bff;
    --violet:#8b5cf6;
    --text:#e6f7ff;
    --muted:#7895a8;
    --line:rgba(0,229,255,.22);
}
.stApp {
    background:
      radial-gradient(circle at 10% -10%, rgba(0,229,255,.16), transparent 28%),
      radial-gradient(circle at 90% 0%, rgba(139,92,246,.12), transparent 26%),
      linear-gradient(180deg,#030812 0%,#07111d 50%,#030812 100%);
    color:var(--text);
}
.block-container {max-width:1280px;padding-top:1.2rem;padding-bottom:3rem;}
[data-testid="stHeader"] {background:rgba(3,8,18,.65);backdrop-filter:blur(10px);}

.cyber-hero {
    position:relative;
    overflow:hidden;
    padding:30px 34px;
    border:1px solid rgba(0,229,255,.25);
    border-radius:22px;
    background:linear-gradient(135deg,rgba(7,24,42,.96),rgba(7,17,31,.96));
    box-shadow:0 0 0 1px rgba(61,123,255,.08),0 22px 60px rgba(0,0,0,.32),inset 0 0 50px rgba(0,229,255,.035);
    margin-bottom:18px;
}
.cyber-hero:after {
    content:"";position:absolute;inset:0;pointer-events:none;
    background-image:linear-gradient(rgba(0,229,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,.035) 1px,transparent 1px);
    background-size:28px 28px;
}
.kicker {font:700 12px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:2px;color:var(--cyan);}
.hero-title {font-size:40px;font-weight:800;letter-spacing:-1px;color:#f3fbff;margin:8px 0 6px;}
.hero-sub {max-width:840px;color:#9bb5c6;font-size:15px;line-height:1.8;}
.live-badge {display:inline-flex;align-items:center;gap:8px;margin-top:14px;padding:7px 11px;border:1px solid rgba(0,229,255,.28);border-radius:999px;background:rgba(0,229,255,.06);color:#9cf5ff;font:700 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1px;}
.live-dot {width:7px;height:7px;border-radius:50%;background:#00ffa8;box-shadow:0 0 12px #00ffa8;}

.section-label {margin:8px 0 8px;color:#8ba7ba;font:700 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.5px;text-transform:uppercase;}
.panel-title {font-size:20px;font-weight:800;color:#eafaff;margin-bottom:2px;}
.panel-sub {color:#6f91a8;font-size:13px;margin-bottom:12px;}

[data-testid="stMetric"] {
    background:linear-gradient(180deg,rgba(12,28,46,.95),rgba(7,19,33,.95));
    border:1px solid rgba(0,229,255,.18);
    border-radius:16px;
    padding:16px 17px;
    box-shadow:inset 0 0 26px rgba(0,229,255,.025),0 12px 28px rgba(0,0,0,.16);
}
[data-testid="stMetricLabel"] {color:#7395aa;}
[data-testid="stMetricValue"] {color:#e9fbff;}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border:1px solid rgba(0,229,255,.16)!important;
    border-radius:18px!important;
    background:linear-gradient(180deg,rgba(9,21,37,.92),rgba(6,15,27,.94));
    box-shadow:0 14px 34px rgba(0,0,0,.18),inset 0 0 36px rgba(0,229,255,.018);
}

[data-baseweb="select"] > div {
    background:#091827!important;
    border-color:rgba(0,229,255,.28)!important;
    color:#e6f7ff!important;
    border-radius:12px!important;
}
.stButton > button {
    width:100%;border-radius:11px;border:1px solid rgba(0,229,255,.32);
    background:linear-gradient(135deg,rgba(0,229,255,.12),rgba(61,123,255,.16));
    color:#dffbff;font-weight:750;
}
.stButton > button:hover {border-color:#00e5ff;color:white;box-shadow:0 0 18px rgba(0,229,255,.18);}

.weather-card {
    min-height:280px;padding:22px;border-radius:16px;text-align:center;
    background:radial-gradient(circle at 50% 0%,rgba(0,229,255,.12),transparent 42%),linear-gradient(180deg,#0a1a2b,#07121f);
    border:1px solid rgba(0,229,255,.2);
}
.weather-icon {font-size:62px;filter:drop-shadow(0 0 14px rgba(0,229,255,.28));margin:8px 0;}
.weather-temp {font:800 38px/1.1 ui-monospace,SFMono-Regular,Menlo,monospace;color:#eaffff;}
.weather-desc {font-size:16px;font-weight:750;color:#9ddbe6;margin-top:9px;}
.source-box {margin-top:18px;padding:11px 13px;border-radius:10px;border:1px solid rgba(0,229,255,.16);background:rgba(0,229,255,.035);color:#7898ad;font:12px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;}

hr {border-color:rgba(0,229,255,.12)!important;}
h1,h2,h3 {color:#eafaff!important;}
[data-testid="stDataFrame"] {border:1px solid rgba(0,229,255,.15);border-radius:12px;overflow:hidden;}
.small-tech {color:#68879b;font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="cyber-hero">
  <div class="kicker">TAIWAN // CWA OPEN DATA // GIS WEATHER INTELLIGENCE</div>
  <div class="hero-title">🛰️ Taiwan Weather Intelligence</div>
  <div class="hero-sub">全台 22 縣市一週天氣 × GIS 行政區域視覺化。選擇縣市後，地圖會聚焦並高亮該區域，同步載入中央氣象署即時預報資料。</div>
  <div class="live-badge"><span class="live-dot"></span> LIVE DATA PIPELINE</div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data sources
# -----------------------------------------------------------------------------
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
DATASET_ID = "F-D0047-091"
GEOJSON_URL = "https://raw.githubusercontent.com/ronnywang/twgeojson/refs/heads/master/twcounty2010.2.json"

try:
    API_KEY = st.secrets["CWA_API_KEY"]
except Exception:
    st.error("尚未設定 CWA_API_KEY。請到 Streamlit Cloud → App settings → Secrets 設定。")
    st.stop()

REGIONS = [
    "臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣", "臺中市",
    "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市", "高雄市", "屏東縣",
    "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
]

CENTROIDS = {
    "臺北市": (25.0375, 121.5637), "新北市": (25.0169, 121.4628), "基隆市": (25.1283, 121.7419),
    "桃園市": (24.9937, 121.3010), "新竹市": (24.8138, 120.9675), "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214), "臺中市": (24.1477, 120.6736), "彰化縣": (24.0756, 120.5440),
    "南投縣": (23.9609, 120.9719), "雲林縣": (23.7092, 120.4313), "嘉義市": (23.4801, 120.4491),
    "嘉義縣": (23.4518, 120.2555), "臺南市": (22.9999, 120.2269), "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.5519, 120.5488), "宜蘭縣": (24.7021, 121.7378), "花蓮縣": (23.9911, 121.6112),
    "臺東縣": (22.7554, 121.1500), "澎湖縣": (23.5712, 119.5793), "金門縣": (24.4494, 118.3767),
    "連江縣": (26.1602, 119.9517),
}


def norm_name(value):
    return str(value or "").replace("台", "臺").strip()


def icon_for(wx):
    wx = str(wx or "")
    if "雷" in wx:
        return "⛈️"
    if "雨" in wx:
        return "🌦️"
    if "陰" in wx:
        return "☁️"
    if "多雲" in wx:
        return "⛅"
    if "晴" in wx:
        return "☀️"
    return "🛰️"


def extract_locations(payload):
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
    text = f"{name} {desc}"
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
        "Weather", "weather", "weatherDescription", "WeatherDescription",
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
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
        "LocationName": region,
        "ElementName": "最高溫度,最低溫度,天氣現象",
    }
    headers = {"User-Agent": "Mozilla/5.0 TaiwanWeatherIntelligence/4.0"}

    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    except requests.exceptions.SSLError:
        try:
            r = requests.get(API_URL, params=params, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException:
            raise RuntimeError("無法連線至 CWA API")
    except requests.exceptions.Timeout:
        raise RuntimeError("CWA API 連線逾時")
    except requests.exceptions.RequestException:
        raise RuntimeError("無法連線至 CWA API")

    if r.status_code in (401, 403):
        raise RuntimeError("CWA API Key 驗證失敗")
    if r.status_code == 404:
        raise RuntimeError(f"CWA 資料集 {DATASET_ID} HTTP 404")
    if not r.ok:
        raise RuntimeError(f"CWA API HTTP {r.status_code}")

    try:
        payload = r.json()
    except ValueError:
        raise RuntimeError("CWA API 回傳格式不是 JSON")

    if str(payload.get("success", "true")).lower() == "false":
        raise RuntimeError("CWA API 回傳 success=false")

    locations = extract_locations(payload)
    wanted = norm_name(region)
    exact = [x for x in locations if norm_name(x.get("locationName") or x.get("LocationName")) == wanted]
    if not exact:
        raise RuntimeError(f"API 有回應，但找不到 {region} 的預報資料")
    return exact[0]


@st.cache_data(ttl=86400, show_spinner=False)
def load_county_geojson():
    headers = {"User-Agent": "Mozilla/5.0 TaiwanWeatherGIS/1.0"}
    try:
        r = requests.get(GEOJSON_URL, headers=headers, timeout=20)
        if not r.ok:
            return None
        return r.json()
    except Exception:
        return None


def geo_feature_name(properties):
    for key in ["COUNTYNAME", "COUNTY_NAM", "C_Name", "name", "COUNTY", "county"]:
        value = properties.get(key)
        if value:
            return norm_name(value)
    return ""


def build_gis(region):
    raw = load_county_geojson()
    selected = norm_name(region)
    layers = []

    if raw and isinstance(raw.get("features"), list):
        geo = copy.deepcopy(raw)
        for feature in geo["features"]:
            props = feature.setdefault("properties", {})
            display_name = geo_feature_name(props)
            is_selected = display_name == selected
            props["display_name"] = display_name or "行政區"
            props["fill_color"] = [0, 229, 255, 165] if is_selected else [20, 50, 78, 80]
            props["line_color"] = [114, 241, 255, 230] if is_selected else [54, 112, 145, 150]

        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                geo,
                pickable=True,
                stroked=True,
                filled=True,
                extruded=False,
                get_fill_color="properties.fill_color",
                get_line_color="properties.line_color",
                line_width_min_pixels=1,
            )
        )

    points = []
    for name, (lat, lon) in CENTROIDS.items():
        is_selected = name == region
        points.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "radius": 17000 if is_selected else 6500,
            "color": [0, 229, 255, 210] if is_selected else [61, 123, 255, 145],
        })

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            points,
            get_position="[lon, lat]",
            get_radius="radius",
            get_fill_color="color",
            get_line_color=[180, 250, 255, 220],
            line_width_min_pixels=1,
            stroked=True,
            pickable=True,
        )
    )

    lat, lon = CENTROIDS[region]
    view = pdk.ViewState(latitude=lat, longitude=lon, zoom=7.8, pitch=28, bearing=0)
    tooltip = {
        "html": "<b>{name}</b><br/><span style='color:#7ff5ff'>GIS weather node</span>",
        "style": {"backgroundColor": "#07131f", "color": "#e8fbff", "border": "1px solid #00e5ff"},
    }
    return pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip=tooltip,
    )


# -----------------------------------------------------------------------------
# Controls
# -----------------------------------------------------------------------------
if "region" not in st.session_state:
    st.session_state.region = "彰化縣"

st.markdown('<div class="section-label">01 // REGION CONTROL</div>', unsafe_allow_html=True)
quick1, quick2, spacer, refresh_col = st.columns([1, 1, 4, 1.4])
with quick1:
    st.button("⚡ 臺中市", on_click=lambda: st.session_state.update(region="臺中市"), use_container_width=True)
with quick2:
    st.button("⚡ 彰化縣", on_click=lambda: st.session_state.update(region="彰化縣"), use_container_width=True)
with refresh_col:
    if st.button("↻ 更新資料", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

region = st.selectbox(
    "全台 22 縣市",
    REGIONS,
    key="region",
    help="選擇任一縣市後，GIS 地圖與 CWA 預報會同步切換。",
)

# -----------------------------------------------------------------------------
# Fetch selected region weather
# -----------------------------------------------------------------------------
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
diffs = [
    x["最高溫"] - x["最低溫"]
    for x in forecast
    if x["最高溫"] is not None and x["最低溫"] is not None
]

st.markdown('<div class="section-label">02 // LIVE TELEMETRY</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("SELECTED ZONE", region)
m2.metric("WEEKLY MAX", f"{max(max_values):.0f} °C" if max_values else "—")
m3.metric("WEEKLY MIN", f"{min(min_values):.0f} °C" if min_values else "—")
m4.metric("AVG TEMP RANGE", f"{sum(diffs)/len(diffs):.1f} °C" if diffs else "—")

# -----------------------------------------------------------------------------
# GIS + current overview
# -----------------------------------------------------------------------------
st.markdown('<div class="section-label">03 // GIS SITUATIONAL MAP</div>', unsafe_allow_html=True)
map_col, today_col = st.columns([2.2, 1], gap="large")

with map_col:
    with st.container(border=True):
        st.markdown('<div class="panel-title">Taiwan County GIS</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel-sub">目前鎖定：{region}｜青色區域 / 節點為目前選取縣市</div>', unsafe_allow_html=True)
        st.pydeck_chart(build_gis(region), use_container_width=True, height=500)
        if load_county_geojson() is None:
            st.caption("行政區界線圖層暫時無法載入，目前改以縣市 GIS 節點顯示。")

with today_col:
    today = forecast[0]
    icon = icon_for(today["天氣"])
    temp_text = (
        f'{today["最低溫"]:.0f}–{today["最高溫"]:.0f}°C'
        if today["最低溫"] is not None and today["最高溫"] is not None
        else "—"
    )
    lat, lon = CENTROIDS[region]
    st.markdown(
        f"""
        <div class="weather-card">
          <div class="kicker">CURRENT ZONE // {region}</div>
          <div class="weather-icon">{icon}</div>
          <div class="weather-temp">{temp_text}</div>
          <div class="weather-desc">{today["天氣"]}</div>
          <div class="source-box">
            DATASET // {DATASET_ID}<br>
            GEO // {lat:.4f}, {lon:.4f}<br>
            STATUS // CWA LIVE<br>
            GIS // COUNTY LEVEL
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Forecast trend
# -----------------------------------------------------------------------------
st.markdown('<div class="section-label">04 // FORECAST ANALYTICS</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.markdown('<div class="panel-title">7-Day Temperature Signal</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">未來一週最高 / 最低溫趨勢</div>', unsafe_allow_html=True)
    chart_df = pd.DataFrame(
        [
            {"日期": x["日期"][5:].replace("-", "/"), "最高溫": x["最高溫"], "最低溫": x["最低溫"]}
            for x in forecast
        ]
    ).set_index("日期")
    st.line_chart(chart_df, height=330)

with st.container(border=True):
    st.markdown('<div class="panel-title">Forecast Data Stream</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">{region}｜中央氣象署未來一週預報</div>', unsafe_allow_html=True)
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

st.markdown(
    f'<div class="small-tech">SYSTEM // CWA {DATASET_ID} · 22 COUNTY/CITY SELECTOR · GIS COUNTY LAYER · API KEY VIA STREAMLIT SECRETS</div>',
    unsafe_allow_html=True,
)

import { NextResponse } from 'next/server';

const API_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091';
const DATASET_ID = 'F-D0047-091';

function normName(value) {
  return String(value || '').replaceAll('台', '臺');
}

function collectLocations(payload) {
  const found = [];
  function walk(obj) {
    if (Array.isArray(obj)) {
      obj.forEach(walk);
      return;
    }
    if (!obj || typeof obj !== 'object') return;

    const name = obj.locationName || obj.LocationName;
    const elements = obj.weatherElement || obj.WeatherElement;
    if (name && elements) {
      found.push(obj);
      return;
    }
    Object.values(obj).forEach(walk);
  }
  walk(payload);
  return found;
}

function elementKind(el) {
  const name = String(el.elementName || el.ElementName || '');
  const desc = String(el.description || el.Description || '');
  const text = `${name} ${desc}`;
  const low = text.toLowerCase();
  if (name === 'MaxT' || text.includes('最高溫') || low.includes('maxt') || low.includes('maximum')) return 'max';
  if (name === 'MinT' || text.includes('最低溫') || low.includes('mint') || low.includes('minimum')) return 'min';
  if (name === 'Wx' || text.includes('天氣現象') || low.includes('weather')) return 'wx';
  return null;
}

function firstElementValue(item) {
  let ev = item.elementValue ?? item.ElementValue ?? {};
  if (Array.isArray(ev)) ev = ev[0] ?? {};
  if (!ev || typeof ev !== 'object') return null;
  const keys = ['value','Value','MaxTemperature','MinTemperature','Temperature','Weather','weather','weatherDescription','WeatherDescription'];
  for (const key of keys) {
    if (ev[key] !== undefined && ev[key] !== null && ev[key] !== '') return ev[key];
  }
  for (const value of Object.values(ev)) {
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return null;
}

function dailyForecast(location) {
  let elements = location.weatherElement || location.WeatherElement || [];
  if (!Array.isArray(elements)) elements = [elements];
  const days = {};

  for (const el of elements) {
    if (!el || typeof el !== 'object') continue;
    const kind = elementKind(el);
    if (!kind) continue;
    let times = el.time || el.Time || [];
    if (!Array.isArray(times)) times = [times];

    for (const item of times) {
      if (!item || typeof item !== 'object') continue;
      const start = item.startTime || item.StartTime || item.dataTime || item.DataTime || '';
      const day = String(start).slice(0, 10);
      if (!day) continue;
      days[day] ||= { date: day, max: [], min: [], wx: [] };
      const value = firstElementValue(item);

      if (kind === 'max' || kind === 'min') {
        const num = Number(value);
        if (Number.isFinite(num)) days[day][kind].push(num);
      } else if (kind === 'wx' && value !== null && value !== '') {
        days[day].wx.push(String(value));
      }
    }
  }

  return Object.keys(days).sort().slice(0, 7).map((day) => {
    const d = days[day];
    return {
      date: d.date,
      min: d.min.length ? Math.min(...d.min) : null,
      max: d.max.length ? Math.max(...d.max) : null,
      weather: d.wx[0] || '—',
    };
  });
}

export async function GET(request) {
  try {
    const apiKey = process.env.CWA_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Vercel 尚未設定 CWA_API_KEY' }, { status: 500 });
    }

    const { searchParams } = new URL(request.url);
    const region = searchParams.get('region') || '彰化縣';

    const url = new URL(API_URL);
    url.searchParams.set('Authorization', apiKey);
    url.searchParams.set('format', 'JSON');
    url.searchParams.set('LocationName', region);
    url.searchParams.set('ElementName', '最高溫度,最低溫度,天氣現象');

    const response = await fetch(url, {
      cache: 'no-store',
      headers: { 'User-Agent': 'TaiwanWeatherIntelligence-Vercel/1.0' },
    });

    if (response.status === 401 || response.status === 403) {
      return NextResponse.json({ error: 'CWA API Key 驗證失敗' }, { status: 502 });
    }
    if (!response.ok) {
      return NextResponse.json({ error: `CWA API HTTP ${response.status}` }, { status: 502 });
    }

    const payload = await response.json();
    if (String(payload?.success ?? 'true').toLowerCase() === 'false') {
      return NextResponse.json({ error: 'CWA API 回傳 success=false' }, { status: 502 });
    }

    const locations = collectLocations(payload);
    const wanted = normName(region);
    const location = locations.find((item) => normName(item.locationName || item.LocationName) === wanted);
    if (!location) {
      return NextResponse.json({ error: `API 有回應，但找不到 ${region}` }, { status: 502 });
    }

    const forecast = dailyForecast(location);
    if (!forecast.length) {
      return NextResponse.json({ error: 'API 連線成功，但無法解析天氣資料' }, { status: 502 });
    }

    return NextResponse.json({
      dataset: DATASET_ID,
      region,
      forecast,
      updatedAt: new Date().toISOString(),
    }, { headers: { 'Cache-Control': 's-maxage=900, stale-while-revalidate=1800' } });
  } catch (error) {
    return NextResponse.json({ error: '無法連線中央氣象署 API' }, { status: 500 });
  }
}

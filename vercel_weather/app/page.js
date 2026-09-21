'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import TaiwanMap, { REGION_CENTERS } from '../components/TaiwanMap';

const REGIONS = Object.keys(REGION_CENTERS);

function iconFor(wx) {
  const text = String(wx || '');
  if (text.includes('雷')) return '⛈️';
  if (text.includes('雨')) return '🌧️';
  if (text.includes('陰')) return '☁️';
  if (text.includes('多雲')) return '⛅';
  if (text.includes('晴')) return '☀️';
  return '🛰️';
}

function TemperatureChart({ data }) {
  const valid = data.filter((d) => Number.isFinite(d.max) && Number.isFinite(d.min));
  if (!valid.length) return <div className="chart" />;

  const values = valid.flatMap((d) => [d.max, d.min]);
  const lo = Math.min(...values) - 1;
  const hi = Math.max(...values) + 1;
  const width = 620;
  const height = 180;
  const padX = 34;
  const padY = 24;
  const x = (i) => padX + (i * (width - padX * 2)) / Math.max(valid.length - 1, 1);
  const y = (v) => height - padY - ((v - lo) / Math.max(hi - lo, 1)) * (height - padY * 2);
  const path = (key) => valid.map((d, i) => `${i ? 'L' : 'M'} ${x(i)} ${y(d[key])}`).join(' ');

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="一週溫度趨勢">
      {[0.25, 0.5, 0.75].map((r) => (
        <line key={r} x1="20" x2="600" y1={height * r} y2={height * r} stroke="rgba(120,220,255,.10)" />
      ))}
      <path d={path('max')} fill="none" stroke="#39e7ff" strokeWidth="3" strokeLinecap="round" />
      <path d={path('min')} fill="none" stroke="#8b7cff" strokeWidth="3" strokeLinecap="round" />
      {valid.map((d, i) => (
        <g key={d.date}>
          <circle cx={x(i)} cy={y(d.max)} r="4" fill="#39e7ff" />
          <circle cx={x(i)} cy={y(d.min)} r="4" fill="#8b7cff" />
          <text x={x(i)} y={height - 7} textAnchor="middle" fill="#7198aa" fontSize="11">{d.date.slice(5)}</text>
        </g>
      ))}
    </svg>
  );
}

export default function Home() {
  const [region, setRegion] = useState('彰化縣');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadWeather = useCallback(async (name) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/weather?region=${encodeURIComponent(name)}`, { cache: 'no-store' });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || '資料取得失敗');
      setData(body);
    } catch (err) {
      setError(err.message || '資料取得失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadWeather(region); }, [region, loadWeather]);

  const stats = useMemo(() => {
    const forecast = data?.forecast || [];
    const highs = forecast.map((d) => d.max).filter(Number.isFinite);
    const lows = forecast.map((d) => d.min).filter(Number.isFinite);
    const ranges = forecast.filter((d) => Number.isFinite(d.max) && Number.isFinite(d.min)).map((d) => d.max - d.min);
    return {
      high: highs.length ? Math.max(...highs) : null,
      low: lows.length ? Math.min(...lows) : null,
      range: ranges.length ? ranges.reduce((a, b) => a + b, 0) / ranges.length : null,
    };
  }, [data]);

  const today = data?.forecast?.[0];
  const center = REGION_CENTERS[region];

  return (
    <main className="dashboard">
      <div className="topbar">
        <div>
          <div className="brand-kicker">TAIWAN // CWA OPEN DATA // GIS WEATHER INTELLIGENCE</div>
          <h1 className="brand-title">Taiwan Weather Intelligence</h1>
        </div>
        <div className="status-pill">● LIVE DATA / {data?.dataset || 'F-D0047-091'}</div>
      </div>

      <section className="hero">
        <div className="hero-grid">
          <div>
            <div className="brand-kicker">NATIONAL WEATHER COMMAND CENTER</div>
            <h2 style={{fontSize:'clamp(1.35rem,2.5vw,2rem)', margin:'8px 0'}}>全台 22 縣市 GIS 氣象監控</h2>
            <div className="hero-copy">直接串接中央氣象署一週預報，透過 Vercel Serverless API 保護 CWA API Key。可由下拉選單或 GIS 地圖直接切換臺中市、彰化縣與全台各縣市。</div>
          </div>
          <div className="control-box">
            <div className="control-label">SELECT REGION / 縣市選擇</div>
            <select value={region} onChange={(e) => setRegion(e.target.value)}>
              {REGIONS.map((name) => <option key={name}>{name}</option>)}
            </select>
            <div className="quick-row">
              {['臺中市','彰化縣','臺北市','高雄市'].map((name) => (
                <button key={name} className={`quick-btn ${region === name ? 'active' : ''}`} onClick={() => setRegion(name)}>{name}</button>
              ))}
              <button className="quick-btn" onClick={() => loadWeather(region)}>↻ 更新資料</button>
            </div>
          </div>
        </div>
      </section>

      {error && <div className="error">API ERROR // {error}</div>}
      {loading && <div className="loading">SCANNING CWA DATASTREAM…</div>}

      <section className="metrics">
        <div className="metric"><div className="metric-label">Selected Zone</div><div className="metric-value">{region}</div><div className="metric-sub">{center ? `${center[0].toFixed(3)}, ${center[1].toFixed(3)}` : '—'}</div></div>
        <div className="metric"><div className="metric-label">Weekly Max</div><div className="metric-value">{stats.high == null ? '—' : `${stats.high.toFixed(0)}°C`}</div><div className="metric-sub">7-day maximum</div></div>
        <div className="metric"><div className="metric-label">Weekly Min</div><div className="metric-value">{stats.low == null ? '—' : `${stats.low.toFixed(0)}°C`}</div><div className="metric-sub">7-day minimum</div></div>
        <div className="metric"><div className="metric-label">Avg Temp Range</div><div className="metric-value">{stats.range == null ? '—' : `${stats.range.toFixed(1)}°C`}</div><div className="metric-sub">mean daily range</div></div>
      </section>

      <section className="grid-main">
        <div className="panel">
          <div className="panel-head"><div className="panel-title">GIS // 台灣縣市氣象節點</div><div className="panel-tag">CLICK MAP TO SELECT</div></div>
          <TaiwanMap selected={region} onSelect={setRegion} />
        </div>

        <div className="panel">
          <div className="panel-head"><div className="panel-title">FORECAST // 一週預報</div><div className="panel-tag">CWA LIVE</div></div>
          <div className="forecast-card">
            <div className="today-row">
              <div>
                <div className="metric-label">TODAY / {today?.date || '—'}</div>
                <div className="temp-range">{today && Number.isFinite(today.min) && Number.isFinite(today.max) ? `${today.min.toFixed(0)}–${today.max.toFixed(0)}°C` : '—'}</div>
                <div className="weather-text">{today?.weather || '等待資料'}</div>
              </div>
              <div className="weather-icon">{iconFor(today?.weather)}</div>
            </div>

            <div className="chart-wrap">
              <div className="chart-title">TEMPERATURE TREND // 青：最高溫　紫：最低溫</div>
              <TemperatureChart data={data?.forecast || []} />
            </div>

            <div className="day-list">
              {(data?.forecast || []).map((day) => (
                <div className="day-item" key={day.date}>
                  <div className="day-date">{day.date}</div>
                  <div className="day-wx">{iconFor(day.weather)} {day.weather}</div>
                  <div className="day-temp">{Number.isFinite(day.min) && Number.isFinite(day.max) ? `${day.min.toFixed(0)}–${day.max.toFixed(0)}°` : '—'}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="info-strip">
        <span>DATA SOURCE // 中央氣象署 CWA Open Data</span>
        <span>DATASET // F-D0047-091</span>
        <span>SECURITY // API KEY SERVER-SIDE ONLY</span>
        <span>{data?.updatedAt ? `UPDATED // ${new Date(data.updatedAt).toLocaleString('zh-TW')}` : ''}</span>
      </div>
    </main>
  );
}

'use client';

import { useEffect, useRef } from 'react';

export const REGION_CENTERS = {
  '臺北市': [25.0375,121.5637], '新北市': [25.0120,121.4657], '基隆市': [25.1276,121.7392],
  '桃園市': [24.9937,121.3010], '新竹市': [24.8138,120.9675], '新竹縣': [24.8387,121.0177],
  '苗栗縣': [24.5602,120.8214], '臺中市': [24.1477,120.6736], '彰化縣': [24.0756,120.5440],
  '南投縣': [23.9609,120.9719], '雲林縣': [23.7092,120.4313], '嘉義市': [23.4801,120.4491],
  '嘉義縣': [23.4518,120.2555], '臺南市': [22.9997,120.2270], '高雄市': [22.6273,120.3014],
  '屏東縣': [22.5519,120.5488], '宜蘭縣': [24.7021,121.7378], '花蓮縣': [23.9911,121.6112],
  '臺東縣': [22.7554,121.1500], '澎湖縣': [23.5712,119.5793], '金門縣': [24.4321,118.3171],
  '連江縣': [26.1605,119.9517]
};

export default function TaiwanMap({ selected, onSelect }) {
  const elRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    let alive = true;

    async function renderMap() {
      const mod = await import('leaflet');
      const L = mod.default || mod;
      if (!alive || !elRef.current) return;

      if (!mapRef.current) {
        mapRef.current = L.map(elRef.current, {
          zoomControl: true,
          attributionControl: true,
          minZoom: 5,
          maxZoom: 13,
        }).setView([23.7, 121.0], 7);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          subdomains: 'abcd',
          maxZoom: 19,
          attribution: '&copy; OpenStreetMap &copy; CARTO'
        }).addTo(mapRef.current);

        layerRef.current = L.layerGroup().addTo(mapRef.current);
      }

      layerRef.current.clearLayers();
      Object.entries(REGION_CENTERS).forEach(([name, [lat, lng]]) => {
        const active = name === selected;
        const marker = L.circleMarker([lat, lng], {
          radius: active ? 11 : 6,
          color: active ? '#39e7ff' : '#697bff',
          weight: active ? 3 : 1.5,
          fillColor: active ? '#39e7ff' : '#4b5bdc',
          fillOpacity: active ? 0.78 : 0.42,
        }).addTo(layerRef.current);
        marker.bindTooltip(name, { direction: 'top', opacity: .92 });
        marker.on('click', () => onSelect?.(name));
      });

      const center = REGION_CENTERS[selected];
      if (center) mapRef.current.flyTo(center, 9, { duration: 0.8 });
      setTimeout(() => mapRef.current?.invalidateSize(), 0);
    }

    renderMap();
    return () => { alive = false; };
  }, [selected, onSelect]);

  useEffect(() => () => {
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }
  }, []);

  return <div ref={elRef} className="map-shell" aria-label="台灣 GIS 縣市地圖" />;
}

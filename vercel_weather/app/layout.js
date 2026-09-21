import './globals.css';
import 'leaflet/dist/leaflet.css';

export const metadata = {
  title: 'Taiwan Weather Intelligence',
  description: 'CWA Open Data × GIS × Vercel',
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}

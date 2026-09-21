# Taiwan Weather Intelligence — Vercel

Next.js + Vercel Serverless API + Leaflet GIS + CWA Open Data。

## Vercel deployment

- Repository: `ke60315-ux/homework`
- Branch: `main`
- Root Directory: `vercel_weather`
- Framework: Next.js
- Environment Variable: `CWA_API_KEY`

CWA API Key 只存在 Vercel Environment Variables，不會寫入 GitHub，也不會送到瀏覽器。

## Local development

```bash
npm install
npm run dev
```

建立 `.env.local`：

```env
CWA_API_KEY=YOUR_CWA_API_KEY
```

資料集：`F-D0047-091`

# 🌿 Taiwan Weather Forecast

> 淡綠文青風 × 中央氣象署 CWA Open Data × Streamlit

這是一個台灣一週天氣預報作品。使用者可切換縣市，查看未來一週最高／最低溫、溫度趨勢與每日預報。API Key 透過 Streamlit Secrets 管理，不會出現在公開 GitHub 原始碼中。

## 🔗 Demo

- **即時天氣 App**：https://homework-dkcfjehzsap55xdqpjef7u.streamlit.app
- **GitHub Pages 展示首頁**：https://ke60315-ux.github.io/homework/

## ✨ 主要功能

- 台灣各縣市選擇
- 未來一週最高／最低溫
- 一週溫度折線圖
- 每日預報表格
- CWA Open Data 即時資料
- 文青淡綠色 UI
- Streamlit Secrets 保護 API Key

## 📁 專案結構

```text
taiwan_weather_forecast/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## 🔐 API Key

程式透過以下方式讀取：

```python
API_KEY = st.secrets["CWA_API_KEY"]
```

正式 API Key 不會存放在 GitHub。部署至 Streamlit Community Cloud 時，請在 **App Settings → Secrets** 設定：

```toml
CWA_API_KEY = "YOUR_CWA_API_KEY"
```

## ▶️ 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Streamlit Cloud

部署設定：

```text
Repository: ke60315-ux/homework
Branch: main
Main file path: taiwan_weather_forecast/app.py
```

---

**Data source:** Central Weather Administration (CWA) Open Data

# 🌿 Taiwan Weather Forecast

淡綠文青風的台灣一週天氣預報，使用中央氣象署 CWA Open Data。

## 執行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

## API Key

此專案不把 API Key 寫入程式碼。請在 Streamlit Secrets 設定：

```toml
CWA_API_KEY = "YOUR_CWA_API_KEY"
```

本機可建立 `.streamlit/secrets.toml`；此檔已被 `.gitignore` 排除。

## Streamlit Cloud

部署時主程式路徑請填：

```text
taiwan_weather_forecast/app.py
```

然後在 Streamlit Cloud 的 Secrets 中加入 `CWA_API_KEY`。

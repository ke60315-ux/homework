# DIC2 — Multiple Linear Regression Explorer

Live GitHub Pages page: https://ke60315-ux.github.io/homework/dic2-regression/

## Features
- Two problem dropdowns: **50 Startups** and **Boston Housing**, plus custom CSV mode.
- Load a publicly accessible CSV URL or upload your own CSV file.
- Choose target variable for custom datasets.
- True in-browser OLS regression; greedy forward feature selection using training-only 5-fold CV.
- Display RMSE, R², adjusted R², MAE, prediction formula, comparison table, and live prediction.
- 1–5 features, 80/20 train/test split, deterministic seed.
- CSV export of results.

## Use
1. Open the [live demo](https://ke60315-ux.github.io/homework/dic2-regression/).
2. Choose a problem, or upload your own CSV.
3. Choose a numeric target column and click **Run Regression**.
4. Click k=1..5 to inspect the selected model.

**Notes:** Input URLs need browser CORS access. GitHub Pages is static; no server-side files are uploaded. The computations run on the visitor's computer and results may differ from the reference screenshot due to data splits and model selection method.

Course: 人工智慧與資訊安全 / Assignment: DIC2 多元線性回歸.

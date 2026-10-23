# Flight Ticket Price Prediction — Multiple Linear Regression Explorer

**Live GitHub Pages:** https://ke60315-ux.github.io/homework/flight-price-prediction/

This is a separate project folder inside the existing `homework` GitHub repository. It does **not** overwrite the DIC2 startup/housing demo.

## Source data
- User-supplied `Clean_Dataset.csv`: 300,153 flights, 12 columns.
- Hosted demo file `datasets/Clean_Dataset_sample.csv`: **1,740 records** extracted from 12 dispersed regions of the original CSV. This is a browser-friendly sample, not the full dataset and not guaranteed representative.
- `price` is the numerical target. Record index and high-cardinality flight ID are excluded; other predictors are one-hot encoded.
- The model currently sees 29 encoded candidate predictors in the demonstration sample.
- Uploading the full source CSV in the web interface runs a deterministic 3,000-row subsample for browser responsiveness.

## Features
- Built-in Flight Ticket Price Prediction / custom CSV URL / CSV file upload
- Five-fold CV greedy forward selection of k=1..5 model predictors
- RMSE, R-squared, adjusted R-squared, MAE
- Regression coefficients, standard error, t-test, p-value, 95% CI and VIF
- Sorted independent test residuals and diagnostic flags
- Interactive price predictor and CSV export

**Statistical note:** Inference is on the selected training model and does not account for post-selection uncertainty. This is a course-work exploration, not a production airfare quote engine.

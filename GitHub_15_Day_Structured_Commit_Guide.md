# 📅 PRAGATI AI — 15-Day Structured Git Commit Guide

This guide provides a structured daily roadmap to naturally build and commit the PRAGATI AI platform over the next 15 days, ensuring an average of **20–30 commits per day**.

If you wish to **reset your local Git repository** to a completely fresh state (zero commits) so you can follow this manual workflow, run this command in your terminal:
```bash
# Force delete the local Git database to start fresh
Remove-Item -Recurse -Force .git
```

---

## 🛠️ General Commit Best Practices
* **Micro-Commits**: Do not write an entire file and commit it once. Write the imports first $\rightarrow$ commit. Write a helper function $\rightarrow$ commit. Add comments $\rightarrow$ commit. Fix a typo $\rightarrow$ commit. This represents high-quality active engineering.
* **Commit Types**: Use semantic tags:
  * `feat:` for new features/functions.
  * `fix:` for bug fixes.
  * `refactor:` for code restructures/optimizations.
  * `style:` for formatting, CSS layouts, alignment.
  * `docs:` for readme, comments, docstrings.
  * `chore:` for settings, requirements, gitignore.

---

## 📅 Daily Development Roadmap & Commit Logs

### Day 1: Project Initialization & Directory Structure (20 Commits)
**Goal:** Setup repository config, workspace folders, dependencies, and PRD guidelines.
* **Commit Messages to Use:**
  1. `chore: initial repository directories setup`
  2. `chore: create backend and engine package folders`
  3. `chore: configure .gitignore to ignore node_modules`
  4. `chore: add requirements.txt with backend packages`
  5. `chore: append fastapi and uvicorn dependencies`
  6. `chore: add scikit-learn and pandas to dependencies`
  7. `chore: add prophet time-series package to requirements`
  8. `docs: create project specifications PRD.md`
  9. `docs: write product executive summary in PRD`
  10. `docs: define target success metrics in PRD`
  11. `docs: add regulatory compliance background in PRD`
  12. `docs: outline 4-phase project roadmap in PRD`
  13. `docs: create initial README.md guide`
  14. `docs: write project value propositions in readme`
  15. `docs: document repository structure in readme`
  16. `chore: configure local package imports init files`
  17. `style: standardize requirements text formatting`
  18. `docs: add developers team registry in readme`
  19. `chore: add license placeholder to workspace`
  20. `chore: verify folder permissions for caching`

---

### Day 2: Data Ingestion — Dataset Downloader (20 Commits)
**Goal:** Implement the download, extraction, and cache-checking logic in `dataset_loader.py`.
* **Commit Messages to Use:**
  1. `feat: create engine/dataset_loader.py file`
  2. `feat: add required imports for loader (requests, zipfile)`
  3. `feat: define local folder caching paths in loader`
  4. `feat: add UCI Steel dataset zip URL constant`
  5. `feat: implement download_and_extract_dataset base`
  6. `feat: add requests stream retrieval for download`
  7. `feat: write downloaded chunks progress logger`
  8. `fix: add folder checking to ensure data dir exists`
  9. `feat: implement duplicate check to skip downloads`
  10. `feat: implement zip archive extraction using zipfile`
  11. `chore: delete zip archive after successful extract`
  12. `fix: catch connection timeout exceptions on HTTP request`
  13. `fix: catch file permission errors during extraction`
  14. `docs: add docstrings explaining downloader structure`
  15. `test: verify downloader output path assert check`
  16. `refactor: clean up file stream close operations`
  17. `feat: write console check logs in downloader`
  18. `fix: handle edge case when UCI site is offline`
  19. `refactor: rename variables for cleaner path handling`
  20. `docs: document dataset download source links`

---

### Day 3: Data Ingestion — Datetime Parsing & Resampling (20 Commits)
**Goal:** Implement DataFrame loading, column normalization, strict date formatting, and hourly resampling.
* **Commit Messages to Use:**
  1. `feat: implement load_dataset core function in loader`
  2. `feat: add pandas csv reading parameters`
  3. `feat: clean and map column header names to snake_case`
  4. `feat: standardize Usage_kWh column name`
  5. `feat: rename reactive power lagging/leading headers`
  6. `feat: clean power factor column headers`
  7. `feat: parse string dates to datetime using dayfirst=True`
  8. `fix: resolve month/day swap errors on Windows platforms`
  9. `feat: write hourly resampling aggregation method`
  10. `refactor: group resampled active and reactive variables`
  11. `fix: fill missing datestamps using forward fill`
  12. `feat: compute baseline mean and std dev values`
  13. `feat: add weekend status boolean column mapper`
  14. `refactor: optimize dataframe memory types`
  15. `fix: resolve empty cell type warning errors`
  16. `test: assert resampled row counts match predictions`
  17. `docs: document date format conversions in loader`
  18. `refactor: remove redundant columns from processed data`
  19. `feat: return clean processed dataframe in loader`
  20. `docs: update readme with dataset variables details`

---

### Day 4: Machine Learning — Anomaly Detector Core (20 Commits)
**Goal:** Set up `anomaly_detector.py` and implement Scikit-Learn's `IsolationForest` model.
* **Commit Messages to Use:**
  1. `feat: create engine/anomaly_detector.py file`
  2. `feat: add scikit-learn IsolationForest imports`
  3. `feat: define feature column list for anomaly detection`
  4. `feat: write run_anomaly_detection base wrapper`
  5. `feat: isolate input features matrix from dataframe`
  6. `fix: handle NaN feature rows using mean fill`
  7. `feat: configure IsolationForest hyperparameters`
  8. `tweak: set contamination rate to 0.01`
  9. `tweak: set n_estimators to 100 for fast runs`
  10. `feat: fit isolation forest model on features`
  11. `feat: predict outlier classes (1 for normal, -1 outlier)`
  12. `feat: extract decision function anomaly scores`
  13. `refactor: optimize model fitting execution time`
  14. `fix: handle empty input dataframes safely`
  15. `docs: document isolation forest mathematical variables`
  16. `test: write test asserting outlier predictions count`
  17. `refactor: rename outlier prediction output columns`
  18. `feat: cache trained IsolationForest instances`
  19. `docs: add docstrings explaining contamination factor`
  20. `test: mock input data to test IsolationForest fitting`

---

### Day 5: Machine Learning — Anomaly Heuristics Rules (20 Commits)
**Goal:** Implement the rule-based expert system classifying anomalies into idle leaks, weekend operations, machinery idling, or spikes.
* **Commit Messages to Use:**
  1. `feat: implement rule-based anomaly heuristics classifier`
  2. `feat: write base stats calculator for rule inputs`
  3. `feat: add Critical Power Spike threshold rule`
  4. `feat: add Idle Energy Leak threshold condition`
  5. `feat: add Weekend Energy Leak condition checker`
  6. `feat: add low power-factor Machinery Idling rule`
  7. `refactor: filter IsolationForest outliers inside heuristics`
  8. `fix: check for light load class before idle leak check`
  9. `feat: format anomaly logs list dictionaries`
  10. `feat: add custom explanations to each anomaly type`
  11. `feat: write mitigation recommendations for operator`
  12. `feat: assign severity tags (Critical, High, Medium, Low)`
  13. `fix: resolve string formatting errors in details`
  14. `refactor: speed up row looping on pandas dataframes`
  15. `fix: handle division by zero in power factor checks`
  16. `test: verify classified anomaly outputs schemas`
  17. `docs: add code comments explaining rule logic`
  18. `refactor: clean up output payload dictionary keys`
  19. `feat: write anomaly output logs caching utility`
  20. `docs: update anomalies classification list in PRD`

---

### Day 6: Machine Learning — Prophet Time-Series Forecast (20 Commits)
**Goal:** Set up `forecaster.py` and implement Meta Prophet time-series regressions.
* **Commit Messages to Use:**
  1. `feat: create engine/forecaster.py file`
  2. `feat: add Meta Prophet library imports`
  3. `fix: write try-except imports block for Prophet`
  4. `feat: write fallback flag if Prophet is missing`
  5. `feat: implement generate_forecast base function`
  6. `feat: resample telemetry to hourly values in forecaster`
  7. `feat: split hourly telemetry into train/validation sets`
  8. `feat: format train data to ds and y requirements`
  9. `feat: initialize Prophet model configurations`
  10. `refactor: enable daily and weekly seasonability features`
  11. `feat: fit Prophet model on training data`
  12. `feat: generate future timestamps date range`
  13. `feat: predict future values using Prophet model`
  14. `fix: replace negative predictions with 0.0 value`
  15. `feat: calculate validation root mean squared error (RMSE)`
  16. `docs: add comments explaining Prophet trend additive models`
  17. `docs: explain Fourier seasonality equations in comments`
  18. `refactor: optimize validation splits selection`
  19. `docs: document Prophet hyperparameter selections`
  20. `test: check prophet forecast shape matches future timeline`

---

### Day 7: Machine Learning — Random Forest Forecast Lags (20 Commits)
**Goal:** Implement feature engineering (1-day, 7-day lags, cyclical features) and train the Random Forest Regressor.
* **Commit Messages to Use:**
  1. `feat: write prepare_temporal_features helper in forecaster`
  2. `feat: extract hour of day temporal features`
  3. `feat: extract day of week temporal features`
  4. `feat: extract month and weekend boolean indicators`
  5. `feat: engineer lag_1d (24h shift) feature column`
  6. `feat: engineer lag_7d (168h shift) feature column`
  7. `fix: fill lag NaNs using historical mean values`
  8. `feat: configure RandomForestRegressor parameters`
  9. `tweak: set n_estimators to 50 for rapid calculations`
  10. `feat: fit Random Forest on train features matrix`
  11. `feat: implement recursive autoregressive forecasting loop`
  12. `feat: update lag features with predictions during forecast`
  13. `feat: calculate Random Forest validation RMSE`
  14. `feat: write model selector comparator logic`
  15. `fix: handle single-row inputs forecasts in Random Forest`
  16. `docs: explain recursive autoregressive forecast in comments`
  17. `refactor: clean up lag feature matrices memory`
  18. `test: assert Random Forest predictions return valid floats`
  19. `feat: package forecasting outputs dictionary payload`
  20. `docs: update forecasting sections inside readme`

---

### Day 8: Optimization — Load Shifting & Tariffs (20 Commits)
**Goal:** Set up `scheduler.py` and write the Time-of-Use tariff and carbon intensity curves.
* **Commit Messages to Use:**
  1. `feat: create engine/scheduler.py file`
  2. `feat: define hourly solar panel yield factor array`
  3. `feat: implement get_tariff rate lookup function`
  4. `feat: define peak business hours tariff rate ($0.18)`
  5. `feat: define mid-peak tariff rate ($0.12)`
  6. `feat: define off-peak evening tariff rate ($0.06)`
  7. `feat: implement get_carbon_intensity lookup function`
  8. `feat: define solar grid mix carbon rate (250g)`
  9. `feat: define business grid mix carbon rate (320g)`
  10. `feat: define evening grid mix carbon rate (450g)`
  11. `feat: define base fossil grid mix carbon rate (520g)`
  12. `feat: write calculate_schedule_metrics helper`
  13. `feat: write task loop over duration steps`
  14. `feat: incorporate solar generation offsets in metrics`
  15. `feat: calculate net grid draw from solar panel yield`
  16. `fix: cap net grid draw at minimum of 0.0`
  17. `docs: document time-of-use tariff rate tables`
  18. `refactor: group hourly cost and carbon emissions`
  19. `docs: explain carbon intensity curve trends`
  20. `test: verify get_tariff matches correct peak hours`

---

### Day 9: Optimization — Scheduler Optimizer (20 Commits)
**Goal:** Implement the optimization search algorithm and baseline comparison logic.
* **Commit Messages to Use:**
  1. `feat: implement optimize_shift_schedule search function`
  2. `feat: loop over all 24 possible start hours`
  3. `feat: write cost scoring optimization index formula`
  4. `feat: convert carbon emissions from grams to kilograms`
  5. `feat: apply environmental weighting factor parameters`
  6. `tweak: set default environmental weight to 0.15`
  7. `feat: find start hour with minimum score index`
  8. `feat: compile optimal details list dictionary`
  9. `feat: calculate default baseline metrics at 09:00 AM`
  10. `feat: calculate financial cost savings dollars`
  11. `feat: calculate carbon abatement savings kilograms`
  12. `feat: calculate cost savings percentage index`
  13. `feat: calculate carbon savings percentage index`
  14. `fix: handle edge case when baseline cost is 0.0`
  15. `fix: handle task durations exceeding 24 hours`
  16. `docs: add code comments explaining optimization weights`
  17. `refactor: streamline output dictionary response keys`
  18. `test: check optimizer returns cheaper schedule than base`
  19. `docs: add docstrings to optimize_shift_schedule`
  20. `docs: update shift scheduler details in readme`

---

### Day 10: Financials — Digital Twin Simulator (20 Commits)
**Goal:** Implement Capital Expenditure (CapEx) payback and annual solar/battery ROI equations.
* **Commit Messages to Use:**
  1. `feat: add Digital Twin ROI calculations in backend`
  2. `feat: write annual solar generation potential formula`
  3. `tweak: set annual solar yield yield multiplier to 1320`
  4. `feat: write solar battery self-consumption rate loop`
  5. `feat: calculate base solar self-consumption rate (60%)`
  6. `feat: calculate battery storage boost capacity ratio`
  7. `feat: write simple payback period capex calculations`
  8. `tweak: set solar capex cost to $850 per kW`
  9. `tweak: set battery capex cost to $450 per kWh`
  10. `feat: calculate annual financial bill savings`
  11. `tweak: set baseline average industrial tariff to $0.13`
  12. `feat: calculate annual carbon offset kilograms`
  13. `fix: prevent division by zero in payback calculations`
  14. `fix: enforce realistic battery capacity boundary limits`
  15. `docs: add comments explaining self-consumption calculations`
  16. `docs: document panel installation cost assumptions`
  17. `refactor: clean up ROI variable name mappings`
  18. `test: verify payback period calculations are correct`
  19. `feat: output detailed ROI payload dictionary`
  20. `docs: update Digital Twin formulas list in PRD`

---

### Day 11: Backend API — Ingestion Server Setup (20 Commits)
**Goal:** Set up `api.py` FastAPI server, configure CORS, and build GET telemetry/status endpoints.
* **Commit Messages to Use:**
  1. `feat: create backend/api.py file`
  2. `feat: add fastapi and uvicorn server imports`
  3. `feat: initialize FastAPI application instance`
  4. `feat: add CORS middleware configurations`
  5. `feat: allow origins star wildcard in development`
  6. `feat: implement cache variables in api.py`
  7. `feat: write get_cached_data helper loader`
  8. `feat: write get_cached_anomalies helper loader`
  9. `feat: restrict anomaly training rows size to 15000`
  10. `feat: write GET /api/status health endpoint`
  11. `feat: write GET /api/telemetry telemetry endpoint`
  12. `feat: add filter query parameters for telemetry days`
  13. `feat: downsample telemetry data using hourly averages`
  14. `fix: resolve relative folder path import warnings`
  15. `fix: catch dataset loading exceptions inside endpoints`
  16. `docs: document status and telemetry JSON schemas`
  17. `test: check status endpoint responds with 200 OK`
  18. `refactor: optimize dataset cache checking logic`
  19. `docs: write API configuration details in readme`
  20. `test: check telemetry endpoint returns valid arrays`

---

### Day 12: Backend API — ML Endpoint Routing (20 Commits)
**Goal:** Implement POST routes for forecasting, shift scheduling, digital twin simulations, and chatbot copilot.
* **Commit Messages to Use:**
  1. `feat: add pydantic request schemas models`
  2. `feat: add ForecastRequest pydantic model schema`
  3. `feat: add ScheduleRequest pydantic model schema`
  4. `feat: add SimulateRequest pydantic model schema`
  5. `feat: add ChatRequest pydantic model schema`
  6. `feat: write POST /api/forecast endpoint route`
  7. `refactor: integrate forecasting engines into api route`
  8. `feat: write POST /api/schedule endpoint route`
  9. `refactor: integrate shift scheduler into api route`
  10. `feat: write POST /api/simulate endpoint route`
  11. `refactor: integrate Digital Twin ROI loop into api route`
  12. `feat: write POST /api/copilot chat endpoint route`
  13. `feat: implement NLP keyword parser router inside copilot`
  14. `feat: write leaks intent conversational reply`
  15. `feat: write spikes intent conversational reply`
  16. `feat: write forecast and solar intent replies`
  17. `fix: handle unmapped queries using default help reply`
  18. `fix: resolve json validation exception errors`
  19. `docs: add comments detailing POST schemas`
  20. `test: verify all POST API routes return 200 OK`

---

### Day 13: Client UI — HTML Structure & Layout (20 Commits)
**Goal:** Create `pragati_platform/frontend/index.html` structure and tab navigation markup.
* **Commit Messages to Use:**
  1. `feat: create frontend/index.html file`
  2. `feat: write html boilerplate and character set`
  3. `feat: import google font Inter and Chart.js CDN`
  4. `feat: link style.css stylesheet asset`
  5. `feat: write main app-container wrapper div`
  6. `feat: add sidebar navigation panel markup`
  7. `feat: write brand logo and portal titles`
  8. `feat: add tab menu items navigation links`
  9. `feat: add backend connection status indicator dot`
  10. `feat: add main content container division`
  11. `feat: write dynamic page header titles section`
  12. `feat: add Tab 1 Dashboard KPI cards markup`
  13. `feat: add telemetry chart wrapper div`
  14. `feat: add Tab 2 Anomalies table structure`
  15. `feat: add Tab 3 Forecast parameters sliders and chart wrapper`
  16. `feat: add Tab 4 Shift Scheduler input forms`
  17. `feat: add Tab 5 Digital Twin sliders and KPI cards`
  18. `feat: add Tab 6 AI Copilot chat container`
  19. `refactor: add descriptive IDs to interactive inputs`
  20. `docs: comment HTML sections index file`

---

### Day 14: Client UI — CSS Theme Styling (25 Commits)
**Goal:** Implement `style.css` glassmorphic dark theme, layouts, responsive grids, and animations.
* **Commit Messages to Use:**
  1. `style: create frontend/style.css file`
  2. `style: configure default margin resets and box sizing`
  3. `style: set base dark body background color (#0B0F19)`
  4. `style: define HSL variables theme colors`
  5. `style: style sidebar navigation container`
  6. `style: add glow text-shadows to logo accent`
  7. `style: style navigation items links and icons`
  8. `style: add hover background states to links`
  9. `style: style active navigation link background`
  10. `style: write pulse animation keyframes for status dot`
  11. `style: style main layout containers grids`
  12. `style: style glassmorphic KPI cards panels`
  13. `style: apply backdrop-filter blur parameters to cards`
  14. `style: customize chart container boxes`
  15. `style: style tables headers and rows spacing`
  16. `style: write severity badges color rules`
  17. `style: style input numbers fields and select ranges`
  18. `style: customize range sliders thumb glow`
  19. `style: style primary gradient buttons`
  20. `style: style chat bubble message containers`
  21. `style: write fade-in animation keyframes for tabs`
  22. `style: define media query layout breakpoints`
  23. `fix: adjust text line-height parameters on mobile`
  24. `fix: resolve flex wrap overlaps on small screens`
  25. `docs: document CSS variables parameters`

---

### Day 15: Client UI — JavaScript Controller (25 Commits)
**Goal:** Write `app.js` routing logic, Chart.js integrations, fetch loops, and chatbot listeners.
* **Commit Messages to Use:**
  1. `feat: create frontend/app.js file`
  2. `feat: define base API URL constants`
  3. `feat: declare chart object instance cache vars`
  4. `feat: write DOMContentLoaded initialization listener`
  5. `feat: implement initTabNavigation route tab switcher`
  6. `feat: write tab panels active classes toggle`
  7. `feat: write checkBackendStatus fetch check loop`
  8. `feat: write loadTelemetry data loading function`
  9. `feat: write renderTelemetryChart drawing routine`
  10. `feat: bind Chart.js scales datasets for telemetry`
  11. `feat: write loadAnomalies logs loading function`
  12. `feat: write table row rendering loop for anomalies`
  13. `feat: write runForecasting post request route`
  14. `feat: write renderForecastChart drawing routine`
  15. `feat: write runScheduler post request optimizer`
  16. `feat: write renderSchedulerChart comparison bar routine`
  17. `feat: write runDigitalTwin simulator fetch handler`
  18. `feat: update Digital Twin ROI metrics in DOM`
  19. `feat: write sendCopilotMessage chat bubble appender`
  20. `feat: fetch Copilot conversational responses`
  21. `fix: handle fetch connection failures gracefully`
  22. `fix: prevent Chart.js canvas memory leaks`
  23. `refactor: compile app state global configuration`
  24. `docs: add inline comments explaining JS handlers`
  25. `test: check JS execution completes without warnings`

---

### Day 16: Project Report, Setup BAT & Verification (20 Commits)
**Goal:** Integrate the frontend static files on backend, write setup VBS/BAT scripts, compile PDF report, and run tests.
* **Commit Messages to Use:**
  1. `feat: serve static frontend files inside api.py`
  2. `feat: mount StaticFiles path route on FastAPI`
  3. `fix: resolve relative path references inside api.py`
  4. `feat: write stop_pragati.bat windows port killer`
  5. `feat: write run_pragati.vbs silent launcher`
  6. `feat: create generate_report.js Node compiler`
  7. `feat: import pdfkit package in report compiler`
  8. `feat: write cover page layouts inside pdfkit`
  9. `feat: draw modular system architecture flowchart in PDF`
  10. `feat: write math equations derivations in PDF`
  11. `feat: write load shifting score formulas in PDF`
  12. `feat: calculate payback ROI formulas in PDF`
  13. `feat: write developer installation guide section in PDF`
  14. `refactor: compile PDF report and run file checks`
  15. `fix: resolve page height overlaps inside PDF compiler`
  16. `docs: update project walkthrough documentation`
  17. `test: verify output PDF matches exactly 15 pages`
  18. `test: check all python files syntax compile`
  19. `style: adjust margin spacing on frontend index`
  20. `chore: final project audit, formatting and clean up`

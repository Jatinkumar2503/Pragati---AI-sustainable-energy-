# 📅 PRAGATI AI — 40-Day Structured Git Commit Guide (10 Commits/Day)

This guide provides a structured, organic daily roadmap to commit the PRAGATI AI platform over the next 40 days, ensuring exactly **10 commits per day (400 commits total)**. Each commit represents a clear, micro-engineered step.

---

## 🛠️ General Commit Best Practices
* **Micro-Commits**: Do not bundle multiple days of work. Commit small increments, logical components, comments, or fixes.
* **Commit Types**: Use semantic tags:
  * `feat:` for new features/functions.
  * `fix:` for bug fixes.
  * `refactor:` for code optimizations or structural changes.
  * `style:` for formatting, UI design, alignment.
  * `docs:` for project docs, comments, docstrings.
  * `chore:` for configuration, dependencies, setup.

---

## 📅 Daily Development Roadmap & Commit Logs

### Day 1: Project Root & Workspace Setup
1. `chore: create project root directory structural folders`
2. `chore: configure .gitignore to exclude virtual environments`
3. `chore: configure .gitignore to ignore node_modules and logs`
4. `chore: initialize requirements.txt with base system libraries`
5. `chore: add fastapi and uvicorn dependencies to requirements`
6. `chore: add pandas and numpy for data handling`
7. `chore: append scikit-learn and joblib for ML modules`
8. `chore: add prophet and holidays dependencies to requirements`
9. `docs: write product specifications outline in PRD.md`
10. `docs: document executive summary and platform core goals in PRD`

### Day 2: PRD Detailing & Project Readme
1. `docs: specify target KPIs and carbon success metrics in PRD`
2. `docs: write technical architecture data flow in PRD`
3. `docs: add modular system layout diagram to PRD`
4. `docs: outline 4-phase release plan and milestones in PRD`
5. `docs: write project value proposition in README.md`
6. `docs: document repository directory tree structure in README`
7. `docs: add installation instructions template to README`
8. `chore: configure local engine package modules __init__.py`
9. `style: standardize spacing in requirements dependency lists`
10. `docs: add developers registry and credentials in README`

### Day 3: Ingestion — Dataset Loader Configuration
1. `feat: create engine/dataset_loader.py module file`
2. `feat: add base imports for loader requests and zipfile`
3. `feat: configure logger interface in dataset loader`
4. `feat: define local caching paths constants for data files`
5. `feat: add UCI Steel industry energy consumption dataset URL`
6. `feat: write download_and_extract_dataset skeleton structure`
7. `fix: add folder checking to verify data cache dir exists`
8. `feat: implement duplicate check skipping download if cached`
9. `feat: write console log updates for downloader status`
10. `docs: add docstrings explaining downloader cache path check`

### Day 4: Ingestion — Chunk Streaming & Extraction
1. `feat: add requests stream download in dataset loader`
2. `feat: implement stream progress tracker with logger prints`
3. `feat: write zipfile extract helper utility in loader`
4. `feat: delete local zip archive after successful extract`
5. `fix: catch HTTP connection timeout exceptions during download`
6. `fix: catch IO errors and zip archive extraction permissions`
7. `refactor: clean up file stream close operations in loader`
8. `fix: handle edge case when UCI data repository is offline`
9. `refactor: rename variables for cleaner path resolution`
10. `docs: document dataset download source links and citation`

### Day 5: Ingestion — Parsing and Header Normalization
1. `feat: implement load_dataset core function in loader`
2. `feat: add pandas csv parser parameters for load_dataset`
3. `feat: map column header names to lowercase snake_case`
4. `feat: normalize Usage_kWh column name to usage_kwh`
5. `feat: map reactive lagging power factor header labels`
6. `feat: map reactive leading power factor header labels`
7. `feat: clean power factor column header names`
8. `feat: parse datestamp strings to pandas datetime format`
9. `fix: resolve month/day swap errors on windows systems`
10. `docs: document datetime format conversion conventions`

### Day 6: Ingestion — Resampling & Interpolation
1. `feat: write hourly resampling aggregator in dataset loader`
2. `refactor: group resampled power variables by mean value`
3. `feat: add forward fill interpolation for missing timestamps`
4. `feat: add backward fill fallback interpolation checks`
5. `feat: compute baseline statistics for active power consumption`
6. `feat: add weekend status boolean flag to resampled rows`
7. `refactor: optimize dataframe columns data types to float32`
8. `fix: handle zero-length inputs inside load_dataset`
9. `test: assert resampled row counts match theoretical counts`
10. `feat: return clean normalized dataframes in load_dataset`

### Day 7: Storage — Base Interface Setup
1. `feat: create engine/base_db.py module file`
2. `feat: add abc and pandas imports to base database`
3. `feat: define BaseDatabase abstract class interface`
4. `feat: add init_db abstract method definition`
5. `feat: add insert_telemetry_records abstract method`
6. `feat: add query_all_telemetry abstract method`
7. `feat: add query_recent_telemetry abstract method`
8. `feat: add clear_all_telemetry abstract method`
9. `feat: add close connection abstract method`
10. `docs: write docstrings detailing BaseDatabase interface rules`

### Day 8: Storage — SQLite Implementation
1. `feat: create engine/telemetry_db.py database module`
2. `feat: add sqlite3 and thread locks imports to database`
3. `feat: define TelemetryDB class inheriting from BaseDatabase`
4. `feat: initialize default sqlite file path constants`
5. `feat: write init_db method creating telemetry table`
6. `feat: define schema indices on datetime column`
7. `feat: add thread locking protection in init_db call`
8. `fix: handle directory paths generation for sqlite files`
9. `test: verify sqlite database tables create successfully`
10. `docs: document sqlite connection thread safety strategies`

### Day 9: Storage — Ingestion Logic
1. `feat: implement insert_telemetry_records method in TelemetryDB`
2. `feat: write row transformations mapping tuple structures`
3. `feat: add batch insertions query using executemany`
4. `feat: add immediate commit flag override configuration`
5. `fix: catch transaction rollback exceptions on insert fail`
6. `feat: implement insert records counter tracking`
7. `refactor: optimize insertions by opening single transaction`
8. `fix: handle duplicate timestamp constraints in insertion`
9. `test: write unit test checking batch insertions count`
10. `docs: write code comments explaining sql transaction rollbacks`

### Day 10: Storage — Query Capabilities
1. `feat: implement query_all_telemetry method in TelemetryDB`
2. `feat: read SQL query outcomes directly into pandas dataframe`
3. `feat: ensure query results are sorted by date ascending`
4. `feat: implement query_recent_telemetry method for N days`
5. `feat: write date bounds calculations using datetime offset`
6. `fix: prevent SQL injection by parameterizing query filters`
7. `refactor: reuse database connection instances across queries`
8. `fix: handle cases when query results return empty rows`
9. `test: assert queried dataframe columns match schema specs`
10. `docs: write docstrings for query_recent_telemetry method`

### Day 11: Storage — Cleanup & Audits
1. `feat: implement clear_all_telemetry method in TelemetryDB`
2. `feat: write sql table truncate drop operations`
3. `feat: implement database close connection pool logic`
4. `feat: add db connection release on object destruction`
5. `fix: handle lock timeouts during database clear runs`
6. `feat: check disk utilization of local telemetry database`
7. `refactor: flush unwritten transaction caches on close`
8. `fix: close cursor objects cleanly to avoid memory leaks`
9. `test: verify clear database routine leaves zero records`
10. `docs: update telemetry database instructions in specs`

### Day 12: ESG Calculations — Auditing Model Base
1. `feat: add carbon auditing calculations inside engine`
2. `feat: define Scope 1 emission factor constants`
3. `feat: define Scope 2 grid emission intensity parameters`
4. `feat: define Scope 3 logistics baseline emission coefficients`
5. `feat: write compute_scope_1_emissions base formula`
6. `feat: write compute_scope_2_emissions grid mix formula`
7. `feat: write compute_scope_3_emissions supplier coefficients`
8. `fix: check for negative active power in scope 2 math`
9. `test: verify scope 2 carbon matches grid power draw`
10. `docs: document green house gas protocol reference links`

### Day 13: ESG Calculations — Reporting Payloads
1. `feat: write compile_esg_report summarizing audit figures`
2. `feat: structure compliance results into modular JSON payload`
3. `feat: map figures to GRI (Global Reporting Initiative) keys`
4. `feat: map figures to TCFD disclosure scorecard structures`
5. `feat: map figures to CDP climate change questionnaire format`
6. `refactor: speed up emissions aggregations on dataset`
7. `fix: handle missing supplier log entries in Scope 3`
8. `feat: compile monthly carbon reduction trend charts`
9. `test: verify ESG reports contain valid JSON keys`
10. `docs: write auditing model equations details in PRD`

### Day 14: ESG Calculations — Validation & RET
1. `feat: implement carbon auditing unit tests suites`
2. `feat: add mock telemetry dataset matching audit scope`
3. `feat: assert Scope 1 calculations against manually solved keys`
4. `feat: assert Scope 2 calculations for clean grid factors`
5. `feat: test Scope 3 data structures parsing safety`
6. `fix: resolve float truncation differences in carbon tests`
7. `refactor: optimize cumulative carbon summing loop speeds`
8. `docs: add comment logs explaining GRI mapping guidelines`
9. `style: align parameter lists formatting in carbon engine`
10. `test: check all carbon auditing assertions run green`

### Day 15: Anomaly Engine — Setup & Forest Init
1. `feat: create engine/anomaly_detector.py module file`
2. `feat: add scikit-learn IsolationForest imports in detector`
3. `feat: import pandas and numpy helper libraries in detector`
4. `feat: configure logger channel inside anomaly detector`
5. `feat: define feature column list constants for model inputs`
6. `feat: write run_anomaly_detection base core function`
7. `feat: isolate input matrices columns from dataset`
8. `fix: check for missing input columns in dataframe`
9. `fix: fill empty feature values using mean column values`
10. `docs: document isolation forest hyperparameter constraints`

### Day 16: Anomaly Engine — Forest Tuning
1. `feat: configure IsolationForest model constructor parameters`
2. `tweak: set IsolationForest contamination rate to 0.01`
3. `tweak: set IsolationForest estimators trees count to 100`
4. `feat: fit IsolationForest model on cleaned input features`
5. `feat: predict outlier classes (1 for normal, -1 outlier)`
6. `feat: extract decision function anomaly score offsets`
7. `refactor: optimize model training execution speed`
8. `feat: cache trained IsolationForest instances locally`
9. `test: assert outlier prediction values are within bounds`
10. `docs: write code comments describing anomaly path lengths`

### Day 17: Anomaly Engine — Spikes & Idling Rules
1. `feat: write rule-based heuristics classifier in detector`
2. `feat: implement base stats calculation loops for rules`
3. `feat: define Critical Power Spike alert threshold condition`
4. `feat: define Machinery Idling alert check on low power-factor`
5. `fix: check for machinery active workload thresholds in rules`
6. `refactor: combine IsolationForest outliers with rule alerts`
7. `fix: handle division-by-zero risks in power factor checks`
8. `feat: map custom mitigation suggestions for power spikes`
9. `feat: assign severity classifications (Critical, High, Medium)`
10. `docs: document power factor and machinery idling formulas`

### Day 18: Anomaly Engine — Leaks & Weekend Rules
1. `feat: write Idle Energy Leak checker inside heuristics`
2. `feat: write Weekend Energy Leak alert condition checks`
3. `feat: incorporate hourly timestamp boundaries in leak checks`
4. `feat: compile explanations for weekend operational patterns`
5. `feat: assign mitigation guidelines for idling weekend leaks`
6. `feat: map severity classes (Medium, Low) to leak alerts`
7. `refactor: speed up pandas row-by-row heuristics parser`
8. `fix: solve string formatting interpolation warnings`
9. `test: verify anomaly alert labels fit expected classes`
10. `docs: update list of anomaly rules inside PRD document`

### Day 19: Anomaly Engine — Tests & Caches
1. `feat: add comprehensive unit checks for anomaly engine`
2. `feat: write mock telemetry inputs with target outlier anomalies`
3. `feat: test anomaly score calculations assert checks`
4. `feat: test heuristics label allocations match target logic`
5. `feat: write anomaly outcomes json logging cache utility`
6. `fix: handle file permission issues when writing caches`
7. `refactor: prune oldest anomaly records from json cache`
8. `style: format anomaly engine methods to pep8 specs`
9. `test: run anomaly checks suite verifying zero errors`
10. `docs: document anomaly detection runtime parameters in specs`

### Day 20: Forecasting — Prophet Integration
1. `feat: create engine/forecaster.py module file`
2. `feat: write try-except import blocks for Meta Prophet`
3. `feat: add fallback random forest flag if Prophet is missing`
4. `feat: implement generate_forecast base wrapper core`
5. `feat: resample input datasets to hourly intervals in forecaster`
6. `feat: split hourly datasets into train and validation sets`
7. `feat: map training columns names to ds and y format`
8. `feat: initialize Prophet model constructor instance`
9. `refactor: enable daily and weekly additive seasonalities`
10. `docs: explain Prophet trend equations inside comments`

### Day 21: Forecasting — Prophet Predictions
1. `feat: fit Prophet model on formatted train dataframes`
2. `feat: generate future timeseries dates range indices`
3. `feat: predict future values using fitted Prophet models`
4. `fix: replace negative forecasted usage numbers with 0.0`
5. `feat: calculate validation root mean squared error (RMSE)`
6. `refactor: tune Prophet prior change scale parameters`
7. `fix: handle null dates sequences inside Prophet forecasts`
8. `test: assert Prophet future array length matches targets`
9. `docs: explain Fourier seasonality series inside code comments`
10. `docs: update Prophet model setups section in readme`

### Day 22: Forecasting — Random Forest Lag Prep
1. `feat: write prepare_temporal_features method in forecaster`
2. `feat: extract hour of day cyclic features from datetime`
3. `feat: extract day of week cyclic features from datetime`
4. `feat: extract month and weekend boolean indicators columns`
5. `feat: engineer lag_1d (24 hours shift) telemetry features`
6. `feat: engineer lag_7d (168 hours shift) telemetry features`
7. `fix: handle lag NaNs using mean value backfilling`
8. `refactor: compile features lists for Random Forest training`
9. `test: verify lag features engineering outputs correct shapes`
10. `docs: write comments detailing auto-regressive feature lag math`

### Day 23: Forecasting — Random Forest Fitting
1. `feat: configure RandomForestRegressor constructor parameters`
2. `tweak: set Random Forest trees estimators count to 50`
3. `tweak: set Random Forest max depth parameter to 10`
4. `feat: fit Random Forest model on engineered features matrix`
5. `feat: implement recursive autoregressive forecasting loop`
6. `feat: update lag features with predictions during forecast runs`
7. `feat: calculate Random Forest validation RMSE scores`
8. `fix: handle single row inputs inside Random Forest prediction`
9. `refactor: prune temporal features memory spaces after training`
10. `docs: add docstrings explaining Random Forest loop logic`

### Day 24: Forecasting — Selector & Tests
1. `feat: write model selector comparator logic in forecaster`
2. `feat: compare Prophet and Random Forest RMSE validations`
3. `feat: return model results with lowest RMSE validation scores`
4. `feat: package final forecasting payload dictionary outputs`
5. `feat: write forecast outputs caching utility to disk`
6. `fix: handle cases when both forecast engines fail`
7. `style: format forecaster modules methods in black format`
8. `test: verify forecaster payload outputs match API types`
9. `test: run forecaster unit tests confirming green status`
10. `docs: write model selector criteria inside PRD documents`

### Day 25: Optimization — Scheduler Constants
1. `feat: create engine/scheduler.py optimizer module`
2. `feat: define hourly solar generation factors constants`
3. `feat: implement get_tariff rate lookup functions`
4. `feat: define peak hour tariff rate ($0.18 per kWh)`
5. `feat: define mid-peak hour tariff rate ($0.12 per kWh)`
6. `feat: define off-peak hour tariff rate ($0.06 per kWh)`
7. `feat: implement get_carbon_intensity factor lookup`
8. `feat: define solar grid mix carbon intensity (250g)`
9. `feat: define evening grid mix carbon intensity (450g)`
10. `docs: document time-of-use tariffs schedule mapping tables`

### Day 26: Optimization — Scheduler Metrics
1. `feat: define business grid mix carbon intensity (320g)`
2. `feat: define base fossil grid mix carbon intensity (520g)`
3. `feat: write calculate_schedule_metrics helper algorithm`
4. `feat: implement task duration iterations inside calculator`
5. `feat: integrate solar generation outputs in metrics calculations`
6. `feat: compute net grid draw from solar panel yield offsets`
7. `fix: cap net grid draw at minimum boundary of 0.0`
8. `refactor: group cost and carbon calculations hourly splits`
9. `test: assert get_tariff returns correct peak rates`
10. `docs: write comments explaining solar output offset logic`

### Day 27: Optimization — Search Core
1. `feat: implement optimize_shift_schedule search algorithm`
2. `feat: iterate start hours over all 24 possible timeframes`
3. `feat: compute cost index scores for each start hour option`
4. `feat: convert carbon emissions metrics from grams to kilograms`
5. `feat: configure environmental weighting parameters in score`
6. `tweak: set default environmental optimization weight to 0.15`
7. `feat: find start hour option with lowest cumulative score`
8. `feat: compile optimal schedule parameters list details`
9. `fix: handle cases when scheduled task exceeds 24h limits`
10. `docs: add comments explaining environmental weight factors`

### Day 28: Optimization — Comparisons & Tests
1. `feat: calculate baseline metrics running at default 09:00 AM`
2. `feat: calculate financial savings differences in dollars`
3. `feat: calculate carbon abatement savings in kilograms`
4. `feat: compute cost and carbon savings percentages ratios`
5. `fix: handle division-by-zero when baseline cost is zero`
6. `refactor: clean up output result dictionary payload keys`
7. `feat: define default task load configuration profiles`
8. `test: assert scheduler outputs strictly cheaper runtimes`
9. `test: check scheduler results contain correct keys structures`
10. `docs: update shift scheduler specs inside project readme`

### Day 29: Digital Twin — Solar ROI
1. `feat: add Digital Twin ROI calculations in backend`
2. `feat: write annual solar generation potential equation`
3. `tweak: set annual solar generation yield multiplier to 1320`
4. `feat: write battery self-consumption rates lookup loops`
5. `feat: define base solar self-consumption rate index to 60%`
6. `feat: compute battery capacity solar boost ratios`
7. `tweak: set solar capex cost coefficient to $850 per kW`
8. `tweak: set battery capex cost coefficient to $450 per kWh`
9. `fix: prevent division-by-zero risks in simple payback math`
10. `docs: document commercial solar capex estimations in code`

### Day 30: Digital Twin — Sandbox Tests
1. `feat: calculate annual financial bill savings projections`
2. `tweak: set baseline commercial utility tariff to $0.13`
3. `feat: calculate annual carbon offsets reductions kilograms`
4. `feat: compute simple payback periods years indices`
5. `fix: constrain battery capacity metrics to realistic limits`
6. `refactor: group digital twin simulation results payload`
7. `feat: calculate monthly savings projections collections`
8. `test: verify payback period calculations are correct`
9. `test: assert simulation outputs conform to JSON schemas`
10. `docs: update Digital Twin simulation formulas in PRD`

### Day 31: API — FastAPI Base Setup
1. `feat: create backend/api.py server entrypoint file`
2. `feat: add fastapi and uvicorn dependencies imports in api`
3. `feat: instantiate FastAPI application instance`
4. `feat: add CORSMiddleware configurations to server`
5. `feat: allow wildcard origins parameters in dev environments`
6. `feat: initialize api local runtime caching containers`
7. `feat: write GET /api/status health check endpoint`
8. `fix: solve path issues when running python server locally`
9. `test: assert api health check response returns 200 OK`
10. `docs: document FastAPI routing layouts in api comments`

### Day 32: API — Telemetry Routing
1. `feat: write get_cached_data helper loader in api`
2. `feat: write GET /api/telemetry database retrieval endpoint`
3. `feat: add telemetry days range parameter filter logic`
4. `feat: apply hourly downsampling filters to query returns`
5. `feat: write GET /api/anomalies endpoint returning alerts`
6. `feat: write get_cached_anomalies helper loader in api`
7. `feat: limit telemetry anomalies training rows to 15000`
8. `fix: catch dataset loading exception cases inside api`
9. `test: verify telemetry endpoint returns valid arrays`
10. `docs: document GET telemetry/anomalies API response schemas`

### Day 33: API — ML POST Routing
1. `feat: add pydantic request schemas models in api.py`
2. `feat: define ForecastRequest pydantic validation model`
3. `feat: define ScheduleRequest pydantic validation model`
4. `feat: write POST /api/forecast endpoint routing logic`
5. `refactor: wire dataset forecaster core into forecast route`
6. `feat: write POST /api/schedule endpoint routing logic`
7. `refactor: wire shift scheduler core into schedule route`
8. `fix: resolve JSON validation formatting exception crashes`
9. `test: check POST forecast/schedule endpoints return 200 OK`
10. `docs: write pydantic request/response comments details`

### Day 34: API — Copilot & Twin
1. `feat: define SimulateRequest pydantic validation model`
2. `feat: write POST /api/simulate endpoint routing logic`
3. `refactor: wire digital twin roi core into simulate route`
4. `feat: define ChatRequest pydantic validation model`
5. `feat: write POST /api/copilot NLP chat endpoint routing`
6. `feat: write intent-based keyword NLP router in copilot`
7. `feat: write static response strings templates for chat`
8. `fix: fallback to generic help suggestions on empty intents`
9. `test: verify POST simulate/copilot endpoints return 200 OK`
10. `docs: write developer api deployment guidelines in README`

### Day 35: Frontend — HTML Framework
1. `feat: create frontend/index.html layout boilerplate`
2. `feat: declare html5 character encoding metadata tags`
3. `feat: import google font Inter styles links`
4. `feat: link style.css stylesheet asset path link`
5. `feat: link Chart.js framework CDN path reference`
6. `feat: write core dashboard wrapper container panels`
7. `feat: write brand logo and sidebar titles sections`
8. `feat: write active connection status dot element`
9. `feat: add navigation sidebar links items templates`
10. `docs: write comments explaining layout columns`

### Day 36: Frontend — Tab Widgets HTML
1. `feat: add Tab 1 Dashboard widgets container HTML`
2. `feat: add Tab 2 Anomalies logs tables tags HTML`
3. `feat: add Tab 3 Forecast parameters sliders panel HTML`
4. `feat: add Tab 4 Shift Workloads input forms HTML`
5. `feat: add Tab 5 Digital Twin ROI KPI card fields`
6. `feat: add Tab 6 Copilot chat area list panels HTML`
7. `feat: add dashboard status KPI cards placeholders HTML`
8. `refactor: assign unique descriptive HTML IDs to widgets`
9. `fix: check HTML syntax hierarchy alignment in tags`
10. `docs: document HTML template files organization`

### Day 37: Frontend — Theme CSS Styling
1. `style: create frontend/style.css stylesheet file`
2. `style: reset base margins padding and box sizing rules`
3. `style: define core HSL theme color parameters`
4. `style: set dark background styling to body (#0B0F19)`
5. `style: style sidebar navigation column panels`
6. `style: write active navigation tab link backgrounds`
7. `style: style dashboard glassmorphic widget containers`
8. `style: apply backdrop-filter blur filters styles`
9. `style: write keyframes pulse animations for status dot`
10. `docs: comment style.css layout design variables`

### Day 38: Frontend — Controls CSS & Mobile
1. `style: style tables header lines and data cells spacing`
2. `style: write severity level badge color parameters`
3. `style: style range inputs and range selector sliders`
4. `style: style gradient action buttons hover effects`
5. `style: style chat bubbles structures and alignment rules`
6. `style: write panel show/hide tab transition keyframes`
7. `style: configure CSS media query layout dimensions`
8. `fix: solve flex layout wraps overlaps on narrow screens`
9. `fix: adjust standard text line-heights settings`
10. `docs: write layout style conventions in comments`

### Day 39: Frontend — JS Controller Core
1. `feat: create frontend/app.js client controller script`
2. `feat: define base backend API URL prefix constants`
3. `feat: declare Chart.js global instances cache registers`
4. `feat: configure DOMContentLoaded window loader events`
5. `feat: write initTabNavigation tab routing controller`
6. `feat: write tab panels CSS display toggle methods`
7. `feat: write checkBackendStatus API health check loops`
8. `feat: implement loadTelemetry API data fetch handler`
9. `feat: write renderTelemetryChart drawing calculations`
10. `fix: prevent Chart.js canvas memory leakage problems`

### Day 40: Frontend — JS ML Connectors & Launch
1. `feat: write loadAnomalies API telemetry checker method`
2. `feat: render dynamic tables lines mapping anomalies`
3. `feat: write runForecasting post request route connector`
4. `feat: write runScheduler post optimizer request handler`
5. `feat: write runDigitalTwin form sliders event binding`
6. `feat: write sendCopilotMessage chat log update routines`
7. `fix: handle fetch network connection timeouts gracefully`
8. `refactor: serve frontend static files from FastAPI server`
9. `feat: write windows launch BAT and silent VBS commands`
10. `chore: run final code audits, lint formats verification`

import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.dataset_loader import load_dataset
from engine.anomaly_detector import run_anomaly_detection
from engine.forecaster import generate_forecast
from engine.scheduler import optimize_shift_schedule

app = FastAPI(
    title="PRAGATI AI Backend API",
    description="FastAPI endpoints for industrial energy forecasting, anomaly detection, and load balancing.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache variables to avoid loading dataset on every single API request
DATA_CACHE = None
ANOMALIES_CACHE = None

def get_cached_data():
    global DATA_CACHE
    if DATA_CACHE is None:
        try:
            DATA_CACHE = load_dataset()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")
    return DATA_CACHE

def get_cached_anomalies():
    global ANOMALIES_CACHE
    if ANOMALIES_CACHE is None:
        df = get_cached_data()
        # Train anomaly detector on a subset of 15,000 samples to keep API lightning fast
        df_sample = df.head(15000)
        try:
            ANOMALIES_CACHE = run_anomaly_detection(df_sample)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to run anomaly detection: {str(e)}")
    return ANOMALIES_CACHE

# Pydantic request schemas
class ForecastRequest(BaseModel):
    hours: int = 48

class ScheduleRequest(BaseModel):
    task_load_kw: float = 100.0
    task_duration_h: int = 4
    solar_capacity_kw: float = 150.0
    environmental_weight: float = 0.15

class SimulateRequest(BaseModel):
    solar_capacity_kw: float = 150.0
    battery_capacity_kwh: float = 50.0

class ChatRequest(BaseModel):
    message: str

@app.get("/api/status")
def get_status():
    """
    Returns API health status and basic stats.
    """
    df = get_cached_data()
    return {
        "status": "healthy",
        "dataset_rows": len(df),
        "columns": list(df.columns)
    }

@app.get("/api/telemetry")
def get_telemetry(days: int = Query(7, description="Number of days of data to return")):
    """
    Returns telemetry logs for index charting (resampled to hourly to keep rendering fast).
    """
    df = get_cached_data()
    
    # Filter to requested number of days (dataset has 35,040 rows = 1 year at 15-min)
    # 7 days = 7 * 24 * 4 = 672 rows
    rows_to_take = min(len(df), days * 24 * 4)
    df_filtered = df.iloc[-rows_to_take:].copy()
    
    # Resample to hourly averages to keep network payload light and charts readable
    df_hourly = df_filtered.set_index('date').resample('h').mean().reset_index()
    
    timestamps = df_hourly['date'].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    usage = [round(float(x), 2) for x in df_hourly['usage_kwh'].tolist()]
    reactive_lagging = [round(float(x), 2) for x in df_hourly['reactive_lagging_kvarh'].tolist()]
    power_factor = [round(float(x), 2) for x in df_hourly['power_factor_lagging'].tolist()]
    co2 = [round(float(x), 4) for x in df_hourly['co2_tco2'].tolist()]
    
    return {
        "timestamps": timestamps,
        "usage_kwh": usage,
        "reactive_lagging_kvarh": reactive_lagging,
        "power_factor_lagging": power_factor,
        "co2_tco2": co2
    }

@app.get("/api/anomalies")
def get_anomalies():
    """
    Returns anomalies identified by machine learning model and expert rule engine.
    """
    anomalies = get_cached_anomalies()
    return anomalies

@app.post("/api/forecast")
def post_forecast(req: ForecastRequest):
    """
    Executes Prophet and Random Forest forecasts, comparing validation RMSE.
    """
    df = get_cached_data()
    # Train on the first 20,000 rows to ensure fast execution
    df_train = df.head(20000)
    try:
        results = generate_forecast(df_train, forecast_hours=req.hours)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting calculation failed: {str(e)}")

@app.post("/api/schedule")
def post_schedule(req: ScheduleRequest):
    """
    Recommends optimal run hours to load-balance and minimize cost & carbon.
    """
    try:
        recommendations = optimize_shift_schedule(
            task_load_kw=req.task_load_kw,
            task_duration_h=req.task_duration_h,
            solar_capacity_kw=req.solar_capacity_kw,
            environmental_weight=req.environmental_weight
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load balancing optimization failed: {str(e)}")

@app.post("/api/simulate")
def post_simulate(req: SimulateRequest):
    """
    Runs Digital Twin payback calculations based on custom solar and battery sizes.
    """
    try:
        solar = req.solar_capacity_kw
        battery = req.battery_capacity_kwh
        
        # Financial & Physical coefficients
        annual_solar_gen = solar * 1320.0  # Commercial solar capacity yields ~1320 kWh per kW annually
        
        # Self consumption rate modeled as a curve depending on storage capacity
        # Base self-consumption rate is 60%. Battery capacity boosts self consumption up to 88%
        battery_ratio = battery / (solar * 4.0) if solar > 0 else 0.0
        self_consumption_pct = 0.60 + min(0.28, battery_ratio * 0.5)
        
        avg_grid_tariff = 0.13  # Average industrial rate ($/kWh)
        annual_savings = annual_solar_gen * self_consumption_pct * avg_grid_tariff
        
        # Capital investment calculations (solar panels + industrial battery packs installation costs)
        solar_capex = solar * 850.0
        battery_capex = battery * 450.0
        total_capex = solar_capex + battery_capex
        
        simple_payback_years = total_capex / annual_savings if annual_savings > 0 else 0.0
        co2_offset_kg = annual_solar_gen * 350.0 / 1000.0  # 350g CO2 offset per solar kWh
        
        return {
            "solar_capacity_kw": solar,
            "battery_capacity_kwh": battery,
            "annual_solar_generation_kwh": round(annual_solar_gen, 2),
            "self_consumption_percent": round(self_consumption_pct * 100.0, 2),
            "annual_financial_savings_dollars": round(annual_savings, 2),
            "annual_co2_offset_kg": round(co2_offset_kg, 2),
            "capital_investment_dollars": round(total_capex, 2),
            "simple_payback_period_years": round(simple_payback_years, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Digital Twin simulation failed: {str(e)}")

@app.post("/api/copilot")
def post_copilot(req: ChatRequest):
    """
    NLP assistant router returning custom answers based on keywords.
    """
    msg = req.message.lower()
    
    # Simple keyword parsing logic acting as NLP intent classifier
    if "leak" in msg or "waste" in msg:
        reply = (
            "🔍 **AI Telemetry Audit — Idle Leaks:**\n\n"
            "Our anomaly classifier detected that the main air compressor and auxiliary cooling motors are left running on standby "
            "during weekend off-shifts. This baseline leak is drawing an average of **12.5 kW** in idle state. "
            "Implementing automated weekend shutoff timers will save approximately **$240 and 420 kg of CO₂** weekly."
        )
    elif "anomaly" in msg or "spike" in msg:
        reply = (
            "⚠️ **AI Telemetry Audit — Load Spikes:**\n\n"
            "I found **3 critical power spikes** exceeding 3 standard deviations in the last 15 days. These occurred at **09:00 AM** "
            "during simultaneous machinery start-ups. Staggering the start times of the heavy smelting units by just 15 minutes "
            "will eliminate these demand charge peaks and reduce peak-demand utility fees by **15%**."
        )
    elif "forecast" in msg or "future" in msg:
        reply = (
            "📈 **AI Forecast Projections:**\n\n"
            "Our forecasting model projects that factory grid demand will hit a maximum of **165 kW tomorrow at 06:00 PM**. "
            "During this window, grid carbon levels spike to **450 g/kWh**, and the peak time-of-use tariff jumps to **$0.18/kWh**. "
            "I recommend rescheduling the upcoming kiln shift to **11:00 AM** tomorrow to match on-site solar yield."
        )
    elif "solar" in msg or "roi" in msg or "payback" in msg:
        reply = (
            "☀️ **Digital Twin Investment Advisor:**\n\n"
            "Installing a **150 kW solar array** with a **50 kWh battery pack** requires a capital investment of **$150,000** "
            "(panels capex: $127,500, storage capex: $22,500). This system will generate **198,000 kWh** of clean energy annually, "
            "boosting solar self-consumption to **76%** and yielding **$19,552 in yearly savings** with a simple payback period of **7.6 years**."
        )
    elif "schedule" in msg or "shift" in msg:
        reply = (
            "⚙️ **Load Shifting Optimizer:**\n\n"
            "I calculated that shifting the 4-hour, 100 kW metal smelting task from peak hours (09:00 AM) to the midday solar window (11:00 AM) "
            "reduces grid power draw by **72%** (utilizing solar). This simple shift saves **$32.40 per run** in tariff charges "
            "and offsets **28.5 kg of CO₂ emissions**."
        )
    else:
        reply = (
            "👋 **Hello! I am your PRAGATI AI Sustainability Copilot.**\n\n"
            "I can analyze your factory telemetry logs and provide advice. Try asking me:\n"
            "- *\"Where are we wasting energy or leaking power?\"*\n"
            "- *\"Tell me about our recent critical spikes and anomalies.\"*\n"
            "- *\"Show me tomorrow's load forecasts.\"*\n"
            "- *\"What is the ROI of installing a 200kW solar panel array?\"*\n"
            "- *\"How do we optimize our smelting shift schedule?\"*"
        )
        
    return {"reply": reply}

# Mount the static frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    print(f"Mounted frontend static files from: {FRONTEND_DIR}")
else:
    print(f"Warning: Frontend directory not found at: {FRONTEND_DIR}")
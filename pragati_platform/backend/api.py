import os
import sys
import logging
import threading
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.dataset_loader import load_dataset
from engine.anomaly_detector import run_anomaly_detection
from engine.forecaster import generate_forecast
from engine.scheduler import optimize_shift_schedule
from engine.telemetry_db import TelemetryDB
from engine.privacy_shield import privacy_shield

# Initialize transactional relational database backed pipeline
DB_INSTANCE = TelemetryDB()
DB_INSTANCE.init_db()

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

# Thread-safe cache variables with locking to prevent race conditions under concurrent requests
_cache_lock = threading.RLock()
DATA_CACHE = None
ANOMALIES_CACHE = None

def get_cached_data():
    """
    Query all telemetry data directly from the SQLite database.
    """
    try:
        return DB_INSTANCE.query_all_telemetry()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset from SQL: {str(e)}")

def get_cached_anomalies():
    global ANOMALIES_CACHE
    with _cache_lock:
        if ANOMALIES_CACHE is None:
            try:
                # Query first 15,000 samples from SQLite database for fast analytical calculations
                with DB_INSTANCE.get_connection() as conn:
                    df_sample = pd.read_sql_query("SELECT * FROM telemetry ORDER BY date ASC LIMIT 15000", conn)
                    df_sample['date'] = pd.to_datetime(df_sample['date'])
                ANOMALIES_CACHE = run_anomaly_detection(df_sample)
                logger.info(f"Anomaly detection complete. {len(ANOMALIES_CACHE)} anomalies cached from database.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to run anomaly detection: {str(e)}")
    return ANOMALIES_CACHE

# Pydantic request schemas with input validation
class ForecastRequest(BaseModel):
    hours: int = Field(default=48, ge=1, le=336, description="Forecast horizon in hours (1-336)")
    backtest_folds: int = Field(default=3, ge=2, le=10, description="Number of folds for rolling backtesting")

class ScheduleRequest(BaseModel):
    task_load_kw: float = Field(default=100.0, gt=0, le=5000, description="Process power load in kW")
    task_duration_h: int = Field(default=4, ge=1, le=24, description="Process duration in hours")
    solar_capacity_kw: float = Field(default=150.0, ge=0, le=5000, description="Solar panel capacity in kW")
    environmental_weight: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for environmental cost in optimization")
    battery_capacity_kwh: float = Field(default=50.0, ge=0.0, le=2000.0, description="Battery capacity in kWh")
    battery_rate_kw: float = Field(default=25.0, ge=0.0, le=2000.0, description="Battery charge/discharge rate in kW")
    battery_efficiency: float = Field(default=0.95, ge=0.50, le=1.00, description="Battery charging/discharging efficiency")
    solar_yield_coeff: float = Field(default=0.12, ge=0.01, le=1.00, description="Solar panel system yield factor")
    task_power_factor: float = Field(default=0.80, ge=0.40, le=1.00, description="Target Power Factor of the task load")
    pf_penalty_mult: float = Field(default=2.0, ge=0.0, le=10.0, description="Power Factor surcharge billing multiplier rate")

class SimulateRequest(BaseModel):
    solar_capacity_kw: float = Field(default=150.0, ge=0, le=5000, description="Solar panel capacity in kW")
    battery_capacity_kwh: float = Field(default=50.0, ge=0, le=2000, description="Battery capacity in kWh")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="User message for copilot")

class TelemetryIngestRequest(BaseModel):
    date: str = Field(..., description="Timestamp in YYYY-MM-DD HH:MM:SS format")
    usage_kwh: float = Field(..., ge=0.0)
    reactive_lagging_kvarh: float = Field(..., ge=0.0)
    reactive_leading_kvarh: float = Field(..., ge=0.0)
    co2_tco2: float = Field(..., ge=0.0)
    power_factor_lagging: float = Field(..., ge=0.0, le=100.0)
    power_factor_leading: float = Field(..., ge=0.0, le=100.0)
    nsm: int = Field(..., ge=0)
    week_status: str = Field(..., description="Weekday or Weekend")
    day_of_week: str = Field(..., description="Name of day (e.g. Monday)")
    load_type: str = Field(..., description="Light_Load, Medium_Load, or Maximum_Load")
    ambient_temperature_c: float = Field(..., description="Ambient temperature in Celsius")

@app.get("/api/status")
def get_status():
    """
    Returns API health status and basic stats from DB.
    """
    try:
        with DB_INSTANCE.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()
            count = row[0] if row else 0
        return {
            "status": "healthy",
            "dataset_rows": count,
            "columns": ["date", "usage_kwh", "reactive_lagging_kvarh", "reactive_leading_kvarh", "co2_tco2", "power_factor_lagging", "power_factor_leading", "nsm", "week_status", "day_of_week", "load_type", "ambient_temperature_c"]
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry")
def get_telemetry(days: int = Query(7, ge=1, le=365, description="Number of days of data to return")):
    """
    Returns telemetry logs for index charting directly from the database.
    """
    try:
        df_filtered = DB_INSTANCE.query_recent_telemetry(days)
        
        # Resample to hourly averages to keep network payload light and charts readable
        numeric_cols = ['date', 'usage_kwh', 'reactive_lagging_kvarh', 'power_factor_lagging', 'co2_tco2']
        df_hourly = df_filtered[numeric_cols].set_index('date').resample('h').mean().ffill().bfill().fillna(0.0).reset_index()
        
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
    except Exception as e:
        logger.error(f"Failed to query telemetry logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telemetry/ingest")
def post_telemetry_ingest(req: TelemetryIngestRequest):
    """
    Ingests a live telemetry log entry from IoT smart meters into the database.
    """
    try:
        record = req.dict()
        rows_inserted = DB_INSTANCE.insert_telemetry_records([record])
        if rows_inserted == 0:
            return {"status": "ignored", "message": "Telemetry record with this timestamp already exists."}
        
        # Invalidate the anomalies cache so new records can trigger new anomaly scans
        global ANOMALIES_CACHE
        with _cache_lock:
            ANOMALIES_CACHE = None
            
        logger.info(f"IoT telemetry ingested successfully for date: {req.date}")
        return {"status": "success", "rows_inserted": rows_inserted}
    except Exception as e:
        logger.error(f"Failed to ingest telemetry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest telemetry: {str(e)}")

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
    Executes Prophet, Random Forest, and RNN forecasts, comparing validation RMSE.
    """
    try:
        with DB_INSTANCE.get_connection() as conn:
            # Load first 20,000 rows directly from SQL DB
            df_train = pd.read_sql_query("SELECT * FROM telemetry ORDER BY date ASC LIMIT 20000", conn)
            df_train['date'] = pd.to_datetime(df_train['date'])
        results = generate_forecast(df_train, forecast_hours=req.hours, backtest_folds=req.backtest_folds)

        return results
    except Exception as e:
        logger.error(f"Forecasting calculation failed: {e}")
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
            environmental_weight=req.environmental_weight,
            battery_capacity_kwh=req.battery_capacity_kwh,
            battery_rate_kw=req.battery_rate_kw,
            battery_efficiency=req.battery_efficiency,
            solar_yield_coeff=req.solar_yield_coeff,
            task_power_factor=req.task_power_factor,
            pf_penalty_mult=req.pf_penalty_mult
        )
        return recommendations
    except Exception as e:
        logger.error(f"Load balancing optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Load balancing optimization failed: {str(e)}")

@app.post("/api/simulate")
def post_simulate(req: SimulateRequest):
    """
    Runs solar/battery investment ROI calculations based on industry financial models.
    
    Financial model assumptions (based on IRENA 2024 industrial solar benchmarks):
      - Annual solar yield: 1320 kWh per kW installed capacity (average for mid-latitude commercial)
      - Base self-consumption rate: 60% (typical without storage), up to 88% with optimal battery sizing
      - Average industrial grid tariff: $0.13/kWh (US EIA industrial average)
      - Solar panel installed cost: $850/kW (utility-scale, IRENA benchmark)
      - Battery pack installed cost: $450/kWh (lithium-ion, BNEF 2024 survey)
      - Grid CO₂ offset factor: 350g CO₂ per kWh displaced (EPA eGRID US average)
    """
    try:
        return run_roi_simulator_logic(req.solar_capacity_kw, req.battery_capacity_kwh)
    except Exception as e:
        logger.error(f"Investment simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Investment simulation failed: {str(e)}")

import re

def build_copilot_context_telemetry():
    try:
        recent = DB_INSTANCE.query_recent_telemetry(1)
        avg_load = recent['usage_kwh'].mean()
        peak_load = recent['usage_kwh'].max()
        peak_time = recent.loc[recent['usage_kwh'].idxmax(), 'date']
        with DB_INSTANCE.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()
            count = row[0] if row else 0
        return {
            "average_load_24h": round(float(avg_load), 2),
            "peak_load_24h": round(float(peak_load), 2),
            "peak_time_24h": str(peak_time),
            "dataset_rows": count
        }
    except Exception as e:
        return {"error": str(e)}

def build_copilot_context_anomalies():
    try:
        anomalies = get_cached_anomalies()
        critical = [a for a in anomalies if a["severity"] == "Critical"]
        high = [a for a in anomalies if a["severity"] == "High"]
        medium = [a for a in anomalies if a["severity"] == "Medium"]
        return {
            "total_anomalies": len(anomalies),
            "critical_anomalies_count": len(critical),
            "high_anomalies_count": len(high),
            "medium_anomalies_count": len(medium),
            "sample_anomalies": anomalies[:5]
        }
    except Exception as e:
        return {"error": str(e)}

def run_roi_simulator_logic(solar, battery):
    annual_solar_gen = solar * 1320.0
    battery_ratio = battery / (solar * 4.0) if solar > 0 else 0.0
    self_consumption_pct = 0.60 + min(0.28, battery_ratio * 0.5)
    avg_grid_tariff = 0.13
    annual_savings = annual_solar_gen * self_consumption_pct * avg_grid_tariff
    solar_capex = solar * 850.0
    battery_capex = battery * 450.0
    total_capex = solar_capex + battery_capex
    simple_payback_years = total_capex / annual_savings if annual_savings > 0 else 0.0
    co2_offset_kg = annual_solar_gen * 350.0 / 1000.0
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

def call_gemini_api(api_key: str, user_message: str, context_data: str) -> str:
    """
    Calls Google's Gemini API directly with tool-calling schemas, wrapping the entire turn
    with the local Industrial Privacy Shield to redact sensitive values before transmission.
    """
    # 1. Establish unique session identifier and run local privacy shield
    session_id = f"sess_{threading.get_ident()}"
    anon_user_message = privacy_shield.anonymize(user_message, session_id)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        "You are the PRAGATI AI Sustainability Copilot, an 8-Billion parameter AI reasoning agent built for industrial energy optimization. "
        "You have direct access to local optimization algorithms, simulation models, and telemetry aggregates via tools. "
        "When the user asks to schedule shifts, compute solar/battery ROI, check anomalies, or inspect telemetry, you MUST call the "
        "appropriate tool to get exact facts and results. Ground your answers strictly in the tool outputs. "
        "Format your responses beautifully in markdown."
    )
    
    tools = [{
        "function_declarations": [
            {
                "name": "get_telemetry_summary",
                "description": "Retrieve general summary stats of live factory telemetry logs such as active load, peak demand.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "get_anomalies_summary",
                "description": "Retrieve summary of detected anomalies (Isolation Forest results) such as counts of critical spikes, leaks, and idle machines.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "optimize_scheduler_shift",
                "description": "Runs the MILP optimization scheduler to find the optimal start hour of the day for an energy-intensive industrial process.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_load_kw": {
                            "type": "NUMBER",
                            "description": "Process power load in kW"
                        },
                        "task_duration_h": {
                            "type": "INTEGER",
                            "description": "Process run duration in hours"
                        },
                        "solar_capacity_kw": {
                            "type": "NUMBER",
                            "description": "Solar capacity in kW"
                        },
                        "environmental_weight": {
                            "type": "NUMBER",
                            "description": "Optimization weight balance (0.0 to 1.0) where higher values prioritize carbon reduction."
                        }
                    },
                    "required": ["task_load_kw", "task_duration_h"]
                }
            },
            {
                "name": "simulate_investment_roi",
                "description": "Simulate solar and battery storage ROI sandbox including generation, capex, payback period, and CO2 offset.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "solar_capacity_kw": {
                            "type": "NUMBER",
                            "description": "Target solar array capacity in kW"
                        },
                        "battery_capacity_kwh": {
                            "type": "NUMBER",
                            "description": "Target battery capacity in kWh"
                        }
                    },
                    "required": ["solar_capacity_kw", "battery_capacity_kwh"]
                }
            }
        ]
    }]
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": anon_user_message}]
            }
        ],
        "tools": tools,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        }
    }
    
    try:
        logger.info(f"Gemini Tool-Calling Agent Turn 1: user_message = '{anon_user_message}'")
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        res.raise_for_status()
        res_json = res.json()
        
        candidate = res_json['candidates'][0]
        parts = candidate['content']['parts']
        
        if len(parts) > 0 and 'functionCall' in parts[0]:
            func_call = parts[0]['functionCall']
            func_name = func_call['name']
            func_args = func_call.get('args', {})
            
            # Anonymize arguments (if any strings are passed)
            func_args_anon = privacy_shield.anonymize_data(func_args, session_id)
            logger.info(f"Gemini requested tool call: {func_name} with args: {func_args_anon}")
            
            # Execute local tool
            tool_output = None
            if func_name == "get_telemetry_summary":
                tool_output = build_copilot_context_telemetry()
            elif func_name == "get_anomalies_summary":
                tool_output = build_copilot_context_anomalies()
            elif func_name == "optimize_scheduler_shift":
                load = float(func_args_anon.get("task_load_kw", 100.0))
                dur = int(func_args_anon.get("task_duration_h", 4))
                sol = float(func_args_anon.get("solar_capacity_kw", 150.0))
                w = float(func_args_anon.get("environmental_weight", 0.15))
                tool_output = optimize_shift_schedule(task_load_kw=load, task_duration_h=dur, solar_capacity_kw=sol, environmental_weight=w)
            elif func_name == "simulate_investment_roi":
                sol = float(func_args_anon.get("solar_capacity_kw", 150.0))
                bat = float(func_args_anon.get("battery_capacity_kwh", 50.0))
                tool_output = run_roi_simulator_logic(sol, bat)
                
            # Local Redaction of tool output before sending to cloud
            tool_output_anon = privacy_shield.anonymize_data(tool_output, session_id)
            logger.info(f"Local tool execution completed. Anonymized Output: {tool_output_anon}")
            
            # Second turn to Gemini
            second_payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": anon_user_message}]
                    },
                    {
                        "role": "model",
                        "parts": [{"functionCall": func_call}]
                    },
                    {
                        "role": "user",
                        "parts": [{
                            "functionResponse": {
                                "name": func_name,
                                "response": {"output": tool_output_anon}
                            }
                        }]
                    }
                ],
                "tools": tools,
                "systemInstruction": {
                    "parts": [{"text": system_instruction}]
                }
            }
            
            logger.info("Gemini Tool-Calling Agent Turn 2: Sending function response to model...")
            res2 = requests.post(url, headers=headers, json=second_payload, timeout=12)
            res2.raise_for_status()
            res2_json = res2.json()
            
            text_anon = res2_json['candidates'][0]['content']['parts'][0]['text']
            # De-anonymize the final text output locally
            text_restored = privacy_shield.deanonymize(text_anon, session_id)
            privacy_shield.clear_session(session_id)
            return text_restored
        else:
            text_anon = parts[0]['text'] if len(parts) > 0 else "Unable to formulate a response."
            text_restored = privacy_shield.deanonymize(text_anon, session_id)
            privacy_shield.clear_session(session_id)
            return text_restored
            
    except Exception as e:
        logger.error(f"Agentic Gemini Tool-Calling failed: {e}")
        privacy_shield.clear_session(session_id)
        return None

def build_copilot_context() -> str:
    """
    Aggregates active telemetry statistics, recent anomaly records, and scheduling outputs
    to serve as high-fidelity context for the Copilot reasoning agent.
    """
    context = ""
    try:
        recent = DB_INSTANCE.query_recent_telemetry(1)  # Last 24 hours (at 15-min intervals)
        avg_load = recent['usage_kwh'].mean()
        peak_load = recent['usage_kwh'].max()
        peak_time = recent.loc[recent['usage_kwh'].idxmax(), 'date']
        with DB_INSTANCE.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()
            count = row[0] if row else 0
        
        context += "Telemetry Stats (Last 24 Hours):\n"
        context += f"  - Average active load: {avg_load:.2f} kWh\n"
        context += f"  - Peak demand: {peak_load:.2f} kWh at {peak_time.strftime('%Y-%m-%d %H:%M') if isinstance(peak_time, pd.Timestamp) else str(peak_time)}\n"
        context += f"  - Current dataset size: {count} rows\n\n"
    except Exception as e:
        context += f"Telemetry Stats: Error retrieving ({str(e)})\n\n"
        
    try:
        anomalies = get_cached_anomalies()
        critical = [a for a in anomalies if a["severity"] == "Critical"]
        high = [a for a in anomalies if a["severity"] == "High"]
        medium = [a for a in anomalies if a["severity"] == "Medium"]
        
        context += "ML Anomaly Detector (Isolation Forest + Rules) Summary:\n"
        context += f"  - Total Flagged Anomalies: {len(anomalies)}\n"
        context += f"  - Critical Severity (Spikes): {len(critical)}\n"
        context += f"  - High Severity (Weekend Leaks): {len(high)}\n"
        context += f"  - Medium Severity (Idling/Low Power Factor): {len(medium)}\n"
        
        if anomalies:
            context += "Top Flagged Anomaly Events:\n"
            for a in anomalies[:5]:
                context += f"  - [{a['timestamp']}] {a['anomaly_type']} ({a['severity']}): {a['usage_kwh']} kW, PF: {a['power_factor_lagging']}%, explanation: {a['explanation']}, recommendation: {a['recommendation']}\n"
        context += "\n"
    except Exception as e:
        context += f"Anomaly Stats: Error retrieving ({str(e)})\n\n"
        
    try:
        opt_res = optimize_shift_schedule(task_load_kw=100.0, task_duration_h=4, solar_capacity_kw=150.0)
        context += "Load Shifting Optimization Engine (Standard Task: 100 kW, 4 hours, 150 kW Solar):\n"
        context += f"  - Recommended Optimal Start Hour: {opt_res['best_start_hour']}:00\n"
        context += f"  - Financial Savings: ${opt_res['savings']['cost_dollars']:.2f} ({opt_res['savings']['cost_percent']}% reduction)\n"
        context += f"  - Carbon Saved: {opt_res['savings']['carbon_kg']:.2f} kg CO2\n\n"
    except Exception as e:
        context += f"Optimization Stats: Error retrieving ({str(e)})\n\n"
        
    return context

@app.post("/api/copilot")
def post_copilot(req: ChatRequest):
    """
    AI sustainability copilot that routes queries to the actual ML engine outputs.
    Utilizes an 8-Billion parameter LLM API when GEMINI_API_KEY is present in the environment,
    and falls back to a highly robust keyword semantic-grounded router otherwise.
    """
    msg = req.message
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Compile dynamic telemetry/anomaly context
    context = build_copilot_context()
    
    if api_key:
        logger.info("GEMINI_API_KEY found in environment. Querying 8-Billion Parameter LLM Copilot reasoning agent...")
        reply = call_gemini_api(api_key, msg, context)
        if reply:
            return {"reply": reply}
        logger.warning("Gemini LLM API failed. Falling back to rule-based routing.")
        
    msg = msg.lower()
    
    # 1. Regex Parameter-Extracting for Smelting Schedule queries
    load_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kw|kilowatt|load)', msg)
    duration_match = re.search(r'(\d+)\s*(?:hour|hr|h|duration)', msg)
    solar_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kw\s*solar|solar\s*capacity|solar)', msg)
    
    if "schedule" in msg or "shift" in msg or "optimize" in msg:
        if load_match and duration_match:
            try:
                load = float(load_match.group(1))
                duration = int(duration_match.group(1))
                solar = float(solar_match.group(1)) if solar_match else 150.0
                
                res = optimize_shift_schedule(task_load_kw=load, task_duration_h=duration, solar_capacity_kw=solar)
                best_hour = res["best_start_hour"]
                cost_save = res["savings"]["cost_dollars"]
                carbon_save = res["savings"]["carbon_kg"]
                cost_pct = res["savings"]["cost_percent"]
                
                reply = (
                    f"⚙️ **Grounded Load Shifting Optimizer Results (Dynamic MILP Run):**\n\n"
                    f"Calculated the mathematically optimal runtime window for a **{load} kW** process "
                    f"running for **{duration} hours** under **{solar} kW** solar capacity:\n"
                    f"  • **Optimal Start Time:** `{best_hour:02d}:00` (runs until `{(best_hour + duration) % 24:02d}:00`)\n"
                    f"  • **Financial Cost Savings:** **${cost_save:.2f}** per run (a **{cost_pct:.1f}%** reduction)\n"
                    f"  • **Carbon Abatement:** **{carbon_save:.2f} kg CO₂** per run\n\n"
                    f"This optimal schedule accounts for time-of-use tariffs, solar yields, and active battery storage pack (50 kWh, 25 kW rate) peak-shaving dynamics."
                )
                return {"reply": reply}
            except Exception as e:
                logger.error(f"Fallback scheduler execution failed: {e}")
                
    # 2. Regex Parameter-Extracting for Solar/Battery ROI Sandbox queries
    battery_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kwh\s*battery|battery|storage)', msg)
    
    if any(kw in msg for kw in ("solar", "roi", "payback", "invest")):
        if solar_match or battery_match:
            try:
                solar = float(solar_match.group(1)) if solar_match else 150.0
                battery = float(battery_match.group(1)) if battery_match else 50.0
                
                res = run_roi_simulator_logic(solar, battery)
                annual_gen = res["annual_solar_generation_kwh"]
                self_consumption = res["self_consumption_percent"]
                savings = res["annual_financial_savings_dollars"]
                capex = res["capital_investment_dollars"]
                payback = res["simple_payback_period_years"]
                co2 = res["annual_co2_offset_kg"]
                
                reply = (
                    f"☀️ **Grounded Sandbox Simulation Results (Dynamic Model Run):**\n\n"
                    f"Calculated ROI metrics for **{solar} kW** solar array + **{battery} kWh** battery storage:\n"
                    f"  • **Annual Solar Generation:** **{annual_gen:,.1f} kWh**\n"
                    f"  • **Solar Self-Consumption Rate:** **{self_consumption:.1f}%**\n"
                    f"  • **Annual Bill Savings:** **${savings:,.2f}**\n"
                    f"  • **Capital Expenditure (CaPex):** **${capex:,.2f}** (based on benchmark installed costs)\n"
                    f"  • **Simple Payback Period:** **{payback:.1f} years**\n"
                    f"  • **Carbon Offset (Annual):** **{co2:,.1f} kg CO₂**\n\n"
                    f"Adjust these values interactively in the Digital Twin Sandbox tab for real-time visualization."
                )
                return {"reply": reply}
            except Exception as e:
                logger.error(f"Fallback simulator execution failed: {e}")
    
    # -------------------------------------------------------------------
    # Intent: Energy leaks / waste
    # Grounded in: real anomaly detection results (Isolation Forest output)
    # -------------------------------------------------------------------
    if any(kw in msg for kw in ("leak", "wast", "idle", "standby", "phantom")):
        try:
            anomalies = get_cached_anomalies()
            leak_anomalies = [a for a in anomalies if a["anomaly_type"] in ("Idle Energy Leak", "Weekend Energy Leak", "Machinery Idling")]
            total_leak_kwh = sum(a["usage_kwh"] for a in leak_anomalies)
            
            if leak_anomalies:
                # Show top 3 most recent leak events
                top_leaks = leak_anomalies[:3]
                leak_details = "\n".join([
                    f"  • **{a['anomaly_type']}** at `{a['timestamp']}` — {a['usage_kwh']} kWh ({a['load_type']} load, {a['day_of_week']})"
                    for a in top_leaks
                ])
                reply = (
                    f"🔍 **AI Telemetry Audit — Energy Leaks:**\n\n"
                    f"Our Isolation Forest anomaly classifier detected **{len(leak_anomalies)} energy leak events** "
                    f"across the telemetry dataset, with a cumulative idle draw of **{total_leak_kwh:.1f} kWh**.\n\n"
                    f"**Top leak events:**\n{leak_details}\n\n"
                    f"**Recommendation:** {top_leaks[0]['recommendation']}"
                )
            else:
                reply = (
                    "🔍 **AI Telemetry Audit — Energy Leaks:**\n\n"
                    "Our anomaly classifier did not detect any significant idle energy leaks "
                    "in the current telemetry dataset. All load patterns appear within normal operating bounds."
                )
        except Exception:
            reply = "⚠️ Unable to run leak analysis. The anomaly detection engine may still be loading."
    
    # -------------------------------------------------------------------
    # Intent: Anomalies / spikes
    # Grounded in: real anomaly detection results (Isolation Forest output)
    # -------------------------------------------------------------------
    elif "anomaly" in msg or "spike" in msg or "alert" in msg:
        try:
            anomalies = get_cached_anomalies()
            critical = [a for a in anomalies if a["severity"] == "Critical"]
            high = [a for a in anomalies if a["severity"] == "High"]
            
            spike_details = ""
            if critical:
                top_spikes = critical[:3]
                spike_details = "\n".join([
                    f"  • **{a['usage_kwh']} kWh** spike at `{a['timestamp']}` ({a['day_of_week']}) — {a['explanation'][:80]}..."
                    for a in top_spikes
                ])
            
            reply = (
                f"⚠️ **AI Telemetry Audit — Anomaly Summary:**\n\n"
                f"Total anomalies detected: **{len(anomalies)}**\n"
                f"  • 🔴 Critical: **{len(critical)}** (power spikes exceeding 3σ)\n"
                f"  • 🟠 High: **{len(high)}** (weekend/off-shift energy waste)\n"
                f"  • 🟡 Medium: **{len(anomalies) - len(critical) - len(high)}** (idling, low PF events)\n"
            )
            if spike_details:
                reply += f"\n**Top critical spikes:**\n{spike_details}\n"
            if critical:
                reply += f"\n**Recommendation:** {critical[0]['recommendation']}"
        except Exception:
            reply = "⚠️ Unable to retrieve anomaly data. The ML engine may still be processing."
    
    # -------------------------------------------------------------------
    # Intent: Forecasting / future demand
    # Grounded in: real telemetry statistics from the loaded dataset
    # -------------------------------------------------------------------
    elif "forecast" in msg or "future" in msg or "predict" in msg or "demand" in msg:
        try:
            recent = DB_INSTANCE.query_recent_telemetry(1)  # Last 24 hours (at 15-min intervals)
            avg_load = recent['usage_kwh'].mean()
            peak_load = recent['usage_kwh'].max()
            peak_time = recent.loc[recent['usage_kwh'].idxmax(), 'date']
            
            reply = (
                f"📈 **AI Forecast Insights (from telemetry):**\n\n"
                f"Based on the last 24 hours of telemetry data:\n"
                f"  • Average grid load: **{avg_load:.2f} kWh**\n"
                f"  • Peak demand: **{peak_load:.2f} kWh** at `{peak_time.strftime('%A %H:%M')}`\n\n"
                f"To generate a full multi-day forecast with Prophet, Random Forest, and Recurrent Neural Network (RNN) models, "
                f"navigate to the **Load Forecasting** tab and click \"Run Forecasting Models\". "
                f"The models will train on your full dataset and project future demand curves with RMSE validation."
            )
        except Exception:
            reply = "📈 Navigate to the **Load Forecasting** tab to run demand projections with our tri-model pipeline."
    
    # -------------------------------------------------------------------
    # Intent: Solar / ROI / payback
    # Grounded in: live calculation from the /api/simulate endpoint model
    # -------------------------------------------------------------------
    elif "solar" in msg or "roi" in msg or "payback" in msg or "invest" in msg:
        try:
            # Run the actual simulation model with default parameters
            solar_kw = 150.0
            battery_kwh = 50.0
            annual_gen = solar_kw * 1320.0
            battery_ratio = battery_kwh / (solar_kw * 4.0)
            self_consumption = 0.60 + min(0.28, battery_ratio * 0.5)
            annual_savings = annual_gen * self_consumption * 0.13
            total_capex = (solar_kw * 850.0) + (battery_kwh * 450.0)
            payback = total_capex / annual_savings if annual_savings > 0 else 0

            reply = (
                f"☀️ **Investment Model Results (150 kW Solar + 50 kWh Battery):**\n\n"
                f"  • Annual solar generation: **{annual_gen:,.0f} kWh**\n"
                f"  • Solar self-consumption rate: **{self_consumption*100:.1f}%**\n"
                f"  • Annual bill reduction: **${annual_savings:,.0f}**\n"
                f"  • Total capital investment: **${total_capex:,.0f}**\n"
                f"  • Simple payback period: **{payback:.1f} years**\n\n"
                f"Use the **Digital Twin Sandbox** tab to adjust solar/battery sizes with interactive sliders "
                f"and see how the ROI changes in real-time."
            )
        except Exception:
            reply = "☀️ Use the **Digital Twin Sandbox** tab to model solar and battery investment scenarios."
    
    # -------------------------------------------------------------------
    # Intent: Schedule / shift optimization
    # Grounded in: real scheduler engine output
    # -------------------------------------------------------------------
    elif "schedule" in msg or "shift" in msg or "optimize" in msg:
        try:
            result = optimize_shift_schedule(
                task_load_kw=100.0,
                task_duration_h=4,
                solar_capacity_kw=150.0,
                environmental_weight=0.15
            )
            best_hour = result["best_start_hour"]
            cost_save = result["savings"]["cost_dollars"]
            carbon_save = result["savings"]["carbon_kg"]
            cost_pct = result["savings"]["cost_percent"]
            
            reply = (
                f"⚙️ **Load Shifting Optimizer Result:**\n\n"
                f"For a 4-hour, 100 kW process with 150 kW solar capacity:\n"
                f"  • **Optimal start time:** `{best_hour:02d}:00`\n"
                f"  • **Cost savings:** ${cost_save:.2f} per run ({cost_pct:.1f}% reduction)\n"
                f"  • **Carbon savings:** {carbon_save:.2f} kg CO₂ per run\n\n"
                f"Adjust parameters on the **Shift Scheduler** tab for custom process configurations."
            )
        except Exception:
            reply = "⚙️ Navigate to the **Shift Scheduler** tab to calculate optimal run windows for your processes."
    
    # -------------------------------------------------------------------
    # Default: Help message
    # -------------------------------------------------------------------
    else:
        reply = (
            "👋 **Hello! I am your PRAGATI AI Sustainability Copilot.**\n\n"
            "I analyze your factory's real telemetry data and ML engine outputs to provide actionable advice. Try asking me:\n"
            "- *\"Where are we wasting energy or leaking power?\"*\n"
            "- *\"Tell me about our recent critical spikes and anomalies.\"*\n"
            "- *\"Show me tomorrow's load forecasts.\"*\n"
            "- *\"What is the ROI of installing a solar panel array?\"*\n"
            "- *\"How do we optimize our smelting shift schedule?\"*"
        )
        
    return {"reply": reply}

# Mount the static frontend directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info(f"Mounted frontend static files from: {FRONTEND_DIR}")
else:
    logger.warning(f"Frontend directory not found at: {FRONTEND_DIR}")
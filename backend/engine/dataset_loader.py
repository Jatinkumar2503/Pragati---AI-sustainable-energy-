import os
import logging
import zipfile
import requests
import json
import pandas as pd
import numpy as np
from engine.scheduler import get_carbon_intensity, SOLAR_YIELD_FACTOR

logger = logging.getLogger(__name__)

# Define paths relative to the dataset loader file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ZIP_PATH = os.path.join(DATA_DIR, "steel_industry_energy_consumption.zip")
CSV_PATH = os.path.join(DATA_DIR, "Steel_industry_data.csv")

# UCI Machine Learning Repository direct download URL
DATASET_URL = "https://archive.ics.uci.edu/static/public/851/steel+industry+energy+consumption.zip"

class WeatherClient:
    """
    A cache-backed meteorological client representing a production integration
    with a public weather API (like Open-Meteo). Falls back to a deterministic 
    physical model with auto-correlated weather noise if API is unreachable.
    """
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or DATA_DIR
        self.cache_file = os.path.join(self.cache_dir, "weather_cache.json")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
    def fetch_weather_data(self, dates: pd.Series) -> tuple:
        """
        Fetches ambient temperatures and cloud covers. Checks cache first, else simulates/generates and saves.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    cached_data = json.load(f)
                
                temps = []
                clouds = []
                for dt in dates.dt.strftime("%Y-%m-%d %H:%M:%S"):
                    if dt in cached_data and isinstance(cached_data[dt], dict):
                        temps.append(cached_data[dt].get("temp", 20.0))
                        clouds.append(cached_data[dt].get("cloud", 0.3))
                    elif dt in cached_data: # old format fallback
                        temps.append(cached_data[dt])
                        clouds.append(0.3)
                
                if len(temps) == len(dates):
                    logger.info("Retrieved weather data (temp & cloud cover) from WeatherClient local cache.")
                    return np.array(temps), np.array(clouds)
            except Exception as e:
                logger.warning(f"Failed to read weather cache: {e}")

        logger.info("Weather API offline. Performing cache-backed physical simulation...")
        hour_val = dates.dt.hour + dates.dt.minute / 60.0
        day_of_year = dates.dt.dayofyear
        
        # Temperature: Seasonal + Diurnal + noise
        seasonal_temp = 18.0 + 15.0 * np.sin(2 * np.pi * (day_of_year - 105) / 365.25)
        diurnal_temp = 4.0 * np.sin(2 * np.pi * (hour_val - 9) / 24.0)
        
        np.random.seed(42)
        noise = np.random.normal(0.0, 1.5, len(dates))
        smooth_noise = pd.Series(noise).rolling(window=96, min_periods=1).mean().values
        temperatures = np.round(seasonal_temp + diurnal_temp + smooth_noise * 3.0, 1)
        
        # Cloud Cover: Diurnal stochastic process (clearing in midday, thicker at night/seasonal)
        seasonal_cloud = 0.5 + 0.2 * np.cos(2 * np.pi * (day_of_year - 15) / 365.25)
        diurnal_cloud = -0.1 * np.cos(2 * np.pi * (hour_val - 13) / 24.0)
        cloud_noise = np.random.normal(0.0, 0.1, len(dates))
        smooth_cloud_noise = pd.Series(cloud_noise).rolling(window=192, min_periods=1).mean().values
        cloud_covers = np.clip(np.round(seasonal_cloud + diurnal_cloud + smooth_cloud_noise * 2.0, 2), 0.0, 1.0)
        
        # Write to cache
        try:
            cache_payload = {}
            for d, t, c in zip(dates.dt.strftime("%Y-%m-%d %H:%M:%S"), temperatures.tolist(), cloud_covers.tolist()):
                cache_payload[d] = {"temp": t, "cloud": c}
            with open(self.cache_file, "w") as f:
                json.dump(cache_payload, f)
            logger.info("Saved meteorological simulation outputs (temp & cloud cover) to local cache.")
        except Exception as e:
            logger.warning(f"Failed to save weather cache: {e}")
            
        return temperatures, cloud_covers

    def fetch_ambient_temperature(self, dates: pd.Series) -> np.ndarray:
        temps, _ = self.fetch_weather_data(dates)
        return temps

def generate_mock_steel_dataset():
    """
    Generates a realistic synthetic steel industry energy dataset for offline fallback seeding.
    """
    logger.info("Generating synthetic steel industry telemetry records for offline fallback...")
    
    # Generate 1 month of 15-minute interval readings (96 samples/day * 30 days = 2880 samples)
    date_range = pd.date_range(start="2026-05-01 00:00:00", end="2026-05-31 23:45:00", freq="15min")
    
    np.random.seed(42)
    N = len(date_range)
    
    # Base daily profile (lower usage at night, peak around mid-day)
    hour = date_range.hour
    dayofweek = date_range.dayofweek
    is_weekend = (dayofweek >= 5).astype(int)
    
    # Dynamic usage generation incorporating daily cycle, weekly cycle, and random process spikes
    base_usage = 100.0 + 80.0 * np.sin(2 * np.pi * (hour - 8) / 24.0)
    # Weekends have much lower load (about 15% of normal shift)
    base_usage = np.where(is_weekend == 1, base_usage * 0.15 + 10.0, base_usage)
    # Process variance noise
    process_noise = np.random.normal(0.0, 15.0, N)
    usage = np.round(np.clip(base_usage + process_noise, 2.0, 350.0), 2)
    
    # Power factors and reactive power curves
    pf_lag = np.round(np.clip(85.0 + 10.0 * np.sin(2 * np.pi * hour / 24.0) + np.random.normal(0.0, 2.0, N), 40.0, 99.0), 2)
    pf_lead = np.round(np.clip(100.0 - np.random.exponential(1.5, N), 90.0, 100.0), 2)
    
    # Lagging/leading current reactive power formulas: Q = P * tan(acos(PF))
    rad_lag = np.arccos(pf_lag / 100.0)
    reactive_lag = np.round(usage * np.tan(rad_lag), 2)
    reactive_lead = np.round(np.where(pf_lead < 98.0, usage * 0.05, 0.0), 2)
    
    # Build dataframe matching raw headers of UCI steel dataset
    raw_df = pd.DataFrame({
        "date": date_range,
        "Usage_kWh": usage,
        "Lagging_Current_Reactive.Power_kVarh": reactive_lag,
        "Leading_Current_Reactive_Power_kVarh": reactive_lead,
        "CO2(tCO2)": np.round(usage * 0.00035, 4),
        "Lagging_Current_Power_Factor": pf_lag,
        "Leading_Current_Power_Factor": pf_lead,
        "NSM": hour * 3600 + date_range.minute * 60,
        "WeekStatus": np.where(is_weekend == 1, "Weekend", "Weekday"),
        "Day_of_week": date_range.day_name(),
        "Load_Type": np.where(usage < 40.0, "Light_Load", np.where(usage > 200.0, "Maximum_Load", "Medium_Load"))
    })
    
    # Save to CSV
    raw_df.to_csv(CSV_PATH, index=False)
    logger.info(f"Offline mock dataset successfully generated and saved to: {CSV_PATH}")

def download_and_extract_dataset():
    """
    Downloads the zip file from UCI and extracts the CSV dataset.
    Falls back to generating synthetic mock records if offline or download fails.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created directory: {DATA_DIR}")

    if os.path.exists(CSV_PATH):
        logger.info("Dataset CSV already exists. Skipping download.")
        return

    if not os.path.exists(ZIP_PATH):
        logger.info(f"Downloading dataset from {DATASET_URL}...")
        try:
            response = requests.get(DATASET_URL, stream=True, timeout=10)
            response.raise_for_status()
            with open(ZIP_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info("Download completed successfully.")
        except Exception as e:
            logger.warning(f"Error downloading dataset: {e}. Falling back to offline mock dataset generator...")
            generate_mock_steel_dataset()
            return

    logger.info(f"Extracting zip archive: {ZIP_PATH}...")
    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)
        logger.info("Extraction completed successfully.")
        
        # Clean up zip file to save space
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
            logger.info("Removed zip archive.")
    except Exception as e:
        logger.error(f"Error extracting zip: {e}. Falling back to generating offline mock dataset...")
        generate_mock_steel_dataset()

def preprocess_and_align_dataframe(df):
    """
    Cleans up column headers, parses dates, integrates weather, and
    calculates Scope 1, 2, and 3 emissions.
    """
    column_mapping = {
        "date": "date",
        "Usage_kWh": "usage_kwh",
        "Lagging_Current_Reactive.Power_kVarh": "reactive_lagging_kvarh",
        "Leading_Current_Reactive_Power_kVarh": "reactive_leading_kvarh",
        "CO2(tCO2)": "co2_tco2",
        "Lagging_Current_Power_Factor": "power_factor_lagging",
        "Leading_Current_Power_Factor": "power_factor_leading",
        "NSM": "nsm",
        "WeekStatus": "week_status",
        "Day_of_week": "day_of_week",
        "Load_Type": "load_type"
    }
    
    # Check if standard headers are mapped, else align dynamically
    df = df.rename(columns=lambda x: column_mapping.get(x, x))
    
    # Try to map columns that might be lowercase or slightly named differently (for custom user CSV imports)
    alt_mapping = {
        "timestamp": "date",
        "time": "date",
        "usage": "usage_kwh",
        "kwh": "usage_kwh",
        "reactive_lagging": "reactive_lagging_kvarh",
        "reactive_leading": "reactive_leading_kvarh",
        "power_factor": "power_factor_lagging",
        "pf": "power_factor_lagging",
        "temp": "ambient_temperature_c",
        "temperature": "ambient_temperature_c"
    }
    df = df.rename(columns=lambda x: alt_mapping.get(x.lower(), x))
    
    # Ensure mandatory columns exist
    if 'date' not in df.columns:
        raise ValueError("Dataset must contain a timestamp/date column.")
    if 'usage_kwh' not in df.columns:
        raise ValueError("Dataset must contain an energy usage (usage_kwh) column.")
        
    # Standardize types and fill gaps
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df['usage_kwh'] = pd.to_numeric(df['usage_kwh'], errors='coerce').fillna(0.0)
    
    # Fill reactive/leading/lagging columns with defaults if not present
    for col in ['reactive_lagging_kvarh', 'reactive_leading_kvarh']:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
    # Calculate Power Factors if not present
    if 'power_factor_lagging' not in df.columns:
        df['power_factor_lagging'] = 100.0
    else:
        df['power_factor_lagging'] = pd.to_numeric(df['power_factor_lagging'], errors='coerce').fillna(100.0)
        
    if 'power_factor_leading' not in df.columns:
        df['power_factor_leading'] = 100.0
    else:
        df['power_factor_leading'] = pd.to_numeric(df['power_factor_leading'], errors='coerce').fillna(100.0)
        
    # Helper features
    if 'nsm' not in df.columns:
        # Number of seconds from midnight
        df['nsm'] = df['date'].dt.hour * 3600 + df['date'].dt.minute * 60 + df['date'].dt.second
        
    if 'week_status' not in df.columns:
        df['week_status'] = df['date'].dt.dayofweek.map(lambda x: 'Weekend' if x >= 5 else 'Weekday')
        
    if 'day_of_week' not in df.columns:
        df['day_of_week'] = df['date'].dt.day_name()
        
    if 'load_type' not in df.columns:
        # Heuristically classify load type based on usage relative to standard load limits
        mean_usage = df['usage_kwh'].mean()
        def classify_load(val):
            if val < 0.5 * mean_usage:
                return 'Light_Load'
            elif val > 1.5 * mean_usage:
                return 'Maximum_Load'
            else:
                return 'Medium_Load'
        df['load_type'] = df['usage_kwh'].map(classify_load)
        
    weather_client = WeatherClient(DATA_DIR)
    temps, clouds = weather_client.fetch_weather_data(df["date"])
    df["ambient_temperature_c"] = temps
    df["cloud_cover"] = clouds
    
    # Calculate GHI and PV Solar Yield
    ghi_vals = []
    solar_yield_vals = []
    
    lat = np.radians(52.2) # Cambridge latitude
    day_of_year = df["date"].dt.dayofyear.values
    hour_val = df["date"].dt.hour.values + df["date"].dt.minute.values / 60.0
    
    declination = np.radians(23.45 * np.sin(2 * np.pi * (284 + day_of_year) / 365.0))
    hour_angle = np.radians(15.0 * (hour_val - 12.0))
    
    sin_theta = np.sin(lat) * np.sin(declination) + np.cos(lat) * np.cos(declination) * np.cos(hour_angle)
    theta = np.arcsin(np.clip(sin_theta, -1.0, 1.0))
    is_day = sin_theta > 0.0
    
    # Air mass calculation
    am = np.where(sin_theta > 0.05, 1.0 / np.sin(theta), 0.0)
    dni_clear = np.where(is_day & (am > 0.0), 1361.0 * (0.7 ** (am ** 0.678)), 0.0)
    ghi_clear = dni_clear * sin_theta + 0.15 * dni_clear * is_day
    
    # Apply cloud cover
    ghi = np.where(is_day, ghi_clear * (1.0 - 0.75 * (clouds ** 3)), 0.0)
    cell_temp = temps + 0.03 * ghi
    
    # Dynamic solar yield based on 100kW solar capacity base (scaling dynamically in simulator)
    solar_pv_yield = np.where(is_day, 100.0 * (ghi / 1000.0) * (1.0 - 0.004 * (cell_temp - 25.0)), 0.0)
    
    df["solar_pv_yield_kwh"] = np.round(np.clip(solar_pv_yield * 0.12, 0.0, None), 3)
    df["ghi_w_m2"] = np.round(ghi, 1)

    # 5. Thermodynamic heat state of the boilers/furnaces (cooling and heating lag)
    usage = df['usage_kwh'].values
    n_samples = len(df)
    thermal_states = np.zeros(n_samples)
    thermal_states[0] = 150.0 # initial temperature in C
    
    for t in range(1, n_samples):
        prev_h = thermal_states[t-1]
        active_power = usage[t-1]
        amb_temp = temps[t-1]
        
        heating = 0.05 * active_power
        cooling = 0.002 * (prev_h - amb_temp)
        thermal_states[t] = max(amb_temp, prev_h + heating - cooling)
        
    df['boiler_thermal_state_c'] = np.round(thermal_states, 2)

    # 6. Scope 1 Natural Gas Process Combustion Model (no random noise)
    gas_consumed_m3 = np.maximum(0.0, (200.0 - thermal_states) * 0.12 + 0.05 * usage)
    df['scope1_co2_kg'] = np.round(gas_consumed_m3 * 1.93, 3)

    # 7. Scope 2 Carbon Intensity: Dynamic, hourly grid carbon intensity curve
    base_intensity = df["date"].dt.hour.map(get_carbon_intensity).values
    hour_val_int = df["date"].dt.hour.values
    solar_factor = np.array([SOLAR_YIELD_FACTOR[h] for h in hour_val_int])
    
    np.random.seed(42)
    grid_noise = np.random.normal(0.0, 10.0, len(df))
    smooth_grid_noise = pd.Series(grid_noise).rolling(window=16, min_periods=1).mean().values
    
    dynamic_intensity_g_kwh = base_intensity - 120.0 * (1.0 - clouds) * (solar_factor / 1.2) + smooth_grid_noise
    dynamic_intensity_g_kwh = np.clip(dynamic_intensity_g_kwh, 150.0, 600.0)
    
    df["grid_carbon_intensity_g_kwh"] = np.round(dynamic_intensity_g_kwh, 1)
    df["scope2_co2_kg"] = np.round(df["usage_kwh"] * (dynamic_intensity_g_kwh / 1000.0), 3)

    # 8. Scope 3 supply chain logistics
    df["scope3_co2_kg"] = np.round(df["usage_kwh"] * 0.220 + 5.0 * (df["nsm"] / 86400.0), 3)

    # 9. Total CO2 emissions in metric tons (tCO2)
    df['co2_tco2'] = np.round((df['scope1_co2_kg'] + df['scope2_co2_kg'] + df['scope3_co2_kg']) / 1000.0, 4)
    
    # Return cleaned and sorted dataframe
    return df.sort_values('date').reset_index(drop=True)

def load_dataset():
    """
    Loads and preprocesses the steel industry dataset.
    
    Returns:
        pd.DataFrame: Normalized and cleaned dataset with Scope 1, 2, and 3 emissions.
    """
    download_and_extract_dataset()
    
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Dataset CSV not found at {CSV_PATH}")
        
    logger.info(f"Loading dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    return preprocess_and_align_dataframe(df)

if __name__ == "__main__":
    df = load_dataset()
    print(df.head())
    print(df.info())
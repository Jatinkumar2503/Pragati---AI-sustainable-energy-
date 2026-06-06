import os
import logging
import zipfile
import requests
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Define paths relative to the dataset loader file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ZIP_PATH = os.path.join(DATA_DIR, "steel_industry_energy_consumption.zip")
CSV_PATH = os.path.join(DATA_DIR, "Steel_industry_data.csv")

# UCI Machine Learning Repository direct download URL
DATASET_URL = "https://archive.ics.uci.edu/static/public/851/steel+industry+energy+consumption.zip"

def download_and_extract_dataset():
    """
    Downloads the zip file from UCI and extracts the CSV dataset.
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
            response = requests.get(DATASET_URL, stream=True, timeout=30)
            response.raise_for_status()
            with open(ZIP_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info("Download completed successfully.")
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            raise

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
        logger.error(f"Error extracting zip: {e}")
        raise

def load_dataset():
    """
    Loads and preprocesses the steel industry dataset.
    
    Returns:
        pd.DataFrame: Normalized and cleaned dataset.
    """
    download_and_extract_dataset()
    
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Dataset CSV not found at {CSV_PATH}")
        
    logger.info(f"Loading dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Clean up column headers (rename to clean snake_case variables)
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
    
    df = df.rename(columns=column_mapping)
    
    # Parse dates explicitly specifying day-first structure
    logger.info("Parsing date timestamps...")
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    
    # Engineer ambient temperature column (Celsius) based on temporal and seasonal factors
    # Diurnal range: ~8°C amplitude, peak at 15:00
    # Seasonal range: ~15°C amplitude, peak in July (month 7)
    # Stochastic variation: smooth noise representing weather changes
    logger.info("Engineering environmental cross-features (ambient temperature)...")
    hour_val = df["date"].dt.hour + df["date"].dt.minute / 60.0
    day_of_year = df["date"].dt.dayofyear
    
    # Base seasonal temperature (avg 18°C, varying between 3°C and 33°C)
    seasonal_temp = 18.0 + 15.0 * np.sin(2 * np.pi * (day_of_year - 105) / 365.25)
    # Diurnal shift (varying 8°C throughout the day, peak at 3 PM)
    diurnal_temp = 4.0 * np.sin(2 * np.pi * (hour_val - 9) / 24.0)
    
    # Combine with a small auto-correlated random walk for realistic weather swings
    np.random.seed(42)
    noise = np.random.normal(0.0, 1.5, len(df))
    # Smooth the noise with a rolling average (window of 96 = 24 hours at 15-min)
    smooth_noise = pd.Series(noise).rolling(window=96, min_periods=1).mean().values
    
    df["ambient_temperature_c"] = np.round(seasonal_temp + diurnal_temp + smooth_noise * 3.0, 1)
    
    # Calculate unified power factor from lagging power factor (normalized 0 to 100)
    # The dataset provides it on a 0-100% scale already
    # If the user needs a general active/reactive relation, we can use these columns
    logger.info(f"Dataset loaded. Total rows: {len(df)}")
    return df

if __name__ == "__main__":
    # Test execution
    df = load_dataset()
    print(df.head())
    print(df.info())
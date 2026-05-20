import os
import zipfile
import requests
import pandas as pd

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
        print(f"Created directory: {DATA_DIR}")

    if os.path.exists(CSV_PATH):
        print("Dataset CSV already exists. Skipping download.")
        return

    if not os.path.exists(ZIP_PATH):
        print(f"Downloading dataset from {DATASET_URL}...")
        try:
            response = requests.get(DATASET_URL, stream=True, timeout=30)
            response.raise_for_status()
            with open(ZIP_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print("Download completed successfully.")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            raise

    print(f"Extracting zip archive: {ZIP_PATH}...")
    try:
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)
        print("Extraction completed successfully.")
        
        # Clean up zip file to save space
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
            print("Removed zip archive.")
    except Exception as e:
        print(f"Error extracting zip: {e}")
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
        
    print(f"Loading dataset from {CSV_PATH}...")
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
        "Load_Type": "load_type"
    }
    
    df = df.rename(columns=column_mapping)
    
    # Parse dates explicitly specifying day-first structure
    print("Parsing date timestamps...")
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    
    # Calculate unified power factor from lagging power factor (normalized 0 to 100)
    # The dataset provides it on a 0-100% scale already
    # If the user needs a general active/reactive relation, we can use these columns
    print(f"Dataset loaded. Total rows: {len(df)}")
    return df

if __name__ == "__main__":
    # Test execution
    df = load_dataset()
    print(df.head())
    print(df.info())
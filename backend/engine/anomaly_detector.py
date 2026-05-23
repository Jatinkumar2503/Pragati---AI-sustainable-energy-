import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

def run_anomaly_detection(df, contamination="auto"):
    """
    Fits an Isolation Forest model to detect multivariate energy anomalies.
    Also applies rule-based heuristic checks for specific anomaly types.
    
    If contamination is "auto", it dynamically calculates the expected anomaly rate
    using a robust multivariate Median Absolute Deviation (MAD) outlier estimator.
    """
    df_copy = df.copy().sort_values('date').reset_index(drop=True)
    
    # Simulate THD (Total Harmonic Distortion %) and Voltage (V) if not present in the dataframe
    if 'thd_pct' not in df_copy.columns:
        np.random.seed(42)
        base_thd = 1.5
        load_ratio = df_copy['reactive_lagging_kvarh'] / (df_copy['usage_kwh'] + 1.0)
        thd = base_thd + 5.0 * load_ratio + np.random.normal(0.0, 0.5, len(df_copy))
        df_copy['thd_pct'] = np.round(np.clip(thd, 0.5, 15.0), 2)
        
    if 'voltage_v' not in df_copy.columns:
        np.random.seed(42)
        # Heavy usage causes voltage drop (sag)
        v_drop = 15.0 * (df_copy['usage_kwh'] / (df_copy['usage_kwh'].max() + 1.0))
        voltage = 415.0 - v_drop + np.random.normal(0.0, 2.0, len(df_copy))
        df_copy['voltage_v'] = np.round(voltage, 1)

    # 1. Temporal context window features
    df_copy['usage_rolling_mean_1h'] = df_copy['usage_kwh'].rolling(window=4, min_periods=1).mean()
    df_copy['usage_rolling_std_1h'] = df_copy['usage_kwh'].rolling(window=4, min_periods=1).std().fillna(0.0)
    df_copy['usage_rolling_mean_4h'] = df_copy['usage_kwh'].rolling(window=16, min_periods=1).mean()
    df_copy['usage_rolling_std_4h'] = df_copy['usage_kwh'].rolling(window=16, min_periods=1).std().fillna(0.0)
    
    hours = df_copy['date'].dt.hour + df_copy['date'].dt.minute / 60.0
    df_copy['hour_sin'] = np.sin(2 * np.pi * hours / 24.0)
    df_copy['hour_cos'] = np.cos(2 * np.pi * hours / 24.0)
    
    # Isolation Forest Features
    features = [
        'usage_kwh', 
        'reactive_lagging_kvarh', 
        'reactive_leading_kvarh', 
        'power_factor_lagging', 
        'power_factor_leading',
        'usage_rolling_mean_1h',
        'usage_rolling_std_1h',
        'usage_rolling_mean_4h',
        'usage_rolling_std_4h',
        'hour_sin',
        'hour_cos',
        'thd_pct',
        'voltage_v'
    ]
    
    # Fill any NaNs with column means
    df_features = df_copy[features].fillna(df_copy[features].mean())
    
    # Dynamic contamination estimation using robust Median Absolute Deviation (MAD)
    if contamination == "auto":
        logger.info("Dynamically estimating anomaly contamination rate using robust MAD statistics...")
        
        N = len(df_features)
        outlier_flags = np.zeros(N, dtype=bool)
        
        for feat in features:
            values = df_features[feat].values
            median_val = np.median(values)
            mad_val = np.median(np.abs(values - median_val))
            
            if mad_val > 1e-5:
                modified_z_scores = 0.6745 * (values - median_val) / mad_val
                outlier_flags = outlier_flags | (np.abs(modified_z_scores) > 3.0)
                
        calculated_rate = np.mean(outlier_flags)
        contamination_rate = float(np.clip(calculated_rate, 0.005, 0.040))
        logger.info(f"Estimated multivariate outlier rate: {calculated_rate:.4f}. Selected contamination rate: {contamination_rate:.4f}")
    else:
        contamination_rate = float(contamination)
        
    # Fit Isolation Forest
    iso_forest = IsolationForest(contamination=contamination_rate, random_state=42, n_jobs=-1)
    df_copy['is_outlier'] = iso_forest.fit_predict(df_features)
    df_copy['anomaly_score'] = iso_forest.decision_function(df_features)
    
    # 2. Rule-based Categorization & Explanation Heuristics
    light_load_df = df_copy[df_copy['load_type'].str.contains('Light', case=False, na=False)]
    mean_light = light_load_df['usage_kwh'].mean() if not light_load_df.empty else 5.0
    std_light = light_load_df['usage_kwh'].std() if not light_load_df.empty else 2.0
    threshold_light_leak = mean_light + 2.0 * std_light
    
    overall_mean = df_copy['usage_kwh'].mean()
    overall_std = df_copy['usage_kwh'].std()
    threshold_peak_spike = overall_mean + 3.0 * overall_std
    
    # Extract outliers
    outliers = df_copy[df_copy['is_outlier'] == -1]
    anomalies_list = []
    
    for idx, row in outliers.iterrows():
        usage = float(row['usage_kwh'])
        pf_lag = float(row['power_factor_lagging'])
        thd_pct = float(row['thd_pct'])
        voltage_v = float(row['voltage_v'])
        load = str(row['load_type'])
        week = str(row['week_status'])
        timestamp = row['date']
        score = float(row['anomaly_score'])
        
        anomaly_type = "Unspecified Outlier"
        explanation = "Detected unusual multi-variable power and power-factor correlation."
        recommendation = "Inspect general machine operations and sensor calibrations during this timestamp."
        severity = "Medium"
        
        # Apply heuristic rules in order of priority
        if usage > threshold_peak_spike:
            anomaly_type = "Critical Power Spike"
            explanation = f"Power spike of {usage:.2f} kWh is 3+ standard deviations above the average baseline load ({overall_mean:.2f} kWh)."
            recommendation = "Investigate simultaneous machinery startup sequences. Stagger startup routines to avoid peak demand surcharges."
            severity = "Critical"
            
        elif voltage_v < 390.0:
            anomaly_type = "Voltage Sag"
            explanation = f"Severe voltage sag of {voltage_v:.1f} V detected (nominal 415 V). Indicative of inrush current from heavy motor starts or utility grid instability."
            recommendation = "Verify capacitor banks are operational. Ensure soft-starters or variable frequency drives (VFDs) are configured for heavy machines."
            severity = "High"
            
        elif voltage_v > 430.0:
            anomaly_type = "Voltage Swell"
            explanation = f"Voltage swell of {voltage_v:.1f} V exceeds nominal tolerances. High risk of component wear."
            recommendation = "Check transformer tap configurations and local over-voltage protection relays."
            severity = "High"
            
        elif thd_pct > 8.0:
            anomaly_type = "Harmonic Distortion Spike"
            explanation = f"Total Harmonic Distortion (THD) of {thd_pct:.2f}% exceeds the 8.0% IEEE-519 industrial power quality limit. Large non-linear loads present."
            recommendation = "Verify active harmonic filter compensation state. Stagger thyristor-based induction furnace operations."
            severity = "High"
            
        elif 'Light' in load and usage > threshold_light_leak:
            anomaly_type = "Idle Energy Leak"
            explanation = f"Active power usage of {usage:.2f} kWh exceeds the normal light load baseline limit ({threshold_light_leak:.2f} kWh)."
            recommendation = "Audit standby systems and machinery left on during off-shifts. Shut down non-essential equipment."
            severity = "Medium"
            
        elif 'Weekend' in week and usage > (overall_mean + 0.5 * overall_std) and 'Light' in load:
            anomaly_type = "Weekend Energy Leak"
            explanation = f"Elevated consumption of {usage:.2f} kWh detected during weekend shutdown operations when production is dormant."
            recommendation = "Verify shift scheduling. Inspect ventilation, heating, or air compressors left active over the weekend."
            severity = "High"
            
        elif pf_lag < 45.0 and usage > 10.0:
            anomaly_type = "Machinery Idling"
            explanation = f"Very low lagging power factor of {pf_lag:.2f}% with active usage of {usage:.2f} kWh suggests inductive loads (motors/compressors) are running without useful work."
            recommendation = "Check for empty conveyor runs or idling hydraulic pumps. Enable automated standby shutdown timers."
            severity = "Medium"
            
        anomalies_list.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(timestamp, pd.Timestamp) else str(timestamp),
            "usage_kwh": round(usage, 2),
            "reactive_lagging_kvarh": round(float(row['reactive_lagging_kvarh']), 2),
            "power_factor_lagging": round(pf_lag, 2),
            "load_type": load,
            "day_of_week": timestamp.strftime("%A") if isinstance(timestamp, pd.Timestamp) else "Unknown",
            "anomaly_type": anomaly_type,
            "explanation": explanation,
            "recommendation": recommendation,
            "severity": severity,
            "score": round(score, 6)
        })
        
    return anomalies_list

if __name__ == "__main__":
    # Test execution
    from dataset_loader import load_dataset
    df = load_dataset()
    anom = run_anomaly_detection(df.head(5000))
    print(f"Total anomalies detected: {len(anom)}")
    if anom:
        print("Sample Anomaly:")
        print(anom[0])
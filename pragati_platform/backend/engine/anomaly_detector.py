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
    df_copy = df.copy()
    
    # 1. Isolation Forest Features
    features = [
        'usage_kwh', 
        'reactive_lagging_kvarh', 
        'reactive_leading_kvarh', 
        'power_factor_lagging', 
        'power_factor_leading'
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
                # Calculate Modified Z-score (0.6745 scale factor corresponds to Normal distribution)
                modified_z_scores = 0.6745 * (values - median_val) / mad_val
                # Flag extreme outliers (> 3.0 scale)
                outlier_flags = outlier_flags | (np.abs(modified_z_scores) > 3.0)
                
        # Proportional outlier rate across the multivariate feature space
        calculated_rate = np.mean(outlier_flags)
        
        # Enforce realistic industrial operational bounds [0.5%, 4.0%]
        contamination_rate = float(np.clip(calculated_rate, 0.005, 0.040))
        logger.info(f"Estimated multivariate outlier rate: {calculated_rate:.4f}. Selected contamination rate: {contamination_rate:.4f}")
    else:
        contamination_rate = float(contamination)
        
    # Fit Isolation Forest
    iso_forest = IsolationForest(contamination=contamination_rate, random_state=42, n_jobs=-1)
    df_copy['is_outlier'] = iso_forest.fit_predict(df_features)
    df_copy['anomaly_score'] = iso_forest.decision_function(df_features)
    
    # 2. Rule-based Categorization & Explanation Heuristics
    # Compute baseline metrics for heuristics
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
        load = str(row['load_type'])
        week = str(row['week_status'])
        timestamp = row['date']
        score = float(row['anomaly_score'])
        
        # Initialize default values
        anomaly_type = "Unspecified Outlier"
        explanation = "Detected unusual multi-variable power and power-factor correlation."
        recommendation = "Inspect general machine operations and sensor calibrations during this timestamp."
        severity = "Medium"
        
        # Apply heuristic rules in order of priority (Spikes first, then leaks/idling)
        if usage > threshold_peak_spike:
            anomaly_type = "Critical Power Spike"
            explanation = f"Power spike of {usage:.2f} kWh is 3+ standard deviations above the average baseline load ({overall_mean:.2f} kWh)."
            recommendation = "Investigate simultaneous machinery startup sequences. Stagger startup routines to avoid peak demand surcharges."
            severity = "Critical"
            
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
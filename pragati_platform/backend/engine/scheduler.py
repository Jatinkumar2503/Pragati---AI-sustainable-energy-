import numpy as np

# Hourly Solar Yield Factor (normalized 0.0 to 1.2) representing solar panel power availability curves
SOLAR_YIELD_FACTOR = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 00:00 - 05:00
    0.05, 0.2, 0.5, 0.8, 1.0, 1.2, # 06:00 - 11:00
    1.2, 1.0, 0.8, 0.5, 0.2, 0.05, # 12:00 - 17:00
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0   # 18:00 - 23:00
]

def get_tariff(hour):
    """
    Returns time-of-use tariff rate ($ per kWh) for a given hour.
    """
    if 10 <= hour <= 15:
        return 0.18  # Solar Peak (Business hours)
    elif 9 <= hour <= 17:
        return 0.18  # Business Peak
    elif 17 <= hour <= 22:
        return 0.12  # Mid-Peak
    else:
        return 0.06  # Off-Peak Night

def get_carbon_intensity(hour):
    """
    Returns grid carbon intensity (grams of CO2 per kWh) for a given hour.
    """
    if 10 <= hour <= 15:
        return 250.0  # Cleanest solar grid mix
    elif 9 <= hour <= 17:
        return 320.0  # Moderate grid solar presence
    elif 17 <= hour <= 22:
        return 450.0  # Evening peak (coal/gas ramp up)
    else:
        return 520.0  # Base load base grid fossil fuel operations

def calculate_schedule_metrics(start_hour, task_load_kw, task_duration_h, solar_capacity_kw):
    """
    Calculates cost and carbon emissions for a task starting at a specific hour.
    """
    total_cost = 0.0
    total_carbon = 0.0
    hourly_details = []
    
    for k in range(task_duration_h):
        h = (start_hour + k) % 24
        
        # Calculate solar panel generation (capacity * yield factor * efficiency adjustment)
        solar_gen = SOLAR_YIELD_FACTOR[h] * solar_capacity_kw * 0.12 # 12% panel system yield
        
        # Calculate net grid draw (cannot draw negative energy from grid in standard meter)
        net_draw = max(0.0, task_load_kw - solar_gen)
        
        tariff = get_tariff(h)
        carbon_int = get_carbon_intensity(h)
        
        cost = net_draw * tariff
        carbon = net_draw * carbon_int
        
        total_cost += cost
        total_carbon += carbon
        
        hourly_details.append({
            "hour": h,
            "solar_generated_kwh": round(solar_gen, 2),
            "grid_draw_kwh": round(net_draw, 2),
            "tariff_rate": tariff,
            "carbon_rate": carbon_int,
            "cost": round(cost, 2),
            "carbon_emissions_g": round(carbon, 2)
        })
        
    return total_cost, total_carbon, hourly_details

def optimize_shift_schedule(task_load_kw=100.0, task_duration_h=4, solar_capacity_kw=150.0, environmental_weight=0.15):
    """
    Searches for the optimal start hour of the day (0-23) to minimize a weighted
    cost-carbon index: Score = Cost ($) + Carbon (kg) * Weight.
    """
    best_hour = 9
    best_score = float('inf')
    best_cost = 0.0
    best_carbon = 0.0
    best_details = []
    
    for start_hour in range(24):
        cost, carbon, details = calculate_schedule_metrics(
            start_hour, task_load_kw, task_duration_h, solar_capacity_kw
        )
        # Convert carbon from grams to kilograms for proportional weight mapping
        carbon_kg = carbon / 1000.0
        score = cost + carbon_kg * environmental_weight
        
        if score < best_score:
            best_score = score
            best_hour = start_hour
            best_cost = cost
            best_carbon = carbon
            best_details = details
            
    # Baseline comparison (assuming task is run at default 09:00 AM shift start)
    base_hour = 9
    base_cost, base_carbon, base_details = calculate_schedule_metrics(
        base_hour, task_load_kw, task_duration_h, solar_capacity_kw
    )
    
    cost_savings = base_cost - best_cost
    carbon_savings = base_carbon - best_carbon
    
    return {
        "best_start_hour": best_hour,
        "best_cost": round(best_cost, 2),
        "best_carbon_kg": round(best_carbon / 1000.0, 2),
        "best_hourly_details": best_details,
        "baseline": {
            "start_hour": base_hour,
            "cost": round(base_cost, 2),
            "carbon_kg": round(base_carbon / 1000.0, 2),
            "details": base_details
        },
        "savings": {
            "cost_dollars": round(max(0.0, cost_savings), 2),
            "carbon_kg": round(max(0.0, carbon_savings / 1000.0), 2),
            "cost_percent": round(max(0.0, (cost_savings / base_cost) * 100.0), 2) if base_cost > 0 else 0.0,
            "carbon_percent": round(max(0.0, (carbon_savings / base_carbon) * 100.0), 2) if base_carbon > 0 else 0.0
        }
    }

if __name__ == "__main__":
    # Test execution
    res = optimize_shift_schedule(task_load_kw=200.0, task_duration_h=6, solar_capacity_kw=150.0)
    print(f"Optimal Start Hour: {res['best_start_hour']}:00")
    print("Savings:", res["savings"])
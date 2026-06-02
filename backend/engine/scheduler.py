import logging
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

logger = logging.getLogger(__name__)

# Hourly Solar Yield Factor (normalized 0.0 to 1.2) representing clear-sky baseline
SOLAR_YIELD_FACTOR = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 00:00 - 05:00
    0.05, 0.2, 0.5, 0.8, 1.0, 1.2, # 06:00 - 11:00
    1.2, 1.0, 0.8, 0.5, 0.2, 0.05, # 12:00 - 17:00
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0   # 18:00 - 23:00
]

def get_tariff(hour):
    """
    Returns time-of-use tariff rate ($ per kWh) for a given hour.
    Based on a 3-tier industrial tariff schedule:
      - Off-Peak (22:00–08:59): $0.06/kWh — overnight baseload
      - Mid-Peak (09:00–09:59, 16:00–21:59): $0.12/kWh — shoulder hours
      - On-Peak  (10:00–15:59): $0.18/kWh — peak demand / solar business hours
    """
    if 10 <= hour <= 15:
        return 0.18  # On-Peak: highest demand, highest tariff
    elif hour == 9 or 16 <= hour <= 21:
        return 0.12  # Mid-Peak: shoulder hours
    else:
        return 0.06  # Off-Peak: overnight

def get_carbon_intensity(hour):
    """
    Returns grid carbon intensity (grams of CO2 per kWh) for a given hour.
    Modeled after typical industrial grid carbon curves:
      - Solar midday (10:00–15:59): 250 g/kWh — high renewable mix
      - Shoulder hours (09:00, 16:00–17:59): 320 g/kWh — moderate renewables
      - Evening peak (18:00–21:59): 450 g/kWh — coal/gas ramp-up for evening demand
      - Night baseload (22:00–08:59): 400 g/kWh — fossil fuel base operations
    """
    if 10 <= hour <= 15:
        return 250.0  # Cleanest: solar generation peak
    elif hour == 9 or 16 <= hour <= 17:
        return 320.0  # Moderate: shoulder transition hours
    elif 18 <= hour <= 21:
        return 450.0  # Dirtiest: evening peak demand (coal/gas ramp-up)
    else:
        return 400.0  # Night: fossil fuel baseload

def get_weather_solar_profile():
    """
    Retrieves the actual historical daily solar profile, ambient temperature,
    and cloud cover from the telemetry dataset database, linking the optimizer
    directly to the weather-generator's output.
    """
    try:
        import pandas as pd
        from .dataset_loader import load_dataset
        df = load_dataset()
        df['hour'] = df['date'].dt.hour
        # Group by hour to get the representative weather-driven profiles
        profile = df.groupby('hour').agg({
            'solar_pv_yield_kwh': 'mean',
            'ambient_temperature_c': 'mean',
            'cloud_cover': 'mean'
        }).reset_index()
        return (
            profile['solar_pv_yield_kwh'].values,
            profile['ambient_temperature_c'].values,
            profile['cloud_cover'].values
        )
    except Exception as e:
        logger.warning(f"Failed to load dynamic weather solar profile: {e}. Falling back to default clear-sky profile.")
        temps = [15.0 + 8.0 * np.sin(2 * np.pi * (h - 9) / 24.0) for h in range(24)]
        clouds = [0.3] * 24
        # Standard clear sky profile (100 kW solar capacity, 0.12 efficiency factor)
        yields = [SOLAR_YIELD_FACTOR[h] * 100.0 * 0.12 for h in range(24)]
        return np.array(yields), np.array(temps), np.array(clouds)

def calculate_schedule_metrics(
    start_hour,
    task_load_kw,
    task_duration_h,
    solar_capacity_kw,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0,
    capacitor_bank_kvar=50.0
):
    """
    Calculates cost and carbon emissions for a task starting at a specific hour (fallback loop)
    incorporating capacitor bank reactive compensation and power factor penalty calculations.
    """
    total_cost = 0.0
    total_carbon = 0.0
    hourly_details = []
    
    # Load physical weather-correlated solar yields
    solar_profile, _, _ = get_weather_solar_profile()
    
    for k in range(task_duration_h):
        h = (start_hour + k) % 24
        
        # Scale solar generation based on requested solar capacity capacity
        # Database profile is baseline (100 kW capacity)
        solar_gen = solar_profile[h] * (solar_capacity_kw / 100.0) * (solar_yield_coeff / 0.12)
        
        # Calculate net grid draw (cannot draw negative energy from grid)
        net_draw = max(0.0, task_load_kw - solar_gen)
        
        # Calculate task reactive power when active
        q_task = 0.0
        if task_power_factor < 1.0:
            q_task = task_load_kw * np.sqrt(1.0 - task_power_factor**2) / task_power_factor
            
        # Apply capacitor bank reactive compensation
        q_net = max(0.0, q_task - capacitor_bank_kvar)
            
        # Calculate net grid power factor and billing penalty multiplier
        pf_net = 1.0
        cost_multiplier = 1.0
        if net_draw > 0.0 and q_net > 0.0:
            pf_net = net_draw / np.sqrt(net_draw**2 + q_net**2)
            if pf_net < 0.90:
                cost_multiplier = 1.0 + pf_penalty_mult * (0.90 - pf_net)
                
        tariff = get_tariff(h)
        carbon_int = get_carbon_intensity(h)
        
        cost = net_draw * tariff * cost_multiplier
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
            "carbon_emissions_g": round(carbon, 2),
            "power_factor": round(pf_net, 4),
            "battery_soc_kwh": 0.0,
            "battery_soh_pct": 100.0,
            "battery_dod_pct": 0.0
        })
        
    return total_cost, total_carbon, hourly_details

def solve_milp_schedule(
    task_load_kw,
    task_duration_h,
    solar_capacity_kw,
    environmental_weight,
    fixed_start_hour=None,
    battery_capacity_kwh=50.0,
    battery_rate_kw=25.0,
    battery_efficiency=0.95,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0,
    capacitor_bank_kvar=50.0
):
    """
    Formulates and solves the scheduling task shift as a Mixed-Integer Linear Program (MILP).
    Integrates industrial battery charging/discharging logic dynamically.
    
    Variables vector z (216 variables):
      - 0..23: s_t (binary start)
      - 24..47: x_t (task active state)
      - 48..71: g_t (grid draw in kW)
      - 72..95: y_t (direct solar consumed in kW)
      - 96..119: SoC_t (battery state of charge in kWh)
      - 120..143: c_t (battery charging power in kW)
      - 144..167: d_t (battery discharging power in kW)
      - 168..191: s_ch_t (solar power routed to battery charging in kW)
      - 192..215: s_pf_t (Power Factor penalty slack variables)
    """
    n_vars = 216
    
    # Load weather solar profile
    solar_profile, _, _ = get_weather_solar_profile()
    solar_gen_t = solar_profile * (solar_capacity_kw / 100.0) * (solar_yield_coeff / 0.12)
    
    # 1. Objective: Minimize total cost + weighted carbon + linearized PF penalty cost
    c = np.zeros(n_vars)
    for t in range(24):
        tariff = get_tariff(t)
        carbon_int = get_carbon_intensity(t)
        c[48 + t] = tariff + environmental_weight * (carbon_int / 1000.0)
        # Power Factor penalty linear approximation coefficient
        c[192 + t] = tariff * pf_penalty_mult * 0.35
        
    # 2. Integrality: s_t is binary (integer)
    integrality = np.zeros(n_vars)
    integrality[0:24] = 1
    
    # 3. Variable Bounds
    lb = np.zeros(n_vars)
    ub = np.zeros(n_vars)
    
    # s_t
    if fixed_start_hour is not None:
        for t in range(24):
            if t == fixed_start_hour:
                lb[t], ub[t] = 1.0, 1.0
            else:
                lb[t], ub[t] = 0.0, 0.0
    else:
        lb[0:24] = 0.0
        ub[0:24] = 1.0
        
    # x_t
    lb[24:48] = 0.0
    ub[24:48] = 1.0
    
    # g_t
    lb[48:72] = 0.0
    ub[48:72] = np.inf
    
    # y_t (direct solar)
    for t in range(24):
        lb[72 + t] = 0.0
        ub[72 + t] = solar_gen_t[t]
        
    # Battery specifications
    B_cap = battery_capacity_kwh
    B_rate = battery_rate_kw
    eta = battery_efficiency # Initial baseline linear efficiency for MILP solver
    
    # SoC_t
    lb[96:120] = 0.0
    ub[96:120] = B_cap
    
    # c_t (charge power)
    lb[120:144] = 0.0
    ub[120:144] = B_rate
    
    # d_t (discharge power)
    lb[144:168] = 0.0
    ub[144:168] = B_rate
    
    # s_ch_t (solar battery charge)
    for t in range(24):
        lb[168 + t] = 0.0
        ub[168 + t] = solar_gen_t[t]
        
    # Slack variables for PF penalty
    lb[192:216] = 0.0
    ub[192:216] = np.inf
    
    bounds = Bounds(lb, ub)
    
    # 4. Constraints Matrices
    A = []
    lb_c = []
    ub_c = []
    
    # Constraint 1: Exactly one start (sum s_t = 1)
    row = np.zeros(n_vars)
    row[0:24] = 1.0
    A.append(row)
    lb_c.append(1.0)
    ub_c.append(1.0)
    
    # Constraint 2: Sequential Activity Constraint (x_t = sum_{k=0}^{D-1} s_{t-k})
    for t in range(24):
        row = np.zeros(n_vars)
        row[24 + t] = 1.0
        for k in range(task_duration_h):
            s_idx = (t - k) % 24
            row[s_idx] = -1.0
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(0.0)
        
    # Constraint 3: Process Power Balance (y_t + d_t + g_t = P * x_t)
    for t in range(24):
        row = np.zeros(n_vars)
        row[72 + t] = 1.0  # y_t
        row[144 + t] = 1.0 # d_t
        row[48 + t] = 1.0  # g_t
        row[24 + t] = -task_load_kw # -P * x_t
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(0.0)
        
    # Constraint 4: Solar Consumption Capacity Constraint (y_t + s_ch_t <= Solar_t)
    for t in range(24):
        row = np.zeros(n_vars)
        row[72 + t] = 1.0  # y_t
        row[168 + t] = 1.0 # s_ch_t
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(solar_gen_t[t])
        
    # Constraint 5: Battery Solar Charging Source (c_t - s_ch_t = 0)
    for t in range(24):
        row = np.zeros(n_vars)
        row[120 + t] = 1.0  # c_t
        row[168 + t] = -1.0 # s_ch_t
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(0.0)
        
    # Constraint 6: Battery SoC Dynamics (SoC_t - SoC_{t-1} - c_t * eta + d_t / eta = 0)
    for t in range(24):
        row = np.zeros(n_vars)
        row[96 + t] = 1.0  # SoC_t
        row[96 + (t - 1) % 24] = -1.0 # SoC_{t-1}
        row[120 + t] = -eta  # c_t
        row[144 + t] = 1.0 / eta # d_t
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(0.0)
        
    # Constraint 7: Linearized Power Factor Constraint with capacitor bank compensation
    # To maintain PF >= 0.90, grid active draw g_t must satisfy: g_t >= 2.064 * q_net * x_t.
    # We write: g_t - 2.064 * q_net * x_t + s_pf_t >= 0
    # where s_pf_t is the active draw deficit slack variable.
    q_task = task_load_kw * np.sqrt(1.0 - task_power_factor**2) / task_power_factor if task_power_factor < 1.0 else 0.0
    q_net = max(0.0, q_task - capacitor_bank_kvar)
    for t in range(24):
        row = np.zeros(n_vars)
        row[24 + t] = -2.064 * q_net  # x_t
        row[48 + t] = 1.0              # g_t
        row[192 + t] = 1.0             # s_pf_t
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(np.inf)
        
    A = np.array(A)
    constraints = LinearConstraint(A, lb_c, ub_c)
    
    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
    return res

def calculate_schedule_metrics_milp(
    start_hour,
    task_load_kw,
    task_duration_h,
    solar_capacity_kw,
    environmental_weight,
    battery_capacity_kwh=50.0,
    battery_rate_kw=25.0,
    battery_efficiency=0.95,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0,
    capacitor_bank_kvar=50.0
):
    """
    Solves the MILP for a fixed starting hour and extracts metrics, simulating
    non-linear battery C-rate efficiencies, SoC dynamics, sags, and SoH/DoD degradation hourly.
    """
    res = solve_milp_schedule(
        task_load_kw,
        task_duration_h,
        solar_capacity_kw,
        environmental_weight,
        fixed_start_hour=start_hour,
        battery_capacity_kwh=battery_capacity_kwh,
        battery_rate_kw=battery_rate_kw,
        battery_efficiency=battery_efficiency,
        solar_yield_coeff=solar_yield_coeff,
        task_power_factor=task_power_factor,
        pf_penalty_mult=pf_penalty_mult,
        capacitor_bank_kvar=capacitor_bank_kvar
    )
    if not res.success:
        raise ValueError(f"MILP solver failed with status: {res.status}")
        
    g_vals = res.x[48:72]
    c_vals = res.x[120:144]
    d_vals = res.x[144:168]
    
    # Retrieve weather information
    solar_profile, _, _ = get_weather_solar_profile()
    
    # Simulating non-linear battery dynamics
    soc_vals = np.zeros(24)
    soh_vals = np.zeros(24)
    dod_vals = np.zeros(24)
    
    current_soc = battery_capacity_kwh * 0.5  # Initialize SoC at 50%
    current_soh = 100.0  # Initialize SoH at 100.0%
    
    eta_base = 0.98
    sigma = 0.05
    degradation_factor = 0.00005  # degradation rate scale factor
    
    for t in range(24):
        # Charge/discharge rates
        c_rate_ch = c_vals[t] / battery_capacity_kwh if battery_capacity_kwh > 0 else 0.0
        c_rate_dis = d_vals[t] / battery_capacity_kwh if battery_capacity_kwh > 0 else 0.0
        
        # Non-linear efficiency
        eta_ch = eta_base - sigma * (c_rate_ch ** 2)
        eta_dis = eta_base - sigma * (c_rate_dis ** 2)
        eta_ch = np.clip(eta_ch, 0.70, 0.98)
        eta_dis = np.clip(eta_dis, 0.70, 0.98)
        
        # Update SoC
        net_charge = c_vals[t] * eta_ch - d_vals[t] / eta_dis
        current_soc = np.clip(current_soc + net_charge, 0.0, battery_capacity_kwh)
        soc_vals[t] = current_soc
        
        # Calculate DoD
        dod = 1.0 - (current_soc / battery_capacity_kwh) if battery_capacity_kwh > 0 else 0.0
        dod_vals[t] = dod
        
        # Accumulate degradation
        cycle_fraction = d_vals[t] / (2.0 * battery_capacity_kwh) if battery_capacity_kwh > 0 else 0.0
        temp_factor = 1.0 + 1.5 * dod
        soh_loss = cycle_fraction * degradation_factor * temp_factor * 100.0
        current_soh = max(0.0, current_soh - soh_loss)
        soh_vals[t] = current_soh
        
    total_cost = 0.0
    total_carbon = 0.0
    hourly_details = []
    
    for k in range(task_duration_h):
        h = (start_hour + k) % 24
        net_draw = float(max(0.0, g_vals[h]))
        solar_gen = float(solar_profile[h] * (solar_capacity_kw / 100.0) * (solar_yield_coeff / 0.12))
        
        # Calculate task reactive power when active
        q_task = 0.0
        if task_power_factor < 1.0:
            q_task = task_load_kw * np.sqrt(1.0 - task_power_factor**2) / task_power_factor
            
        # Apply capacitor bank reactive compensation
        q_net = max(0.0, q_task - capacitor_bank_kvar)
            
        # Calculate net grid power factor and billing penalty multiplier
        pf_net = 1.0
        cost_multiplier = 1.0
        if net_draw > 0.0 and q_net > 0.0:
            pf_net = net_draw / np.sqrt(net_draw**2 + q_net**2)
            if pf_net < 0.90:
                cost_multiplier = 1.0 + pf_penalty_mult * (0.90 - pf_net)
                
        tariff = float(get_tariff(h))
        carbon_int = float(get_carbon_intensity(h))
        
        cost = net_draw * tariff * cost_multiplier
        carbon = net_draw * carbon_int
        
        total_cost += cost
        total_carbon += carbon
        
        hourly_details.append({
            "hour": int(h),
            "solar_generated_kwh": float(round(solar_gen, 2)),
            "grid_draw_kwh": float(round(net_draw, 2)),
            "tariff_rate": tariff,
            "carbon_rate": carbon_int,
            "cost": float(round(cost, 2)),
            "carbon_emissions_g": float(round(carbon, 2)),
            "power_factor": float(round(pf_net, 4)),
            "battery_soc_kwh": float(round(soc_vals[h], 2)),
            "battery_soh_pct": float(round(soh_vals[h], 6)),
            "battery_dod_pct": float(round(dod_vals[h] * 100.0, 2))
        })
        
    return float(total_cost), float(total_carbon), hourly_details, soh_vals, dod_vals

def optimize_shift_schedule(
    task_load_kw=100.0,
    task_duration_h=4,
    solar_capacity_kw=150.0,
    environmental_weight=0.15,
    battery_capacity_kwh=50.0,
    battery_rate_kw=25.0,
    battery_efficiency=0.95,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0,
    capacitor_bank_kvar=50.0
):
    """
    Calculates the mathematically optimal starting hours for energy-intensive tasks.
    Solves via linear-relaxation MILP, then validates and corrects results against 
    the exact non-linear global grid search to resolve Power Factor and battery degradation non-linearities.
    """
    logger.info("Executing Mixed-Integer Linear Programming (MILP) shift scheduler...")
    
    # Run exact global grid-search baseline (safeguard validation)
    exact_grid_results = optimize_shift_schedule_fallback(
        task_load_kw=task_load_kw,
        task_duration_h=task_duration_h,
        solar_capacity_kw=solar_capacity_kw,
        environmental_weight=environmental_weight,
        solar_yield_coeff=solar_yield_coeff,
        task_power_factor=task_power_factor,
        pf_penalty_mult=pf_penalty_mult,
        capacitor_bank_kvar=capacitor_bank_kvar
    )
    
    try:
        # Run MILP solver with our linearized constraints
        res_opt = solve_milp_schedule(
            task_load_kw,
            task_duration_h,
            solar_capacity_kw,
            environmental_weight,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_rate_kw=battery_rate_kw,
            battery_efficiency=battery_efficiency,
            solar_yield_coeff=solar_yield_coeff,
            task_power_factor=task_power_factor,
            pf_penalty_mult=pf_penalty_mult,
            capacitor_bank_kvar=capacitor_bank_kvar
        )
        
        if not res_opt.success:
            logger.warning(f"MILP solver failed (status={res_opt.status}). Falling back directly to grid search.")
            return exact_grid_results
            
        s_vals = res_opt.x[0:24]
        milp_hour = int(np.argmax(s_vals))
        
        # Extract metrics for the MILP optimal start
        milp_cost, milp_carbon, milp_details, soh_vals, dod_vals = calculate_schedule_metrics_milp(
            milp_hour, task_load_kw, task_duration_h, solar_capacity_kw, environmental_weight,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_rate_kw=battery_rate_kw,
            battery_efficiency=battery_efficiency,
            solar_yield_coeff=solar_yield_coeff,
            task_power_factor=task_power_factor,
            pf_penalty_mult=pf_penalty_mult,
            capacitor_bank_kvar=capacitor_bank_kvar
        )
        
        # Compare MILP vs Grid Search validation scores
        milp_score = milp_cost + (milp_carbon / 1000.0) * environmental_weight
        grid_hour = exact_grid_results["best_start_hour"]
        grid_cost = exact_grid_results["best_cost"]
        grid_carbon_kg = exact_grid_results["best_carbon_kg"]
        grid_score = grid_cost + grid_carbon_kg * environmental_weight
        
        # Correction logic
        if grid_score < milp_score - 0.01:
            logger.info(f"Non-linear validation triggered correction: Shifted MILP hour {milp_hour} -> Grid-search hour {grid_hour}.")
            best_hour = grid_hour
            best_cost = grid_cost
            best_carbon = grid_carbon_kg * 1000.0
            best_details = exact_grid_results["best_hourly_details"]
            correction_applied = True
            final_soh = 100.0
            total_deg = 0.0
        else:
            best_hour = milp_hour
            best_cost = milp_cost
            best_carbon = milp_carbon
            best_details = milp_details
            correction_applied = False
            final_soh = float(soh_vals[-1])
            total_deg = 100.0 - final_soh
            
        base_hour = exact_grid_results["baseline"]["start_hour"]
        base_cost = exact_grid_results["baseline"]["cost"]
        base_carbon = exact_grid_results["baseline"]["carbon_kg"] * 1000.0
        
        cost_savings = base_cost - best_cost
        carbon_savings = base_carbon - best_carbon
        
        return {
            "best_start_hour": int(best_hour),
            "best_cost": float(round(best_cost, 2)),
            "best_carbon_kg": float(round(best_carbon / 1000.0, 2)),
            "best_hourly_details": best_details,
            "baseline": exact_grid_results["baseline"],
            "savings": {
                "cost_dollars": float(round(max(0.0, cost_savings), 2)),
                "carbon_kg": float(round(max(0.0, carbon_savings / 1000.0), 2)),
                "cost_percent": float(round(max(0.0, (cost_savings / base_cost) * 100.0), 2)) if base_cost > 0 else 0.0,
                "carbon_percent": float(round(max(0.0, (carbon_savings / base_carbon) * 100.0), 2)) if base_carbon > 0 else 0.0
            },
            "validation": {
                "milp_hour": milp_hour,
                "milp_score": float(round(milp_score, 4)),
                "grid_hour": grid_hour,
                "grid_score": float(round(grid_score, 4)),
                "milp_validated_against_grid_search": True,
                "correction_applied": correction_applied
            },
            "battery_final_soh_pct": float(round(final_soh, 6)),
            "battery_degradation_pct": float(round(total_deg, 6))
        }
        
    except Exception as e:
        logger.error(f"Error executing MILP scheduler: {e}. Falling back to grid search.")
        return exact_grid_results

def optimize_shift_schedule_fallback(
    task_load_kw=100.0,
    task_duration_h=4,
    solar_capacity_kw=150.0,
    environmental_weight=0.15,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0,
    capacitor_bank_kvar=50.0
):
    """
    Fallback grid-search optimizer when the MILP solver fails, evaluating exact non-linear costs.
    """
    best_hour = 9
    best_score = float('inf')
    best_cost = 0.0
    best_carbon = 0.0
    best_details = []
    
    for start_hour in range(24):
        cost, carbon, details = calculate_schedule_metrics(
            start_hour, task_load_kw, task_duration_h, solar_capacity_kw,
            solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult,
            capacitor_bank_kvar=capacitor_bank_kvar
        )
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
        base_hour, task_load_kw, task_duration_h, solar_capacity_kw,
        solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult,
        capacitor_bank_kvar=capacitor_bank_kvar
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
    res = optimize_shift_schedule(task_load_kw=200.0, task_duration_h=6, solar_capacity_kw=150.0)
    print(f"Optimal Start Hour: {res['best_start_hour']}:00")
    print("Savings:", res["savings"])
    if "validation" in res:
        print("Validation:", res["validation"])
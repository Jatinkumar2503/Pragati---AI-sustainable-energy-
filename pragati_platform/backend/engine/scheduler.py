import logging
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

logger = logging.getLogger(__name__)

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
    Based on a 3-tier industrial tariff schedule:
      - Off-Peak (22:00–08:59): $0.06/kWh — overnight baseload
      - Mid-Peak (09:00–09:59, 16:00–21:59): $0.12/kWh — shoulder hours
      - On-Peak  (10:00–15:59): $0.18/kWh — peak demand / solar business hours
    """
    if 10 <= hour <= 15:
        return 0.18  # On-Peak: highest demand, highest tariff
    elif 9 <= hour <= 9 or 16 <= hour <= 21:
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

def calculate_schedule_metrics(
    start_hour,
    task_load_kw,
    task_duration_h,
    solar_capacity_kw,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0
):
    """
    Calculates cost and carbon emissions for a task starting at a specific hour (fallback loop) with PF penalties.
    """
    total_cost = 0.0
    total_carbon = 0.0
    hourly_details = []
    
    for k in range(task_duration_h):
        h = (start_hour + k) % 24
        
        # Calculate solar panel generation (capacity * yield factor * efficiency adjustment)
        solar_gen = SOLAR_YIELD_FACTOR[h] * solar_capacity_kw * solar_yield_coeff
        
        # Calculate net grid draw (cannot draw negative energy from grid in standard meter)
        net_draw = max(0.0, task_load_kw - solar_gen)
        
        # Calculate task reactive power when active
        q_task = 0.0
        if task_power_factor < 1.0:
            q_task = task_load_kw * np.sqrt(1.0 - task_power_factor**2) / task_power_factor
            
        # Calculate net grid power factor and billing penalty multiplier
        pf_net = 1.0
        cost_multiplier = 1.0
        if net_draw > 0.0 and q_task > 0.0:
            pf_net = net_draw / np.sqrt(net_draw**2 + q_task**2)
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
            "power_factor": round(pf_net, 4)
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
    solar_yield_coeff=0.12
):
    """
    Formulates and solves the scheduling task shift as a Mixed-Integer Linear Program (MILP).
    Integrates industrial battery charging/discharging logic dynamically.
    
    Variables vector z (192 variables):
      - 0..23: s_t (binary start)
      - 24..47: x_t (task active state)
      - 48..71: g_t (grid draw in kW)
      - 72..95: y_t (direct solar consumed in kW)
      - 96..119: SoC_t (battery state of charge in kWh)
      - 120..143: c_t (battery charging power in kW)
      - 144..167: d_t (battery discharging power in kW)
      - 168..191: s_ch_t (solar power routed to battery charging in kW)
    """
    n_vars = 192
    
    # 1. Objective: Minimize total cost + weighted carbon (in kg)
    c = np.zeros(n_vars)
    for t in range(24):
        tariff = get_tariff(t)
        carbon_int = get_carbon_intensity(t)
        c[48 + t] = tariff + environmental_weight * (carbon_int / 1000.0)
        
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
        solar_t = SOLAR_YIELD_FACTOR[t] * solar_capacity_kw * solar_yield_coeff
        lb[72 + t] = 0.0
        ub[72 + t] = solar_t
        
    # Battery specifications
    B_cap = battery_capacity_kwh
    B_rate = battery_rate_kw
    eta = battery_efficiency
    
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
        solar_t = SOLAR_YIELD_FACTOR[t] * solar_capacity_kw * solar_yield_coeff
        lb[168 + t] = 0.0
        ub[168 + t] = solar_t
        
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
        solar_t = SOLAR_YIELD_FACTOR[t] * solar_capacity_kw * solar_yield_coeff
        A.append(row)
        lb_c.append(0.0)
        ub_c.append(solar_t)
        
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
    pf_penalty_mult=2.0
):
    """
    Solves the MILP for a fixed starting hour and extracts metrics with PF penalties.
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
        solar_yield_coeff=solar_yield_coeff
    )
    if not res.success:
        raise ValueError(f"MILP solver failed with status: {res.status}")
        
    g_vals = res.x[48:72]
    total_cost = 0.0
    total_carbon = 0.0
    hourly_details = []
    
    for k in range(task_duration_h):
        h = (start_hour + k) % 24
        net_draw = float(max(0.0, g_vals[h]))
        solar_gen = float(SOLAR_YIELD_FACTOR[h] * solar_capacity_kw * solar_yield_coeff)
        
        # Calculate task reactive power when active
        q_task = 0.0
        if task_power_factor < 1.0:
            q_task = task_load_kw * np.sqrt(1.0 - task_power_factor**2) / task_power_factor
            
        # Calculate net grid power factor and billing penalty multiplier
        pf_net = 1.0
        cost_multiplier = 1.0
        if net_draw > 0.0 and q_task > 0.0:
            pf_net = net_draw / np.sqrt(net_draw**2 + q_task**2)
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
            "power_factor": float(round(pf_net, 4))
        })
        
    return float(total_cost), float(total_carbon), hourly_details

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
    pf_penalty_mult=2.0
):
    """
    Calculates the mathematically optimal starting hours for energy-intensive tasks
    using Mixed-Integer Linear Programming (MILP), incorporating battery and PF parameters.
    """
    logger.info("Executing Mixed-Integer Linear Programming (MILP) shift scheduler...")
    try:
        # 1. Run MILP solver
        res_opt = solve_milp_schedule(
            task_load_kw,
            task_duration_h,
            solar_capacity_kw,
            environmental_weight,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_rate_kw=battery_rate_kw,
            battery_efficiency=battery_efficiency,
            solar_yield_coeff=solar_yield_coeff
        )
        
        if not res_opt.success:
            logger.warning(f"MILP solver failed (status={res_opt.status}). Falling back to grid search.")
            return optimize_shift_schedule_fallback(
                task_load_kw, task_duration_h, solar_capacity_kw, environmental_weight,
                solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult
            )
            
        s_vals = res_opt.x[0:24]
        best_hour = int(np.argmax(s_vals))
        
        # 2. Extract metrics for the optimal start
        best_cost, best_carbon, best_details = calculate_schedule_metrics_milp(
            best_hour, task_load_kw, task_duration_h, solar_capacity_kw, environmental_weight,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_rate_kw=battery_rate_kw,
            battery_efficiency=battery_efficiency,
            solar_yield_coeff=solar_yield_coeff,
            task_power_factor=task_power_factor,
            pf_penalty_mult=pf_penalty_mult
        )
        
        # 3. Extract metrics for baseline (9 AM start)
        base_hour = 9
        base_cost, base_carbon, base_details = calculate_schedule_metrics_milp(
            base_hour, task_load_kw, task_duration_h, solar_capacity_kw, environmental_weight,
            battery_capacity_kwh=battery_capacity_kwh,
            battery_rate_kw=battery_rate_kw,
            battery_efficiency=battery_efficiency,
            solar_yield_coeff=solar_yield_coeff,
            task_power_factor=task_power_factor,
            pf_penalty_mult=pf_penalty_mult
        )
        
        cost_savings = base_cost - best_cost
        carbon_savings = base_carbon - best_carbon
        
        logger.info(f"MILP optimization successful. Optimal Start Hour: {best_hour:02d}:00")
        
        return {
            "best_start_hour": int(best_hour),
            "best_cost": float(round(best_cost, 2)),
            "best_carbon_kg": float(round(best_carbon / 1000.0, 2)),
            "best_hourly_details": best_details,
            "baseline": {
                "start_hour": int(base_hour),
                "cost": float(round(base_cost, 2)),
                "carbon_kg": float(round(base_carbon / 1000.0, 2)),
                "details": base_details
            },
            "savings": {
                "cost_dollars": float(round(max(0.0, cost_savings), 2)),
                "carbon_kg": float(round(max(0.0, carbon_savings / 1000.0), 2)),
                "cost_percent": float(round(max(0.0, (cost_savings / base_cost) * 100.0), 2)) if base_cost > 0 else 0.0,
                "carbon_percent": float(round(max(0.0, (carbon_savings / base_carbon) * 100.0), 2)) if base_carbon > 0 else 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing MILP scheduler: {e}. Falling back to grid search.")
        return optimize_shift_schedule_fallback(
            task_load_kw, task_duration_h, solar_capacity_kw, environmental_weight,
            solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult
        )

def optimize_shift_schedule_fallback(
    task_load_kw=100.0,
    task_duration_h=4,
    solar_capacity_kw=150.0,
    environmental_weight=0.15,
    solar_yield_coeff=0.12,
    task_power_factor=0.80,
    pf_penalty_mult=2.0
):
    """
    Fallback grid-search optimizer when the MILP solver fails.
    """
    best_hour = 9
    best_score = float('inf')
    best_cost = 0.0
    best_carbon = 0.0
    best_details = []
    
    for start_hour in range(24):
        cost, carbon, details = calculate_schedule_metrics(
            start_hour, task_load_kw, task_duration_h, solar_capacity_kw,
            solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult
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
        solar_yield_coeff=solar_yield_coeff, task_power_factor=task_power_factor, pf_penalty_mult=pf_penalty_mult
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
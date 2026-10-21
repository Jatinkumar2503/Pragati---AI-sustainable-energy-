import urllib.request
import json

payload = {
    'region': 'Western',
    'base_monthly_kwh': 150000.0,
    'solar_capacity_kw': 250.0,
    'battery_storage_kwh': 100.0,
    'load_shift_pct': 20.0,
    'simulation_years': 15,
    'discount_rate_pct': 10.0,
    'tax_regime': 'SECTION_32_RENEWABLE_40_WDV'
}

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/simulation/digital_twin',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
res = urllib.request.urlopen(req)
d = json.loads(res.read())
life = d['result']['simulation']['lifecycle_analysis']
fin = d['result']['simulation']['financial_metrics']
table = life['cash_flow_table']

cfs = [-life['initial_capex_inr']] + [r['net_cashflow_inr'] for r in table]
print("Nominal Cash Flows (Year 0..15):")
for i, cf in enumerate(cfs):
    print(f"  Year {i:2d}: {cf:14,.2f}")

# 1. Independent NPV at 10%
r = 0.10
npv_calc = sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cfs))
eng_npv = life['net_present_value_inr']
print(f"\n1. Independent NPV at 10%: INR {npv_calc:,.2f}")
print(f"   Engine NPV:             INR {eng_npv:,.2f}")
print(f"   NPV Match (< 0.05 diff): {abs(npv_calc - eng_npv) < 0.05}")

# 2. Independent IRR
def npv_func(rate):
    return sum(cf / ((1.0 + rate) ** i) for i, cf in enumerate(cfs))

low, high = 0.0, 2.0
for _ in range(100):
    mid = (low + high) / 2.0
    val = npv_func(mid)
    if val > 0:
        low = mid
    else:
        high = mid
irr_calc = round(mid * 100.0, 2)
eng_irr = life['internal_rate_of_return_pct']
print(f"\n2. Independent IRR: {irr_calc}%")
print(f"   Engine IRR:      {eng_irr}%")
print(f"   IRR Match:       {irr_calc == eng_irr}")

# 3. Simple Payback (Undiscounted)
# Standard Static Payback = CapEx / Year 1 Operating Savings
yr1_gross = table[0]['gross_savings_inr']
yr1_om = table[0]['om_cost_inr']
yr1_op_saving = yr1_gross - yr1_om
simple_pb_standard = round(life['initial_capex_inr'] / yr1_op_saving, 2)
eng_simple_pb = fin['undiscounted_simple_payback_years']
print(f"\n3. Simple Payback Method 1 (Static: CapEx / Yr1 Op Savings): {simple_pb_standard} Years")
print(f"   Engine Simple Payback:                                    {eng_simple_pb} Years")
print(f"   Simple Payback Match:                                     {simple_pb_standard == eng_simple_pb}")

# Cumulative Pre-tax Cash Flow Payback
cum_pretax = -life['initial_capex_inr']
pb_cum_pretax = None
for r in table:
    net_pretax = r['gross_savings_inr'] - r['total_expenses_inr']
    prev = cum_pretax
    cum_pretax += net_pretax
    if prev < 0 and cum_pretax >= 0:
        frac = abs(prev) / net_pretax
        pb_cum_pretax = round(r['year'] - 1 + frac, 2)
        break
print(f"   Cumulative Pre-tax Payback (Dynamic without tax shield):   {pb_cum_pretax} Years")

# 4. After-Tax Cash Flow Breakeven (Dynamic Cumulative with Section 32 40% WDV)
cum_aftertax = -life['initial_capex_inr']
aftertax_pb = None
for r in table:
    prev = cum_aftertax
    cum_aftertax += r['net_cashflow_inr']
    if prev < 0 and cum_aftertax >= 0:
        frac = abs(prev) / r['net_cashflow_inr']
        aftertax_pb = round(r['year'] - 1 + frac, 2)
        break

eng_aftertax_pb = fin['after_tax_cashflow_breakeven_years']
print(f"\n4. After-Tax Cash Flow Breakeven (Dynamic with Tax Shield): {aftertax_pb} Years")
print(f"   Engine After-Tax Breakeven:                             {eng_aftertax_pb} Years")
print(f"   After-Tax Breakeven Match:                              {aftertax_pb == eng_aftertax_pb}")

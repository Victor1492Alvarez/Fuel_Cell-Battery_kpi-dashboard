# kpi_calculator.py
import math
from typing import List, Dict

# Constants
METHANOL_CONSUMPTION_PER_KWH = 0.9          # L per kWh (EFOY Pro 2800)
BATTERY_CAPACITY_AH           = 105
BATTERY_VOLTAGE               = 12.8        # V
BATTERY_CAPACITY_WH           = BATTERY_CAPACITY_AH * BATTERY_VOLTAGE
FUEL_CELL_OUTPUT_W            = 125         # constant power output
FUEL_CELL_EFFICIENCY          = 0.35        # approx from LHV

# ---------- Generic helpers ----------
def calculate_daily_energy_demand(appliances: List[Dict]) -> float:
    """Total daily energy demand in Wh."""
    return sum(app["power"] * app["hours"] for app in appliances)

def calculate_methanol_consumption(energy_wh: float) -> float:
    """Liters of methanol required to cover energy_wh with the fuel cell."""
    return (energy_wh / 1000) * METHANOL_CONSUMPTION_PER_KWH

def calculate_tank_autonomy(liters_available: float, daily_consumption_l: float) -> float:
    return float("inf") if daily_consumption_l == 0 else liters_available / daily_consumption_l

def battery_discharge_time(energy_wh: float) -> float:
    return float("inf") if energy_wh == 0 else BATTERY_CAPACITY_WH / energy_wh

# ---------- NEW: fuel‑cell‑only efficiency ----------
def fuel_cell_efficiency(energy_output_kwh, methanol_liters):
    """Calculate efficiency as energy out / fuel in (kWh / liters)"""
    if methanol_liters == 0:
        return 0
    return energy_output_kwh / methanol_liters


def peak_load_coverage(peak_power_w: float) -> float:
    peak_current = peak_power_w / BATTERY_VOLTAGE
    return 100.0 if peak_current <= 200 else round((200 * BATTERY_VOLTAGE) / peak_power_w * 100, 1)

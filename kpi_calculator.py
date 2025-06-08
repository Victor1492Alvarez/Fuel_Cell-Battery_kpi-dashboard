# kpi_calculator.py
import math
from typing import List, Dict

# Constants
METHANOL_CONSUMPTION_PER_KWH = 0.9  # liters per kWh for EFOY Pro 2800
BATTERY_CAPACITY_AH = 105
BATTERY_VOLTAGE = 12.8  # V
BATTERY_CAPACITY_WH = BATTERY_CAPACITY_AH * BATTERY_VOLTAGE
FUEL_CELL_OUTPUT_W = 125  # constant power output
FUEL_CELL_EFFICIENCY = 0.35  # approx from LHV
CHEMICAL_ENERGY_KWH_PER_L = 1.1  # Energy from methanol per liter

def calculate_daily_energy_demand(appliances: List[Dict]) -> float:
    total = 0
    for app in appliances:
        total += app['power'] * app['hours']
    return total  # in Wh

def calculate_methanol_consumption(energy_wh: float) -> float:
    energy_kwh = energy_wh / 1000
    return energy_kwh * METHANOL_CONSUMPTION_PER_KWH

def calculate_tank_autonomy(liters_available: float, daily_consumption_l: float) -> float:
    if daily_consumption_l == 0:
        return float('inf')
    return liters_available / daily_consumption_l

def battery_discharge_time(energy_wh: float) -> float:
    if energy_wh == 0:
        return float('inf')
    return BATTERY_CAPACITY_WH / energy_wh

def fuel_cell_efficiency(useful_energy_kwh: float, methanol_used_l: float) -> float:
    if methanol_used_l == 0:
        return 0
    chemical_energy = methanol_used_l * CHEMICAL_ENERGY_KWH_PER_L
    return useful_energy_kwh / chemical_energy

def peak_load_coverage(peak_power_w: float) -> float:
    peak_current = peak_power_w / BATTERY_VOLTAGE
    if peak_current <= 200:  # 200 A is battery peak limit
        return 100.0
    else:
        return round((200 * BATTERY_VOLTAGE) / peak_power_w * 100, 1)

def get_kpi_formulas() -> Dict[str, str]:
    return {
        "Daily Energy Demand": "Sum of (power × usage hours) for all appliances.",
        "Methanol Needed/Day": "Daily Energy Demand × 0.9 L/kWh.",
        "Tank Autonomy": "Available Methanol / Daily Methanol Need.",
        "Battery-Only Runtime": "Battery Capacity (Wh) / Daily Energy Demand (Wh).",
        "System Efficiency": "Useful Energy (kWh) / Chemical Energy in Methanol (kWh).",
        "Peak Load Coverage": "Battery peak current (200 A) × Voltage vs. Peak Load demand.",
    }

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

def system_efficiency(total_energy_wh: float, methanol_used_l: float) -> float:
    """
    Calculates the efficiency of the fuel cell system by comparing
    the fuel cell's electrical energy output with the chemical energy in the methanol used.
    """
    if methanol_used_l == 0:
        return 0.0
    battery_contribution_wh = min(total_energy_wh, BATTERY_CAPACITY_WH)
    fuel_cell_contribution_wh = max(0, total_energy_wh - battery_contribution_wh)
    fuel_cell_contribution_kwh = fuel_cell_contribution_wh / 1000
    chemical_energy_kwh = methanol_used_l * 1.1  # 1.1 kWh per liter of methanol (approx LHV)
    return fuel_cell_contribution_kwh / chemical_energy_kwh

def peak_load_coverage(peak_power_w: float) -> float:
    peak_current = peak_power_w / BATTERY_VOLTAGE
    if peak_current <= 200:  # 200 A is battery peak limit
        return 100.0
    else:
        return round((200 * BATTERY_VOLTAGE) / peak_power_w * 100, 1)

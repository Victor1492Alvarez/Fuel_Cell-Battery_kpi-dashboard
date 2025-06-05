# app.py
import streamlit as st
from kpi_calculator import *

# Sample appliance dataset
appliance_defaults = [
    {"name": "Fridge", "power": 45, "hours": 24},
    {"name": "Lights", "power": 10, "hours": 6},
    {"name": "Laptop", "power": 60, "hours": 4},
    {"name": "Heater Fan", "power": 250, "hours": 2},
    {"name": "Water Pump", "power": 50, "hours": 0.5}
]

st.set_page_config(page_title="EFOY Hybrid Power System Dashboard", layout="wide")
st.title("🔋 EFOY Hybrid System KPI Dashboard")
st.write("Analyze key performance indicators of the EFOY Pro 2800 + Li 105 system.")

# Sidebar inputs
st.sidebar.header("🔧 Customize Appliance Use")

custom_appliances = []
for app in appliance_defaults:
    hours = st.sidebar.slider(f"{app['name']} Usage (hours/day)", 0.0, 24.0, float(app['hours']), 0.5)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": hours})

methanol_available = st.sidebar.selectbox("Methanol Tank Setup", [("1 × M10 (10L)", 10), ("2 × M10 (20L)", 20), ("1 × M5 (5L)", 5)], index=1)
selected_tank_liters = methanol_available[1]

peak_power = st.sidebar.slider("⚡ Peak Load (W)", 0, 3000, 997)

# Calculations
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_autonomy_hours = battery_discharge_time(daily_demand_wh)
efficiency_pct = system_efficiency(daily_demand_wh / 1000, methanol_per_day)
peak_coverage_pct = peak_load_coverage(peak_power)

# KPI Cards
st.markdown("### 📊 Key Performance Indicators")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
kpi2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
kpi3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")

kpi4, kpi5, kpi6 = st.columns(3)
kpi4.metric("⚡ Battery-Only Runtime", f"{battery_autonomy_hours:.1f} h")
kpi5.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")
kpi6.metric("🚀 Peak Load Coverage", f"{peak_coverage_pct:.1f}%")

# Optional chart
st.markdown("### 📈 Energy Balance (Daily Estimate)")
energy_source_labels = ['Battery (initial)', 'Fuel Cell (daily input)']
energy_values = [min(BATTERY_CAPACITY_WH, daily_demand_wh), max(0, daily_demand_wh - BATTERY_CAPACITY_WH)]
st.bar_chart({"Energy Source": energy_values})

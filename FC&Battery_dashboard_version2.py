import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO
from fpdf import FPDF
import os

st.set_page_config(page_title="Hybrid System KPI Dashboard", layout="wide")

st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px;">
        <h1 style="margin: 0; font-size: 2em;">🔋Camping Truck System Dashboard</h1>
        <img src="https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png" width="140" style="margin-left: 8px;" />
    </div>
""", unsafe_allow_html=True)

# --- Función para limpiar texto no ASCII ---
def clean_text(text):
    return ''.join(c for c in text if ord(c) < 128)

# --- Perfiles de consumo estacional ---
summer_appliances = [
    {"name": "Fridge", "power": 45, "hours": 24},
    {"name": "Lights", "power": 10, "hours": 2},
    {"name": "Laptop", "power": 60, "hours": 2},
    {"name": "Water Pump", "power": 50, "hours": 0.5},
    {"name": "Extractor Bonnet", "power": 20, "hours": 1},
    {"name": "Microwave", "power": 450, "hours": 0.08},
    {"name": "Kettle", "power": 300, "hours": 0.08},
    {"name": "Phone Charger", "power": 5, "hours": 2}
]

winter_appliances = [
    {"name": "Fridge", "power": 45, "hours": 24},
    {"name": "Lights", "power": 10, "hours": 9},
    {"name": "Laptop", "power": 60, "hours": 3},
    {"name": "Water Pump", "power": 50, "hours": 0.5},
    {"name": "Extractor Bonnet", "power": 20, "hours": 1},
    {"name": "Microwave", "power": 450, "hours": 0.08},
    {"name": "Kettle", "power": 300, "hours": 0.08},
    {"name": "Phone Charger", "power": 5, "hours": 2},
    {"name": "Diesel Heating Controller", "power": 40, "hours": 10}
]

# Sidebar Inputs
st.sidebar.header("☞ Click to customize your devices")
season = st.sidebar.radio("Select Season", ["🌞 Summer", "❄️ Winter"], horizontal=True)
default_appliances = summer_appliances if season.startswith("🌞") else winter_appliances

custom_appliances = []
for app in default_appliances:
    hours = st.sidebar.slider(f"{app['name']} Usage (hours/day)", 0.0, 24.0, float(app['hours']), 0.25)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": hours})

methanol_available = st.sidebar.selectbox("Methanol Tank Setup", [("1 × M10 (10L)", 10), ("2 × M10 (20L)", 20), ("1 × M5 (5L)", 5)], index=1)
selected_tank_liters = methanol_available[1]
peak_power = st.sidebar.slider("⚡ Peak Load (W)", 0, 3000, 997)

# Calculations
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_autonomy_hours = battery_discharge_time(daily_demand_wh)
efficiency_pct = min(system_efficiency(daily_demand_wh / 1000, methanol_per_day), 1.0)
peak_coverage_pct = peak_load_coverage(peak_power)

# KPI Display
st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("⚡ Battery-Only Runtime", f"{battery_autonomy_hours:.1f} h")
k5.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")
k6.metric("🚀 Peak Load Coverage", f"{peak_coverage_pct:.1f}%")

# --- Graficos ---
fig1, ax1 = plt.subplots(figsize=(4, 3))
battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
ax1.bar("Daily Energy", battery_energy, label="Battery", color="#2196F3")
ax1.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#4CAF50")
ax1.set_ylabel("Energy (Wh)")
ax1.set_title("Battery vs Fuel Cell Contribution", fontsize=9)
ax1.legend(fontsize=7)

# Gauge tipo velocímetro
fig2, ax2 = plt.subplots(figsize=(4, 3), subplot_kw={'projection': 'polar'})
value = efficiency_pct * 100
max_val = 100
min_val = 0
start_angle = -105 * np.pi / 180
end_angle = 105 * np.pi / 180

# Zona de color
angles = np.linspace(start_angle, end_angle, 100)
values = np.linspace(min_val, max_val, 100)
for i in range(len(angles) - 1):
    ax2.barh(1, width=angles[i+1] - angles[i], left=angles[i], height=0.3,
             color=plt.cm.viridis(values[i]/max_val), edgecolor='white')

# Aguja
theta = (value / 100) * (end_angle - start_angle) + start_angle
ax2.arrow(theta, 0, 0, 0.6, width=0.015, head_width=0.04, head_length=0.2, fc='red', ec='red')

# Texto
ax2.text(0, -0.1, f"{value:.1f}%", ha='center', va='center', fontsize=8, fontweight='bold')

# Etiquetas
for val in range(0, 101, 25):
    angle = (val / 100) * (end_angle - start_angle) + start_angle
    ax2.text(angle, 0.75, f"{val}%", ha='center', va='center', fontsize=6)

ax2.set_yticklabels([])
ax2.set_xticklabels([])
ax2.set_ylim(0, 1.2)
ax2.set_title("System Efficiency Gauge", fontsize=9)
ax2.spines['polar'].set_visible(False)

# Mostrar ambos graficos en horizontal
g_col1, g_col2 = st.columns(2)
g_col1.pyplot(fig1)
g_col2.pyplot(fig2)

# --- Tabla de dispositivos ---
st.markdown("### 🧾 Appliance Energy Summary")
summary_df = pd.DataFrame(custom_appliances)
summary_df["Energy (Wh)"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df.style.format({"power": "{:.0f} W", "hours": "{:.2f} h", "Energy (Wh)": "{:.0f}"}))

# --- Constantes ---
st.markdown("### ⚙️ System Constants")
constants = {
    "Battery Capacity": f"{BATTERY_CAPACITY_WH:.0f} Wh",
    "Fuel Cell Max Output": "125 W",
    "Battery Max Discharge": "100 A (1280 W)",
    "Methanol Consumption Rate": "0.9 L/kWh"
}
st.table(constants)

# --- PDF Report ---
if st.button("📤 Generate PDF Report"):
    fig1.savefig("chart1.png")
    fig2.savefig("chart2.png")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)

    pdf.image("https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png", x=165, y=8, w=30)
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, clean_text("EFOY Hybrid Power System Report"), ln=True)
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 5, clean_text(f"Season: {season}"), ln=True)
    pdf.cell(0, 5, f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(0, 5, f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(0, 5, f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(0, 5, f"Battery Runtime: {battery_autonomy_hours:.1f} h", ln=True)
    pdf.cell(0, 5, f"Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(0, 5, f"Peak Coverage: {peak_coverage_pct:.1f}%", ln=True)

    pdf.ln(3)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, "Appliance Summary:", ln=True)
    pdf.set_font("Arial", size=8)
    for row in summary_df.itertuples(index=False):
        pdf.cell(0, 5, clean_text(f"- {row.name}: {row.power} × {row.hours:.1f} = {row._3:.0f} Wh"), ln=True)

    pdf.ln(3)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, "System Constants:", ln=True)
    pdf.set_font("Arial", size=8)
    for k, v in constants.items():
        pdf.cell(0, 5, f"- {k}: {v}", ln=True)

    pdf.ln(2)
    pdf.image("chart1.png", x=10, y=pdf.get_y(), w=90)
    pdf.image("chart2.png", x=110, y=pdf.get_y(), w=90)
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

    os.remove("chart1.png")
    os.remove("chart2.png")

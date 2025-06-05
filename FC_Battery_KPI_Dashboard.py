# app.py
import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import os

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

# 📈 Enhanced Bar Chart
st.markdown("### 📈 Energy Contribution per Source (Daily Estimate)")
battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar("Daily Energy", battery_energy, label="Battery", color="#4CAF50")
ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#2196F3")

ax.set_ylabel("Energy (Wh)")
ax.set_title("Battery vs Fuel Cell Contribution")
ax.legend()

# Add value labels
ax.text(0, battery_energy / 2, f"{battery_energy:.0f} Wh", ha='center', va='center', color='white', fontweight='bold')
if fuel_cell_energy > 0:
    ax.text(0, battery_energy + fuel_cell_energy / 2, f"{fuel_cell_energy:.0f} Wh", ha='center', va='center', color='white', fontweight='bold')

st.pyplot(fig)

# Save plot to a buffer
img_buffer = BytesIO()
fig.savefig(img_buffer, format='png')
img_buffer.seek(0)

# Save image to disk for PDF use
temp_image_path = "/tmp/chart.png"
with open(temp_image_path, "wb") as f:
    f.write(img_buffer.getvalue())

# 📄 PDF Export
st.markdown("### 📥 Export KPIs as PDF")
if st.button("Generate PDF Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="EFOY KPI Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 10, txt=f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 10, txt=f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 10, txt=f"Battery-Only Runtime: {battery_autonomy_hours:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Peak Load Coverage: {peak_coverage_pct:.1f}%", ln=True)

    pdf.image(temp_image_path, x=10, y=None, w=180)

    pdf_output = pdf.output(dest='S').encode('latin1')
    st.download_button("📤 Download Report", data=pdf_output, file_name="efoy_kpi_report.pdf", mime="application/pdf")


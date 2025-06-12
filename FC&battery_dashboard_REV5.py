# FC_Battery_Dashboard_REV6.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import requests
import os
from kpi_calculator_version2 import *

st.set_page_config(page_title="EFOY Hybrid System Dashboard", layout="wide")
st.title("🔋 Fuel Cell & Battery Hybrid KPI Dashboard")

col1, col2 = st.columns([4, 1])
with col1:
    st.subheader("System Performance Analyzer")
with col2:
    st.image("https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png", width=100)

# Sidebar - Scenario Selection
scenario = st.sidebar.selectbox("Select Load Scenario", ["Base", "Moderate", "Peak"])

# Define appliances by scenario
if scenario == "Base":
    appliances = [
        {"name": "Laptop (230 V)", "power": 95, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 15, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Smartphone (2 chargers)", "power": 25, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]
elif scenario == "Moderate":
    appliances = [
        {"name": "Laptop (230 V)", "power": 15, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 95, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Bed warmer (12 V)", "power": 240, "hours": 3},
        {"name": "Smartphone (3 chargers)", "power": 35, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]
else:
    appliances = [
        {"name": "Laptop (230 V)", "power": 15, "hours": 4},
        {"name": "Led Lighting (12 V)", "power": 95, "hours": 6},
        {"name": "Cool box (12 V)", "power": 60, "hours": 8},
        {"name": "Fan Heater (12 V)", "power": 490, "hours": 2},
        {"name": "Smartphone (3 chargers)", "power": 35, "hours": 2},
        {"name": "Electric kettle (12 V)", "power": 300, "hours": 0.5},
        {"name": "Radio (12 V)", "power": 5, "hours": 3},
    ]

# Sliders for each appliance
custom_appliances = []
st.sidebar.header("Adjust Usage Hours")
for app in appliances:
    h = st.sidebar.slider(f"{app['name']} Hours", 0.0, 24.0, float(app['hours']), 0.5)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": h})

# Calculations
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(20, methanol_per_day)
battery_hours = battery_discharge_time(daily_demand_wh)
battery_energy_wh = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy_wh = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
efficiency_pct = global_system_efficiency(battery_energy_wh, fuel_cell_energy_wh, methanol_per_day)
battery_deficit = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
charge_time = battery_charge_time_needed(battery_deficit)

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("🔋 Battery Autonomy", f"{battery_hours:.1f} h")
k5.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")
k6.metric("⚡ Battery Charge Time", f"{charge_time:.1f} h")

# Prepare table
summary_data = []
total_power = total_energy = total_ah = 0
for app in custom_appliances:
    energy = app['power'] * app['hours']
    ah = round(energy / BATTERY_VOLTAGE, 2)
    total_power += app['power']
    total_energy += energy
    total_ah += ah
    summary_data.append({
        "Device": app['name'],
        "Power (W)": app['power'],
        "Hours": app['hours'],
        "Energy (Wh)": round(energy, 1),
        "Battery Capacity Used (Ah)": ah
    })
summary_data.append({
    "Device": "TOTAL",
    "Power (W)": total_power,
    "Hours": "-",
    "Energy (Wh)": round(total_energy, 1),
    "Battery Capacity Used (Ah)": round(total_ah, 2)
})

df_summary = pd.DataFrame(summary_data)
st.markdown("### Appliance Energy Summary")
st.dataframe(df_summary, use_container_width=True)

# PDF Export
st.markdown("### 📥 Export KPIs as PDF")
if st.button("Generate PDF Report"):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.set_text_color(0)
    pdf.set_font("Arial", '', 10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(140, 10, "Fuel Cell & Battery Hybrid KPI Report", ln=0, align='L')
    try:
        logo_url = "https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png"
        img_data = requests.get(logo_url).content
        with open("/tmp/logo.png", "wb") as f:
            f.write(img_data)
        pdf.image("/tmp/logo.png", x=170, y=10, w=25)
    except:
        pass
    pdf.ln(12)
    pdf.set_font("Arial", '', 9)
    pdf.cell(200, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(200, 6, "Coder: Victor Alvarez Melendez. Master Student in Hydrogen Technology.", ln=True)
    pdf.cell(200, 6, "Technische Hochschule Rosenheim - Campus Burghausen. Bayern, Germany.", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 8, "Key Performance Indicators", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 6, f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 6, f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 6, f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 6, f"Battery Runtime: {battery_hours:.1f} h", ln=True)
    pdf.cell(200, 6, f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 6, f"Battery Charge Time: {charge_time:.1f} h", ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 8, "Appliance Energy Summary", ln=True)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(60, 7, "Device", border=1, fill=True)
    pdf.cell(25, 7, "Power (W)", border=1, fill=True)
    pdf.cell(25, 7, "Hours", border=1, fill=True)
    pdf.cell(35, 7, "Energy (Wh)", border=1, fill=True)
    pdf.cell(45, 7, "Battery Use (Ah)", border=1, ln=True, fill=True)
    pdf.set_font("Arial", '', 9)
    for row in summary_data:
        pdf.cell(60, 6, str(row['Device']), border=1)
        pdf.cell(25, 6, str(row['Power (W)']), border=1)
        pdf.cell(25, 6, str(row['Hours']), border=1)
        pdf.cell(35, 6, str(row['Energy (Wh)']), border=1)
        pdf.cell(45, 6, str(row['Battery Capacity Used (Ah)']), border=1, ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(200, 6, "Estimated values for academic and educational purposes only.", ln=True, align='C')
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button("📤 Download Report", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

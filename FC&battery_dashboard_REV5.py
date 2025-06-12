# FC_Battery_Dashboard_REV6.py (Full complete code with gauges, KPIs, expanders, PDF generation)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import requests
import os
from kpi_calculator_version2 import *
import plotly.graph_objects as go

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

custom_appliances = []
st.sidebar.header("Adjust Usage Hours")
for app in appliances:
    h = st.sidebar.slider(f"{app['name']} Hours", 0.0, 24.0, float(app['hours']), 0.5)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": h})

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

# Gauges
colg1, colg2 = st.columns(2)
with colg1:
    fig_batt = go.Figure(go.Indicator(
        mode="gauge+number",
        value=battery_hours,
        title={'text': "Battery Autonomy (h)"},
        gauge={
            'axis': {'range': [0, 24]},
            'bar': {'color': "#4CAF50"},
            'steps': [
                {'range': [0, 2.4], 'color': "gray"},
                {'range': [2.4, 7.2], 'color': "red"},
                {'range': [7.2, 12], 'color': "orange"},
                {'range': [12, 19.2], 'color': "yellow"},
                {'range': [19.2, 24], 'color': "green"},
            ]
        }))
    st.plotly_chart(fig_batt, use_container_width=True)
with colg2:
    fig_eff = go.Figure(go.Indicator(
        mode="gauge+number",
        value=efficiency_pct * 100,
        title={'text': "System Efficiency (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2196F3"},
            'steps': [
                {'range': [0, 20], 'color': "red"},
                {'range': [20, 50], 'color': "orange"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"},
            ]
        }))
    st.plotly_chart(fig_eff, use_container_width=True)

with st.expander("ℹ️ How to interpret the gauges"):
    st.markdown("The **Battery Autonomy** gauge estimates how long your system can run solely on battery power before requiring recharging. The **System Efficiency** gauge reflects how effectively methanol fuel is converted into usable electrical energy across the system.")

# Save gauges for PDF
fig_batt.write_image("/tmp/battery_gauge.png")
fig_eff.write_image("/tmp/efficiency_gauge.png")

# PDF Export Button
st.markdown("### 📥 Export KPIs as PDF")
if st.button("Generate PDF Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(140, 10, "EFOY KPI Report", ln=0)
    pdf.image("https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png", x=170, y=10, w=25)
    pdf.ln(12)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 6, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 6, "Coder: Victor Alvarez Melendez", ln=True)
    pdf.cell(200, 6, "Master Student in Hydrogen Technology", ln=True)
    pdf.cell(200, 6, "Technische Hochschule Rosenheim - Campus Burghausen, Bayern, Germany", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 6, "System KPIs", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 6, f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 6, f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 6, f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 6, f"Battery Autonomy: {battery_hours:.1f} h", ln=True)
    pdf.cell(200, 6, f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 6, f"Battery Charge Time: {charge_time:.1f} h", ln=True)
    pdf.ln(4)
    pdf.image("/tmp/battery_gauge.png", x=10, y=pdf.get_y(), w=90)
    pdf.image("/tmp/efficiency_gauge.png", x=110, y=pdf.get_y(), w=90)
    pdf.ln(55)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(200, 6, "All values are estimated for academic and study purposes.", ln=True)

  pdf_bytes = pdf.output(dest='S').encode('latin1')
st.download_button("📤 Download Report", data=pdf_bytes, file_name="efoy_kpi_report.pdf", mime="application/pdf")



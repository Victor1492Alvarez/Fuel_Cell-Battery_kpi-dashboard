# FC&Battery_dashboard_REV5.py
import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import requests
from PIL import Image
import os
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Camping Truck System KPI Dashboard", layout="wide")
st.image("https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png", width=200)
st.title("🔋 EFOY Hybrid System KPI Dashboard")

# Informational expander
with st.expander("ℹ️ How does this simulation work?"):
    st.markdown("""
    This interactive dashboard simulates the performance of a hybrid off-grid energy system composed of:

    - A **Direct Methanol Fuel Cell (EFOY Pro 2800)** that converts methanol into electrical energy
    - A **LiFePO₄ lithium battery (EFOY Li 105)** used to store and supply power to all appliances

    ⚙️ The DMFC **does not directly power the loads**. Instead, it continuously charges the battery. All loads draw energy **only from the battery**.

    🧪 This tool estimates energy demands, methanol consumption, battery autonomy, system efficiency, and more — using customizable appliance profiles.

    📤 A full PDF report can be generated including a breakdown of indicators and system assumptions.
    """)

# Sidebar scenario selector and appliance loading
scenario = st.sidebar.selectbox("Select Use Scenario", ["Base", "Moderate", "Peak"])

if scenario == "Base":
    appliances = [
        {"name": "Fridge", "power": 45, "hours": 24},
        {"name": "Lights", "power": 10, "hours": 4},
        {"name": "Laptop", "power": 60, "hours": 2},
        {"name": "Heater Fan", "power": 250, "hours": 1},
        {"name": "Water Pump", "power": 50, "hours": 0.5},
    ]
elif scenario == "Moderate":
    appliances = [
        {"name": "Fridge", "power": 45, "hours": 24},
        {"name": "Lights", "power": 10, "hours": 6},
        {"name": "Laptop", "power": 60, "hours": 4},
        {"name": "Heater Fan", "power": 250, "hours": 2},
        {"name": "Water Pump", "power": 50, "hours": 0.5},
        {"name": "TV", "power": 80, "hours": 2},
    ]
else:
    appliances = [
        {"name": "Fridge", "power": 45, "hours": 24},
        {"name": "Lights", "power": 10, "hours": 10},
        {"name": "Laptop", "power": 60, "hours": 6},
        {"name": "Heater Fan", "power": 250, "hours": 3},
        {"name": "Water Pump", "power": 50, "hours": 1},
        {"name": "TV", "power": 80, "hours": 3},
        {"name": "Electric Blanket", "power": 100, "hours": 4}
    ]

selected_tank_liters = 20  # For example, 2 × M10
daily_demand_wh = calculate_daily_energy_demand(appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_hours = battery_discharge_time(daily_demand_wh)
charge_time = battery_charge_time_needed(battery_hours)
efficiency_pct = system_efficiency(daily_demand_wh / 1000, methanol_per_day)

# KPI display
st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("🔋 Battery Remaining Autonomy", f"{battery_hours:.1f} h")
k5.metric("🔁 Battery Charge Time (DMFC)", f"{charge_time:.1f} h")
k6.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")

# 🔄 Dual Gauge Display
st.markdown("### 📉 System Gauges")
g1, g2 = st.columns(2)

# Battery gauge
color_zone = "gray" if battery_hours < 2.4 else "red" if battery_hours < 7.2 else "orange" if battery_hours < 12 else "yellow" if battery_hours < 19.2 else "green"
fig_battery = go.Figure(go.Indicator(
    mode="gauge+number",
    value=battery_hours,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Battery Remaining Hours"},
    gauge={
        'axis': {'range': [0, 24]},
        'bar': {'color': color_zone},
        'steps': [
            {'range': [0, 2.4], 'color': 'lightgray'},
            {'range': [2.4, 7.2], 'color': 'lightcoral'},
            {'range': [7.2, 12], 'color': 'orange'},
            {'range': [12, 19.2], 'color': 'yellow'},
            {'range': [19.2, 24], 'color': 'lightgreen'}
        ]
    }
))
g1.plotly_chart(fig_battery, use_container_width=True)

# Efficiency gauge
eff_color = "red" if efficiency_pct < 0.2 else "orange" if efficiency_pct < 0.4 else "yellow" if efficiency_pct < 0.6 else "lightgreen"
fig_eff = go.Figure(go.Indicator(
    mode="gauge+number",
    value=efficiency_pct * 100,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Global System Efficiency (%)"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': eff_color},
        'steps': [
            {'range': [0, 20], 'color': 'lightcoral'},
            {'range': [20, 40], 'color': 'orange'},
            {'range': [40, 60], 'color': 'yellow'},
            {'range': [60, 100], 'color': 'lightgreen'}
        ]
    }
))
g2.plotly_chart(fig_eff, use_container_width=True)

# Expander explanation
with st.expander("ℹ️ How to interpret the gauges"):
    st.markdown("""
    **Battery Remaining Hours Gauge**: 
    Indicates how many hours of autonomy remain based on current daily consumption. Colored zones guide urgency: 

    - Gray: <10% → Critical battery
    - Red: 10–30%
    - Orange: 30–50%
    - Yellow: 50–80%
    - Green: >80% → Fully available

    **Global Efficiency Gauge**:
    Shows how much of the energy chemically stored in methanol is actually converted and delivered to your battery system. 
    Higher efficiency means better performance and optimized methanol use.
    """)

# Scenario Summary Table
st.markdown("### 🧾 Appliance Energy Summary")
summary_df = pd.DataFrame(appliances)
summary_df["Energy (Wh)"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df, use_container_width=True)

# KPI Formula Explanation
with st.expander("📘 KPI Calculation Formulas"):
    st.markdown("""
    **Daily Energy Demand (Wh)** = sum of (Device Power × Hours of Use)

    **Methanol Needed/Day (L)** = Energy Demand (Wh) / Fuel Cell Conversion Rate (approx. 950 Wh/L)

    **Tank Autonomy (days)** = Methanol Volume Available / Daily Methanol Consumption

    **Battery Remaining Autonomy (h)** = Available Battery Energy (Wh) / Average Power Consumption (W)

    **Battery Charge Time (h)** = (Battery Capacity - Remaining Energy) / Fuel Cell Output Power

    **Global Efficiency (%)** = Delivered Energy to Loads / Chemical Energy Input (from Methanol)
    """)

# PDF export with logo and disclaimer
st.markdown("### 📥 Export KPIs as PDF")
if st.button("Generate PDF Report"):
    pdf = FPDF()
    pdf.add_page()
    logo_url = "https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png"
    try:
        logo_data = requests.get(logo_url).content
        logo_path = "/tmp/dashboard_logo.png"
        with open(logo_path, "wb") as f:
            f.write(logo_data)
        pdf.image(logo_path, x=160, y=10, w=30)
    except:
        pass
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt="EFOY KPI Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 10, txt=f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 10, txt=f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 10, txt=f"Battery Remaining Autonomy: {battery_hours:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"Battery Charge Time (DMFC): {charge_time:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"Global System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt="Battery gauge represents remaining hours of autonomy based on current usage. Efficiency gauge reflects how effectively the methanol is converted to usable energy. Ranges are color coded for quick interpretation.")
    pdf.ln(4)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", style='I', size=9)
    pdf.multi_cell(0, 10, txt="Note: All values are estimated for educational and academic purposes only.")
    pdf.ln(3)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", style='', size=9)
    timestamp = datetime.now().strftime("Generated on %Y-%m-%d at %H:%M")
    pdf.cell(200, 10, txt=timestamp, ln=True)
    pdf.set_font("Arial", style='I', size=9)
    pdf.multi_cell(0, 10, txt="Coder: Victor Alvarez Melendez. Master Student in Hydrogen Technology. Technische Hochschule Rosenheim - Campus Burghausen. Bayern, Germany.")

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button("📤 Download Report", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

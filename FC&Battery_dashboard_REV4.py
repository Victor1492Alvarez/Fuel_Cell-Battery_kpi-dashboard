# app.py

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import os
import plotly.graph_objects as go
from kpi_calculator import *

st.set_page_config(page_title="EFOY Hybrid System KPI Dashboard", layout="wide")

st.title("🔋 EFOY Fuel Cell & Battery KPI Dashboard")

st.sidebar.header("🛠️ System Inputs")

# Methanol tank
methanol_liters = st.sidebar.number_input("Available Methanol (liters)", min_value=0.0, value=10.0)

# Appliance inputs
st.sidebar.subheader("⚡ Appliance Usage")
appliances = []
for i in range(3):
    with st.sidebar.expander(f"Appliance #{i+1}"):
        name = st.text_input(f"Name #{i+1}", value=f"Device {i+1}", key=f"name{i}")
        power = st.number_input(f"Power (W) #{i+1}", min_value=0.0, value=50.0, key=f"power{i}")
        hours = st.number_input(f"Usage hours/day #{i+1}", min_value=0.0, value=4.0, key=f"hours{i}")
        appliances.append({'name': name, 'power': power, 'hours': hours})

# Peak load input
peak_power = st.sidebar.number_input("Peak Power Demand (W)", min_value=0.0, value=250.0)

# --- KPI Calculations ---
daily_demand_wh = calculate_daily_energy_demand(appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(methanol_liters, methanol_per_day)
battery_runtime_days = battery_discharge_time(daily_demand_wh)
peak_coverage = peak_load_coverage(peak_power)

# --- KPI Display ---
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
col2.metric("Methanol Needed/Day", f"{methanol_per_day:.2f} L")
col3.metric("Tank Autonomy", f"{autonomy_days:.1f} days")
col4.metric("Battery-Only Runtime", f"{battery_runtime_days:.1f} days")

col5, col6 = st.columns(2)
battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
fuel_cell_energy_kwh = fuel_cell_energy / 1000
fc_efficiency = fuel_cell_efficiency(fuel_cell_energy_kwh, methanol_per_day)

# Gauge interpretation
eff_val = round(fc_efficiency * 100, 1)
if fc_efficiency < 0.2:
    interpretation = "<20%: Possible methanol waste or consumption overestimation"
elif fc_efficiency < 0.5:
    interpretation = "30–40%: System working as expected for DMFC"
else:
    interpretation = ">50%: Likely battery-only or overestimated energy usage"

# Bar chart
fig_bar, ax = plt.subplots(figsize=(6, 4))
ax.bar("Daily Energy", battery_energy, label="Battery", color="#2196F3")
ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#4CAF50")
ax.set_ylabel("Energy (Wh)")
ax.set_title("Battery vs Fuel Cell Contribution")
ax.legend()

# Gauge chart
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=eff_val,
    title={'text': "Overall System Efficiency (%)"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "black"},
        'steps': [
            {'range': [0, 20], 'color': '#FF5E5E'},
            {'range': [20, 50], 'color': '#FFC107'},
            {'range': [50, 100], 'color': '#4CAF50'}
        ]
    }
))
fig_gauge.add_annotation(
    x=0.5, y=0.0,
    text=interpretation,
    showarrow=False,
    font=dict(size=12),
    yshift=20
)

col5.pyplot(fig_bar)
col6.plotly_chart(fig_gauge, use_container_width=True)

# Appliance Summary Table
st.subheader("📋 Appliance Energy Summary")
summary_df = pd.DataFrame(appliances)
summary_df["daily_energy_wh"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df.rename(columns={"name": "Name", "power": "Power (W)", "hours": "Usage (h)", "daily_energy_wh": "Energy (Wh)"}))

# System Constants
constants = {
    "Battery Capacity (Wh)": BATTERY_CAPACITY_WH,
    "Fuel Cell Output Power (W)": FUEL_CELL_OUTPUT_W,
    "Methanol Energy Content (kWh/L)": CHEMICAL_ENERGY_KWH_PER_L
}
st.subheader("⚙️ System Constants")
st.json(constants)

# KPI Formulas
with st.expander("📘 KPI Formulas & Definitions"):
    st.markdown("<small>", unsafe_allow_html=True)
    formulas = get_kpi_formulas()
    for kpi, explanation in formulas.items():
        st.markdown(f"**{kpi}**: {explanation}")
    st.markdown("</small>", unsafe_allow_html=True)

# PDF Export
st.subheader("📄 Export Report")

if st.button("📥 Generate PDF"):

    # Save charts
    fig_bar.savefig("temp_chart.png")
    fig_gauge.write_image("temp_gauge.png")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 10, "EFOY Hybrid Power System Report", ln=0)
    pdf.image("dashboard_logo.png", x=160, y=10, w=30, h=30)
    pdf.ln(20)

    pdf.set_font("Arial", size=9)
    pdf.cell(0, 6, "This is the result of your simulation. Values are generated for academic purposes only.", ln=True)

    # KPIs
    pdf.cell(0, 6, "Key Performance Indicators:", ln=True)
    kpi_data = [
        f"Daily Energy Demand: {daily_demand_wh:.0f} Wh",
        f"Methanol Needed/Day: {methanol_per_day:.2f} L",
        f"Tank Autonomy: {autonomy_days:.1f} days",
        f"Battery-Only Runtime: {battery_runtime_days:.1f} days",
        f"System Efficiency: {eff_val:.1f}%",
        f"Peak Load Coverage: {peak_coverage:.1f}%"
    ]
    for item in kpi_data:
        pdf.cell(0, 5, txt=item, ln=True)

    # Appliance Summary
    pdf.ln(3)
    pdf.cell(0, 6, "Appliance Energy Summary:", ln=True)
    for row in summary_df.itertuples(index=False):
        pdf.cell(0, 5, txt=f"- {row.name}: {row.power} W × {row.hours:.1f} h = {row._3:.0f} Wh", ln=True)

    # System Constants
    pdf.ln(3)
    pdf.cell(0, 6, "System Constants:", ln=True)
    for k, v in constants.items():
        pdf.cell(0, 5, txt=f"- {k}: {v}", ln=True)

    # Insert charts
    pdf.ln(5)
    y = pdf.get_y()
    pdf.image("temp_chart.png", x=10, y=y, w=90)
    pdf.image("temp_gauge.png", x=110, y=y, w=90)

    # Outro
    pdf.set_font("Arial", "I", 8)
    pdf.ln(55)
    pdf.cell(0, 8, "Thanks for using our app. Servus, and enjoy your camping days in the Alps!", ln=True, align='C')

    # Output
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

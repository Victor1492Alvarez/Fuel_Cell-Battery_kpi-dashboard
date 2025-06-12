# FC&Battery_dashboard_REV5.py
import streamlit as st
from kpi_calculator_version2 import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import requests
from PIL import Image
import os

st.set_page_config(page_title="EFOY Hybrid System KPI Dashboard", layout="wide")
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

st.sidebar.header("☞ Customize your appliances")

# Appliance dataset
appliance_defaults = [
    {"name": "Fridge", "power": 45, "hours": 24},
    {"name": "Lights", "power": 10, "hours": 6},
    {"name": "Laptop", "power": 60, "hours": 4},
    {"name": "Electric Fan Heater", "power": 250, "hours": 2},
    {"name": "Water Pump", "power": 50, "hours": 0.5},
    {"name": "Electric Blanket", "power": 100, "hours": 5}
]

custom_appliances = []
for app in appliance_defaults:
    hours = st.sidebar.slider(f"{app['name']} Usage (hrs/day)", 0.0, 24.0, float(app['hours']), 0.25)
    custom_appliances.append({"name": app['name'], "power": app['power'], "hours": hours})

methanol_available = st.sidebar.selectbox("Methanol Tank Setup", [("1 × M10 (10L)", 10), ("2 × M10 (20L)", 20), ("1 × M5 (5L)", 5)], index=1)
selected_tank_liters = methanol_available[1]
peak_power = st.sidebar.slider("⚡ Peak Load (W)", 0, 3000, 997)

# Core calculations
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_hours = battery_discharge_time(daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
efficiency_pct = global_system_efficiency(battery_energy, fuel_cell_energy, methanol_per_day)
peak_coverage_pct = peak_load_coverage(peak_power)
charge_time = battery_charge_time_needed(battery_energy)

# KPI display
st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("⚡ Battery-Only Runtime", f"{battery_hours:.1f} h")
k5.metric("🔁 Charge Time (via Fuel Cell)", f"{charge_time:.1f} h")
k6.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")

# Chart
st.markdown("### 📈 Energy Contribution per Source")
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar("Daily Energy", battery_energy, label="Battery", color="#4CAF50")
ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#2196F3")
ax.set_ylabel("Energy (Wh)")
ax.set_title("Battery vs Fuel Cell Contribution")
ax.legend()
st.pyplot(fig)

# Table
st.markdown("### 🧾 Appliance Summary")
summary_df = pd.DataFrame(custom_appliances)
summary_df["Energy (Wh)"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df.style.format({"power": "{:.0f} W", "hours": "{:.2f} h", "Energy (Wh)": "{:.0f}"}))

st.markdown("### ⚙️ System Constants")
st.table({
    "Battery Capacity": f"{BATTERY_CAPACITY_WH:.0f} Wh",
    "Fuel Cell Output": f"{FUEL_CELL_OUTPUT_W} W",
    "Methanol Consumption Rate": f"{METHANOL_CONSUMPTION_PER_KWH} L/kWh",
    "Battery Voltage": f"{BATTERY_VOLTAGE} V"
})

# PDF Export
st.markdown("### 📤 Export Report")
if st.button("Generate PDF Report"):
    camper_url = "https://cdn.pixabay.com/photo/2017/03/27/14/56/caravan-2179408_1280.jpg"
    alps_url = "https://cdn.pixabay.com/photo/2020/03/17/15/12/alps-4940073_1280.jpg"
    camper_response = requests.get(camper_url)
    alps_response = requests.get(alps_url)
    if camper_response.status_code == 200 and alps_response.status_code == 200:
        camper_img = Image.open(BytesIO(camper_response.content))
        alps_img = Image.open(BytesIO(alps_response.content))
        camper_img.save("camper.png", format="PNG")
        alps_img.save("alps.png", format="PNG")
    else:
        st.error("Failed to load one or both images from the web.")
        st.stop()

    fig.savefig("temp_chart.png")
    pdf = FPDF()
    pdf.add_page()
    pdf.image("camper.png", x=10, y=8, w=40)
    pdf.image("alps.png", x=150, y=8, w=50)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 40, txt="EFOY Hybrid Power System Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 10, txt=f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 10, txt=f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 10, txt=f"Battery Runtime: {battery_hours:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"Charge Time (DMFC): {charge_time:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.image("temp_chart.png", x=10, y=None, w=180)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 10, txt="Report generated for educational purposes – EFOY Pro 2800 + Li 105 architecture. DMFC → Battery → Load only.\nServus! Enjoy your spring weekend in the Alps 🏕️")
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

    for f in ["camper.png", "alps.png", "temp_chart.png"]:
        if os.path.exists(f):
            os.remove(f)

# Footer
st.markdown("---")
st.caption("📘 Case Study – EFOY Pro 2800 + Li 105 Hybrid Energy System Dashboard")

import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import os

# --- Función para limpiar texto no ASCII (como emojis) para PDF ---
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

st.set_page_config(page_title="EFOY Hybrid System KPI Dashboard", layout="wide")
st.title("🔋 EFOY Hybrid System KPI Dashboard")

with st.expander("ℹ️ Click to learn how this simulation works"):
    st.markdown("""
    This tool calculates key performance indicators (KPIs) for a hybrid energy system combining:
    - A **Direct Methanol Fuel Cell (EFOY Pro 2800)**
    - A **LiFePO₄ Battery (EFOY Li 105)**

    The goal is to estimate energy autonomy and methanol consumption for two seasonal use profiles:
    - 🌞 **Summer** (low lighting/heating needs)
    - ❄️ **Winter** (longer usage, heating control active)

    > All values are simulated for educational purposes.
    """)

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

daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
methanol_per_day = calculate_methanol_consumption(daily_demand_wh)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_autonomy_hours = battery_discharge_time(daily_demand_wh)
efficiency_pct = min(system_efficiency(daily_demand_wh / 1000, methanol_per_day), 1.0)
peak_coverage_pct = peak_load_coverage(peak_power)

st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("⚡ Battery-Only Runtime", f"{battery_autonomy_hours:.1f} h")
k5.metric("🌱 System Efficiency", f"{efficiency_pct*100:.1f}%")
k6.metric("🚀 Peak Load Coverage", f"{peak_coverage_pct:.1f}%")

battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar("Daily Energy", battery_energy, label="Battery", color="#4CAF50")
ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#2196F3")
ax.set_ylabel("Energy (Wh)")
ax.set_title("Battery vs Fuel Cell Contribution")
ax.legend()
st.pyplot(fig)

st.markdown("### 🧾 Appliance Energy Summary")
summary_df = pd.DataFrame(custom_appliances)
summary_df["Energy (Wh)"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df.style.format({"power": "{:.0f} W", "hours": "{:.2f} h", "Energy (Wh)": "{:.0f}"}))

st.markdown("### ⚙️ System Constants")
constants = {
    "Battery Capacity": f"{BATTERY_CAPACITY_WH:.0f} Wh",
    "Fuel Cell Max Output": "125 W",
    "Battery Max Discharge": "100 A (1280 W)",
    "Methanol Consumption Rate": "0.9 L/kWh"
}
st.table(constants)

st.markdown("### 📥 Export PDF Report")
if st.button("📤 Generate PDF Report"):
    fig.savefig("temp_chart.png")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=clean_text("🔋 EFOY Hybrid Power System Report"), ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=clean_text(f"Season Selected: {season}"), ln=True)
    pdf.cell(200, 10, txt=f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 10, txt=f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 10, txt=f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 10, txt=f"Battery-Only Runtime: {battery_autonomy_hours:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Peak Load Coverage: {peak_coverage_pct:.1f}%", ln=True)
    pdf.image("temp_chart.png", x=10, y=None, w=180)

    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Appliance Summary:", ln=True)
    for _, row in summary_df.iterrows():
        line = f"- {row['name']}: {row['power']} W × {row['hours']} h = {row['Energy (Wh)']:.0f} Wh"
        pdf.cell(200, 8, txt=clean_text(line), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 10, txt="System Constants:", ln=True)
    pdf.set_font("Arial", size=10)
    for key, val in constants.items():
        pdf.cell(200, 8, txt=f"- {key}: {val}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 10, clean_text("Report generated for educational purposes - Task 2: Camping Truck.\nServus! Enjoy your spring weekend in the Alps 🏕️"))

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

    if os.path.exists("temp_chart.png"):
        os.remove("temp_chart.png")

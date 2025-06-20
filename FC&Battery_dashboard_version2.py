import streamlit as st 
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from kpi_calculator import fuel_cell_efficiency
from io import BytesIO
from fpdf import FPDF
import os

st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px;">
        <h2 style="margin: 0; font-size: 2em;">🔋Camping Truck System Dashboard</h2>
        <img src="https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png" width="140" style="margin-left: 8px;" />
    </div>
""", unsafe_allow_html=True)

def clean_text(text):
    return ''.join(c for c in text if ord(c) < 128)

# --- Profiles ---
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

with st.expander("ℹ️ Click here to learn how this simulation works"):
    st.markdown("""
    Welcome to our Interactive KPI Dashboard!
    This tool calculates key performance indicators (KPIs) for a hybrid energy system combining:
    - A **Direct Methanol Fuel Cell (EFOY Pro 2800)**
    - A **LiFePO₄ Battery (EFOY Li 105)**

    The goal is to estimate energy autonomy and methanol consumption for two seasonal use profiles:
    - 🌞 **Summer**
    - ❄️ **Winter**

    Click on the upper-left corner to customize your appliances!  
    All values are simulated for educational purposes (Task No. 2).
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

# --- Energy Calculations ---
daily_demand_wh = calculate_daily_energy_demand(custom_appliances)
battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
fuel_cell_energy_kwh = fuel_cell_energy / 1000

methanol_per_day = calculate_methanol_consumption(fuel_cell_energy)
autonomy_days = calculate_tank_autonomy(selected_tank_liters, methanol_per_day)
battery_autonomy_hours = battery_discharge_time(daily_demand_wh)
fc_efficiency = fuel_cell_efficiency(fuel_cell_energy_kwh, methanol_per_day) * 100
peak_coverage_pct = peak_load_coverage(peak_power)

# --- KPI Section ---
st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")

k4, k5, k6 = st.columns(3)
k4.metric("⚡ Battery-Only Runtime", f"{battery_autonomy_hours:.1f} h")
k5.metric("🌱 Fuel‑Cell Efficiency", f"{fc_efficiency:.1f}%")
k6.metric("🚀 Peak Load Coverage", f"{peak_coverage_pct:.1f}%")

# --- Chart ---
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar("Daily Energy", battery_energy, label="Battery", color="#2196F3")
ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#4CAF50")
ax.set_ylabel("Energy (Wh)")
ax.set_title("Battery vs Fuel Cell Contribution")
ax.legend()
st.pyplot(fig)

# --- Appliance Summary ---
st.markdown("### 🧾 Appliance Energy Summary")
summary_df = pd.DataFrame(custom_appliances)
summary_df["Energy (Wh)"] = summary_df["power"] * summary_df["hours"]
st.dataframe(summary_df.style.format({"power": "{:.0f} W", "hours": "{:.2f} h", "Energy (Wh)": "{:.0f}"}))

# --- Constants Table ---
st.markdown("### ⚙️ System Constants")
constants = {
    "Battery Capacity": f"{BATTERY_CAPACITY_WH:.0f} Wh",
    "Fuel Cell Max Output": "125 W",
    "Battery Max Discharge": "100 A (1280 W)",
    "Methanol Consumption Rate": "0.9 L/kWh"
}
st.table(constants)

# --- PDF Export ---
if st.button("📤 Generate PDF Report"):
    fig.savefig("temp_chart.png")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "", ln=True)

    x_start = pdf.get_x()
    y_start = pdf.get_y()

    pdf.set_xy(10, 10)
    pdf.cell(120, 10, txt=clean_text("🔋 EFOY Hybrid Power System Report"), ln=0)

    logo_width = 40
    logo_height = 40
    pdf.image("https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png", x=pdf.w - logo_width - 10, y=10, w=logo_width, h=logo_height)

    pdf.ln(20)

    pdf.set_font("Arial", size=9)
    pdf.cell(0, 6, txt=clean_text(f"Season: {season}"), ln=True)

    pdf.cell(0, 6, txt="Key Performance Indicators:", ln=True)
    kpi_data = [
        f"Daily Energy Demand: {daily_demand_wh:.0f} Wh",
        f"Methanol Needed/Day: {methanol_per_day:.2f} L",
        f"Tank Autonomy: {autonomy_days:.1f} days",
        f"Battery-Only Runtime: {battery_autonomy_hours:.1f} h",
        f"Fuel-Cell Efficiency: {fc_efficiency:.1f}%",
        f"Peak Load Coverage: {peak_coverage_pct:.1f}%"
    ]
    for item in kpi_data:
        pdf.cell(0, 5, txt=item, ln=True)

    pdf.ln(3)
    pdf.cell(0, 6, txt="Appliance Summary (W × h = Wh):", ln=True)
    for row in summary_df.itertuples(index=False):
        line = f"- {row.name}: {row.power} × {row.hours:.1f} = {row._3:.0f}"
        pdf.cell(0, 5, txt=clean_text(line), ln=True)

    pdf.ln(3)
    pdf.cell(0, 6, txt="System Constants:", ln=True)
    for k, v in constants.items():
        pdf.cell(0, 5, txt=f"- {k}: {v}", ln=True)

    pdf.ln(2)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, clean_text("Report generated for educational purposes - Task 2: Camping Truck. Servus! Enjoy your spring weekend in the Alps 🏕️"))

    if pdf.get_y() < 210:
        pdf.image("temp_chart.png", x=10, y=pdf.get_y(), w=pdf.w - 20)

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

    if os.path.exists("temp_chart.png"):
        os.remove("temp_chart.png")

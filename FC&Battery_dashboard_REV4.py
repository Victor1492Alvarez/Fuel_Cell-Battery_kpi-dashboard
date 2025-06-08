import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import os
import plotly.graph_objects as go

st.set_page_config(page_title="Hybrid System KPI Dashboard", layout="wide")

st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px;">
        <h2 style="margin: 0; font-size: 2em;">🔋Camping Truck System Dashboard</h2>
        <img src="https://raw.githubusercontent.com/Victor1492Alvarez/Fuel_Cell-Battery_kpi-dashboard/main/dashboard_logo.png" width="140" style="margin-left: 8px;" />
    </div>
""", unsafe_allow_html=True)

def clean_text(text):
    return text.encode('latin1', errors='ignore').decode('latin1')

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
    Welcome to our Interactive KPI Dashboard! This tool calculates key performance indicators (KPIs) for a hybrid energy system combining:
    - A **Direct Methanol Fuel Cell (EFOY Pro 2800)**
    - A **LiFePO₄ Battery (EFOY Li 105)**
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
peak_coverage_pct = peak_load_coverage(peak_power)

battery_energy = min(BATTERY_CAPACITY_WH, daily_demand_wh)
fuel_cell_energy = max(0, daily_demand_wh - BATTERY_CAPACITY_WH)
global_efficiency = global_system_efficiency(battery_energy, fuel_cell_energy, methanol_per_day)

st.markdown("### 📊 Key Performance Indicators")
k1, k2, k3 = st.columns(3)
k1.metric("🔋 Daily Energy Demand", f"{daily_demand_wh:.0f} Wh")
k2.metric("🧪 Methanol Needed/Day", f"{methanol_per_day:.2f} L")
k3.metric("🛢️ Tank Autonomy", f"{autonomy_days:.1f} days")
k4, k5, k6 = st.columns(3)
k4.metric("⚡ Battery-Only Runtime", f"{battery_autonomy_hours:.1f} h")
k5.metric("🌱 System Efficiency", f"{global_efficiency * 100:.1f}%")
k6.metric("🚀 Peak Load Coverage", f"{peak_coverage_pct:.1f}%")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.bar("Daily Energy", battery_energy, label="Battery", color="#2196F3")
    ax.bar("Daily Energy", fuel_cell_energy, bottom=battery_energy, label="Fuel Cell", color="#4CAF50")
    ax.set_ylabel("Energy (Wh)")
    ax.set_title("Battery vs Fuel Cell Contribution")
    ax.legend()
    st.pyplot(fig)

with col2:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=global_efficiency * 100,
        title={'text': "Global Efficiency (%)"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 20], 'color': "#EF5350"},
                {'range': [20, 50], 'color': "#FFEB3B"},
                {'range': [50, 100], 'color': "#66BB6A"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': global_efficiency * 100}
        }
    ))
    fig_gauge.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.caption("""
    🔍 Gauge interpretation:
    - <20% (🔴): Potential inefficient methanol use or overestimated load.
    - 20–50% (🟡): Normal functional range.
    - >50% (🟢): Possibly battery-only supply.
    """)

st.markdown("### 🧾 Energy Summary based on Devices")
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

with st.expander("📘 What are the KPI Formulas about?"):
    st.markdown("""
    <small>
    - **Daily Energy Demand** = Σ(Power × Hours) of all devices<br>
    - **Methanol Needed/Day** = Energy (kWh) × 0.9 L/kWh<br>
    - **Tank Autonomy** = Available Methanol / Daily Consumption<br>
    - **Battery-Only Runtime** = Battery Capacity / Daily Energy<br>
    - **Global System Efficiency** = Useful FC Energy / (Methanol × 1.1 kWh/L)<br>
    - **Peak Load Coverage** = % peak load battery can support (max 1280 W)<br>
    </small>
    """, unsafe_allow_html=True)

if st.button("📤 Generate PDF Report"):
    fig.savefig("temp_chart.png", dpi=300, bbox_inches="tight")
    fig_gauge.write_image("temp_gauge.png", scale=3)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=5)
    pdf.set_font("Arial", size=10)

    # Header
    pdf.set_xy(10, 10)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text("Key Performance Indicators Report - Summary"), ln=True)

    try:
        logo_width = 40
        logo_height = 40
        pdf.image("dashboard_logo.png", x=165, y=4,w=logo_width, h=logo_height)
    except:
        pass

    pdf.set_font("Arial", size=9)
    pdf.ln(12)
    pdf.multi_cell(0, 5, clean_text("This is the result of your simulation. Values are generated for educational and academic purposes only."))

    # KPIs
    pdf.set_font("Arial", 'B', 10)
    pdf.ln(4)
    pdf.cell(0, 6, "Key Performance Indicators", ln=True)
    pdf.set_font("Arial", size=9)
    kpi_text = f"""
- Energy Demand: {daily_demand_wh:.0f} Wh
- Methanol/day: {methanol_per_day:.2f} L
- Tank Autonomy: {autonomy_days:.1f} days
- Battery Runtime: {battery_autonomy_hours:.1f} h
- Global Efficiency: {global_efficiency*100:.1f}%
- Peak Coverage: {peak_coverage_pct:.1f}%
"""
    pdf.multi_cell(0, 5, clean_text(kpi_text))

    # Energy Summary based on Devices
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "Energy Summary based on Devices", ln=True)
    pdf.set_font("Arial", size=9)
    for _, row in summary_df.iterrows():
        appliance_text = f"- {row['name']}: {row['power']} W × {row['hours']:.2f} h = {row['Energy (Wh)']:.0f} Wh"
        pdf.multi_cell(0, 5, clean_text(appliance_text))

    # Constants
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "System Constants", ln=True)
    pdf.set_font("Arial", size=9)
    for k, v in constants.items():
        pdf.cell(0, 5, clean_text(f"- {k}: {v}"), ln=True)

    # Gráficos
    pdf.ln(3)
    pdf.image("temp_chart.png", x=10, y=180, w=90)
    pdf.image("temp_gauge.png", x=110, y=197, w=90)

    # Gauge interpretation
    pdf.set_xy(10, 250)
    pdf.set_font("Arial", size=10)
    interpretation = """
Gauge Interpretation:
- Red (<20%): Potential inefficient methanol use or consumption overestimation.
- Yellow (20–50%): Normal operation.
- Green (>50%): Battery-only use.
"""
    pdf.multi_cell(0, 4, clean_text(interpretation))

    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, clean_text("Thank you for using our app.\nServus! And enjoy your camping days in the Alps!"))

    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

    os.remove("temp_chart.png")
    os.remove("temp_gauge.png")

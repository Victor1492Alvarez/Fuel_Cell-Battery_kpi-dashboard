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
    return ''.join(c for c in text if ord(c) < 128)

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
    Welcome to our Interactive KPI Dashboard!.
    This tool calculates key performance indicators (KPIs) for a hybrid energy system combining:
    - A **Direct Methanol Fuel Cell (EFOY Pro 2800)**
    - A **LiFePO₄ Battery (EFOY Li 105)**

    The goal is to estimate energy autonomy and methanol consumption for two seasonal use profiles:
    - 🌞 **Summer** (low lighting/heating needs)
    - ❄️ **Winter** (longer usage, heating control active)

    Click on upper left corner to display the Menu and customize your Devices!. 
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
        mode="gauge+number+delta",
        value=global_efficiency * 100,
        delta={'reference': 50},
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

with st.expander("📘 KPI Formulas"):
    st.markdown("""
    <small>
    - **Daily Energy Demand** = Σ(Power × Hours) of all devices (user-defined)<br>
    - **Methanol Needed/Day** = Energy (kWh) × 0.9 L/kWh<br>
    - **Tank Autonomy** = Available Methanol / Daily Consumption<br>
    - **Battery-Only Runtime** = Battery Capacity / Daily Energy<br>
    - **Global System Efficiency** = Useful Energy from Fuel Cell / (Methanol Used × 1.1 kWh/L)<br>
    - **Peak Load Coverage** = % of peak load that battery can support (Max: 1280 W)<br>
    </small>
    """, unsafe_allow_html=True)

if st.button("📤 Generate PDF Report"):
    fig.savefig("temp_chart.png")
    fig_gauge.write_image("temp_gauge.png")
    logo_path = "dashboard_logo.png"

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    pdf.set_font("Arial", "B", 14)
    
    # Header
    pdf.cell(0, 10, "Hybrid System KPI Executive Report", ln=1, align="L")
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=260, y=5, w=30)

    pdf.set_font("Arial", "", 10)
    pdf.set_y(20)
    pdf.multi_cell(0, 5, "This is the result of your simulation. Values generated for educational and academic purposes only.", align="L")

    # KPI Table
    pdf.set_font("Arial", "B", 11)
    pdf.ln(4)
    pdf.cell(0, 8, "Key Performance Indicators", ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 6, f"🔋 Daily Energy Demand: {daily_demand_wh:.0f} Wh")
    pdf.cell(95, 6, f"🧪 Methanol Needed/Day: {methanol_per_day:.2f} L")
    pdf.cell(95, 6, f"🛢️ Tank Autonomy: {autonomy_days:.1f} days", ln=1)
    pdf.cell(95, 6, f"⚡ Battery-Only Runtime: {battery_autonomy_hours:.1f} h")
    pdf.cell(95, 6, f"🌱 System Efficiency: {global_efficiency * 100:.1f}%")
    pdf.cell(95, 6, f"🚀 Peak Load Coverage: {peak_coverage_pct:.1f}%", ln=1)

    # Appliance Summary Table
    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Appliance Energy Summary", ln=1)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 6, "Device", 1)
    pdf.cell(35, 6, "Power (W)", 1)
    pdf.cell(35, 6, "Hours", 1)
    pdf.cell(40, 6, "Energy (Wh)", 1, ln=1)
    pdf.set_font("Arial", "", 9)
    for app in custom_appliances:
        pdf.cell(50, 6, app['name'], 1)
        pdf.cell(35, 6, f"{app['power']:.0f}", 1)
        pdf.cell(35, 6, f"{app['hours']:.2f}", 1)
        energy = app['power'] * app['hours']
        pdf.cell(40, 6, f"{energy:.0f}", 1, ln=1)

    # System Constants Table
    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "System Constants", ln=1)
    pdf.set_font("Arial", "", 9)
    for k, v in constants.items():
        pdf.cell(70, 6, k, 1)
        pdf.cell(60, 6, v, 1, ln=1)

    # Graphs
    pdf.ln(3)
    pdf.image("temp_chart.png", x=10, y=130, w=130)
    pdf.image("temp_gauge.png", x=150, y=130, w=130)

    # Final message
       # Final message with interpretation
    pdf.set_y(190)
    pdf.set_font("Arial", "B", 10)

    # Interpretación dinámica de la eficiencia
    efficiency_pct = global_efficiency * 100
    if efficiency_pct < 20:
        interpretation_text = "⚠️ Efficiency < 20%: Possible methanol waste or energy overestimation."
        interpretation_color = (239, 83, 80)  # red
    elif 20 <= efficiency_pct < 50:
        interpretation_text = "⚠️ Efficiency between 30–40%: Normal range for DMFC hybrid systems."
        interpretation_color = (255, 235, 59)  # yellow
    else:
        interpretation_text = "✅ Efficiency > 50%: Warning, possible battery-only estimation or input mismatch."
        interpretation_color = (102, 187, 106)  # green

    pdf.set_text_color(*interpretation_color)
    pdf.multi_cell(0, 6, interpretation_text, align="C")

    # Footer message
    pdf.ln(3)
    pdf.set_text_color(100)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 8, "Thanks for using our app.\nThis tool is intended for academic and educational purposes only.\nServus! and enjoy your camping days in the Alps. ⛰️", align="C")

    # Save to streamlit
    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_executive_report.pdf", mime="application/pdf")

    os.remove("temp_chart.png")
    os.remove("temp_gauge.png")

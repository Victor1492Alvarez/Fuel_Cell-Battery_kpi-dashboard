# app.py
import streamlit as st
from kpi_calculator import *
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import requests
from PIL import Image

# --- Seasonal appliance profiles ---
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

# --- PDF Export ---
st.markdown("### 📥 Export PDF Report")
if st.button("📤 Generate PDF Report"):
    # Download and convert images using Pillow
    camper_url = "https://cdn.pixabay.com/photo/2017/03/27/14/56/caravan-2179408_1280.jpg"
    alps_url = "https://cdn.pixabay.com/photo/2020/03/17/15/12/alps-4940073_1280.jpg"

    camper_img = Image.open(BytesIO(requests.get(camper_url).content))
    alps_img = Image.open(BytesIO(requests.get(alps_url).content))

    camper_img.save("camper.png", format="PNG")
    alps_img.save("alps.png", format="PNG")

    fig.savefig("temp_chart.png")

    pdf = FPDF()
    pdf.add_page()
    pdf.image("camper.png", x=10, y=8, w=40)
    pdf.image("alps.png", x=150, y=8, w=50)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 40, txt="EFOY Hybrid Power System Report", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Season Selected: {season}", ln=True)
    pdf.cell(200, 10, txt=f"Daily Energy Demand: {daily_demand_wh:.0f} Wh", ln=True)
    pdf.cell(200, 10, txt=f"Methanol Needed/Day: {methanol_per_day:.2f} L", ln=True)
    pdf.cell(200, 10, txt=f"Tank Autonomy: {autonomy_days:.1f} days", ln=True)
    pdf.cell(200, 10, txt=f"Battery-Only Runtime: {battery_autonomy_hours:.1f} h", ln=True)
    pdf.cell(200, 10, txt=f"System Efficiency: {efficiency_pct*100:.1f}%", ln=True)
    pdf.cell(200, 10, txt=f"Peak Load Coverage: {peak_coverage_pct:.1f}%", ln=True)
    pdf.image("temp_chart.png", x=10, y=None, w=180)

    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="\nAppliance Summary:", ln=True)
    for index, row in summary_df.iterrows():
        line = f"- {row['name']}: {row['power']} W × {row['hours']} h = {row['Energy (Wh)']:.0f} Wh"
        pdf.cell(200, 8, txt=line, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 10, txt="\nSystem Constants:", ln=True)
    pdf.set_font("Arial", size=10)
    for key, val in constants.items():
        pdf.cell(200, 8, txt=f"- {key}: {val}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 10, txt="Report generated for educational purposes - Task 2: Camping Truck.\nServus! Enjoy your spring weekend in the Alps 🏕️")

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1'))
    st.download_button("📩 Download PDF", data=pdf_output.getvalue(), file_name="efoy_kpi_report.pdf", mime="application/pdf")

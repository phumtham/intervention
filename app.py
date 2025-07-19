
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# Load equipment data
df = pd.read_excel("equipment_costs.xlsx", engine="openpyxl")
equipment_data = df.set_index("equipment").to_dict("index")

# Define healthcare schemes
schemes = {
    "A": "Universal healthcare (ประกันสุขภาพถ้วนหน้า)",
    "B": "UCEP Scheme",
    "C": "Social security Scheme (ประกันสังคม)",
    "D": "Civil service Scheme (จ่ายตรง)",
    "E": "Self pay (เงินสด)"
}

# Define operations and default equipment
operation_defaults = {
    "Diagnostic angiogram": {"Angiogram": 1, "Contrast media": 4, "femoral sheath": 1, "Diagnostic catheter": 1, "0.038 Wire": 1},
    "Cerebral angiogram with simple coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "SL10": 1, "Synchro": 1, "Rhya": 2, "Coil": 5},
    "Cerebral angiogram with transarterial ONYX embolization": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "Apollo": 1, "Mirage": 1, "Rhya": 1, "ONYX ": 2},
    "Cerebral angiogram with transvenous coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 2, "Diagnostic catheter": 2, "Softip guider": 1, "0.038 Wire": 1, "SL10": 1, "Synchro": 1, "Rhya": 3, "Coil": 10},
    "Cerebral angiogram with stent assisted coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "SL10": 2, "Synchro": 1, "Coil": 5, "Neuroform ATLAS": 1, "Rhya": 3}
}

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = 0
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}
if "operation" not in st.session_state:
    st.session_state.operation = ""
if "equipment" not in st.session_state:
    st.session_state.equipment = {}

# Navigation buttons
def next_page():
    st.session_state.page += 1

def prev_page():
    st.session_state.page -= 1

# Page 0: Patient Data
if st.session_state.page == 0:
    st.title("Patient Information")
    st.session_state.patient_data["ชื่อ"] = st.text_input("ชื่อ")
    st.session_state.patient_data["นามสกุล"] = st.text_input("นามสกุล")
    st.session_state.patient_data["HN"] = st.text_input("HN")
    st.session_state.patient_data["Diagnosis"] = st.text_input("Diagnosis")
    scheme = st.selectbox("Healthcare Scheme", list(schemes.keys()), format_func=lambda x: schemes[x])
    st.session_state.patient_data["Scheme"] = scheme
    if st.button("Next"):
        next_page()

# Page 1: Operation Selection
elif st.session_state.page == 1:
    st.title("Select Operation")
    operations = list(operation_defaults.keys()) + ["Others"]
    selected_op = st.selectbox("Operation", operations)
    if selected_op == "Others":
        custom_op = st.text_input("Enter operation name")
        st.session_state.operation = custom_op
    else:
        st.session_state.operation = selected_op
    if st.button("Previous"):
        prev_page()
    if st.button("Next"):
        next_page()

# Page 2: Equipment Selection
elif st.session_state.page == 2:
    st.title("Select Equipment")
    st.subheader(f"Operation: {st.session_state.operation}")
    defaults = operation_defaults.get(st.session_state.operation, {})
    equipment_counts = {}
    for item in equipment_data:
        default = defaults.get(item, 0)
        max_val = 1 if item in ["femoral sheath", "Destination longsheath", "Fubuki Longsheath", "NeuronMAX Longsheath", "Fargo/ FargoMAX", "Sofia 5F ", "Neuroform ATLAS", "Surpass", "Silk Vista", "Copernic balloon ", "Hyperglide balloon", "Exchange wire", "mariner"] else 100
        equipment_counts[item] = st.number_input(item, min_value=0, max_value=max_val, value=default)
    st.session_state.equipment = equipment_counts
    if st.button("Previous"):
        prev_page()
    if st.button("Next"):
        next_page()

# Page 3: Cost Summary
elif st.session_state.page == 3:
    st.title("Cost Summary")
    scheme = st.session_state.patient_data["Scheme"]
    total_cost = 0
    total_reimbursement = 0
    for item, qty in st.session_state.equipment.items():
        cost = equipment_data[item]["Cost"]
        reimb = equipment_data[item][schemes[scheme]]
        total_cost += cost * qty
        total_reimbursement += reimb * qty
    out_of_pocket = max(total_cost - total_reimbursement, 0)
    st.write(f"**Total Cost:** {total_cost:.2f}")
    st.write(f"**Total Reimbursement:** {total_reimbursement:.2f}")
    st.write(f"**Out-of-pocket Cost:** {out_of_pocket:.2f}")
    if st.button("Previous"):
        prev_page()
    if st.button("Next"):
        next_page()

# Page 4: PDF Generation
elif st.session_state.page == 4:
    st.title("Generate PDF Summary")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 50
    pd = st.session_state.patient_data
    c.drawString(x + 300, y, f"ชื่อ: {pd['ชื่อ']} {pd['นามสกุล']}")
    c.drawString(x + 300, y - 20, f"HN: {pd['HN']}")
    c.drawString(x + 300, y - 40, f"Diagnosis: {pd['Diagnosis']}")
    c.drawString(x, y - 80, f"Healthcare Scheme: {schemes[pd['Scheme']]}")
    c.drawString(x, y - 100, f"Operation: {st.session_state.operation}")
    y -= 140
    c.drawString(x, y, "Equipment Used:")
    y -= 20
    for item, qty in st.session_state.equipment.items():
        if qty > 0:
            c.drawString(x + 20, y, f"{item}: {qty}")
            y -= 15
    y -= 10
    c.drawString(x, y, f"Total Cost: {total_cost:.2f}")
    y -= 15
    c.drawString(x, y, f"Total Reimbursement: {total_reimbursement:.2f}")
    y -= 15
    c.drawString(x, y, f"Out-of-pocket Cost: {out_of_pocket:.2f}")
    y -= 40
    c.drawString(x, y, "Patient Signature: __________________________")
    c.save()
    buffer.seek(0)
    st.download_button("Download PDF", buffer, file_name="summary.pdf")
    if st.button("Previous"):
        prev_page()

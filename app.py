
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from io import BytesIO
from datetime import datetime

# Load equipment cost data
df = pd.read_excel("ค่าอุปกรณ์.xlsx", engine="openpyxl")
df.set_index("equipment", inplace=True)

# Mapping for healthcare schemes
scheme_map = {
    "Scheme A : universal healthcare (ประกันสุขภาพถ้วนหน้า)": "Universal healthcare",
    "Scheme B: UCEP Scheme": "UCEP",
    "C: Social security Scheme (ประกันสังคม)": "Social Security",
    "D: Civil service Scheme (จ่ายตรง)": "Civil Servant",
    "E: Self pay (เงินสด)": "Self pay"
}

# Default equipment per operation
operation_defaults = {
    "Diagnostic angiogram": {"Angiogram": 1, "Contrast media": 4, "femoral sheath": 1, "Diagnostic catheter": 1, "0.038 Wire": 1},
    "Cerebral angiogram with simple coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "SL10": 1, "Synchro": 1, "Rhya": 2, "Coil": 5},
    "Cerebral angiogram with transarterial ONYX embolization": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "Apollo": 1, "Mirage": 1, "Rhya": 1, "ONYX ": 2},
    "Cerebral angiogram with transvenous coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 2, "Diagnostic catheter": 2, "Softip guider": 1, "0.038 Wire": 1, "SL10": 1, "Synchro": 1, "Rhya": 3, "Coil": 10},
    "Cerebral angiogram with stent assisted coiling": {"Angiogram": 1, "Contrast media": 6, "femoral sheath": 1, "Softip guider": 1, "0.038 Wire": 1, "SL10": 2, "Synchro": 1, "Coil": 5, "Neuroform ATLAS": 1, "Rhya": 3}
}

# Equipment limited to 0 or 1
limited_equipment = ["femoral sheath", "Destination longsheath", "Fubuki Longsheath", "NeuronMAX Longsheath", "Fargo/ FargoMAX", "Sofia 5F ", "Neuroform ATLAS", "Surpass", "Silk Vista", "Copernic balloon ", "Hyperglide balloon", "exchange wire", "mariner"]

# Page 1: Patient Data
if "page" not in st.session_state:
    st.session_state.page = 1

if st.session_state.page == 1:
    st.title("Patient Information")
    name = st.text_input("ชื่อ")
    surname = st.text_input("นามสกุล")
    hn = st.text_input("HN")
    diagnosis = st.text_input("Diagnosis")
    scheme = st.selectbox("Healthcare Scheme", list(scheme_map.keys()))
    if st.button("Next"):
        st.session_state.patient_data = {"ชื่อ": name, "นามสกุล": surname, "HN": hn, "Diagnosis": diagnosis, "Scheme": scheme}
        st.session_state.page = 2
    st.stop()

# Page 2: Operation Selection
if st.session_state.page == 2:
    st.title("Select Operation")
    operations = list(operation_defaults.keys()) + ["Others"]
    operation = st.selectbox("Operation", operations)
    other_op = ""
    if operation == "Others":
        other_op = st.text_input("Specify Operation")
    if st.button("Next"):
        st.session_state.operation = other_op if operation == "Others" else operation
        st.session_state.page = 3
    st.stop()

# Page 3: Equipment Selection
if st.session_state.page == 3:
    st.title("Select Equipment Used")
    default_equipment = operation_defaults.get(st.session_state.operation, {})
    equipment_used = {}
    for item in df.index:
        default = default_equipment.get(item, 0)
        max_val = 1 if item in limited_equipment else 20
        qty = st.number_input(f"{item}", min_value=0, max_value=max_val, value=default, step=1)
        if qty > 0:
            equipment_used[item] = qty
    if st.button("Next"):
        st.session_state.equipment_used = equipment_used
        st.session_state.page = 4
    st.stop()

# Page 4: Cost Summary
if st.session_state.page == 4:
    st.title("Cost Summary")
    scheme_col = scheme_map[st.session_state.patient_data["Scheme"]]
    total_cost = 0
    total_reimb = 0
    for item, qty in st.session_state.equipment_used.items():
        cost = df.at[item, "Cost"] * qty
        reimb = df.at[item, scheme_col] * qty
        total_cost += cost
        total_reimb += reimb
    out_of_pocket = max(0, total_cost - total_reimb)
    st.write(f"**Total Cost:** {total_cost:,.2f} THB")
    st.write(f"**Total Reimbursement:** {total_reimb:,.2f} THB")
    st.write(f"**Out-of-pocket:** {out_of_pocket:,.2f} THB")
    if st.button("Generate PDF"):
        st.session_state.summary = {"Total Cost": total_cost, "Total Reimbursement": total_reimb, "Out-of-pocket": out_of_pocket}
        st.session_state.page = 5
    st.stop()

# Page 5: PDF Generation
if st.session_state.page == 5:
    st.title("Download PDF Summary")
    buffer = BytesIO()
    doc = fitz.open()
    page = doc.new_page()
    patient = st.session_state.patient_data
    summary = st.session_state.summary
    equip = st.session_state.equipment_used
    op = st.session_state.operation
    scheme = patient["Scheme"]

    y = 50
    page.insert_text((350, y), f"{patient['ชื่อ']} {patient['นามสกุล']}", fontsize=12)
    y += 20
    page.insert_text((350, y), f"HN: {patient['HN']}", fontsize=12)
    y += 20
    page.insert_text((350, y), f"Diagnosis: {patient['Diagnosis']}", fontsize=12)
    y += 40
    page.insert_text((50, y), f"Healthcare Scheme: {scheme}", fontsize=12)
    y += 20
    page.insert_text((50, y), f"Operation: {op}", fontsize=12)
    y += 30
    page.insert_text((50, y), "Equipment Used:", fontsize=12)
    for item, qty in equip.items():
        y += 20
        page.insert_text((70, y), f"{item}: {qty}", fontsize=11)
    y += 30
    page.insert_text((50, y), f"Total Cost: {summary['Total Cost']:,.2f} THB", fontsize=12)
    y += 20
    page.insert_text((50, y), f"Total Reimbursement: {summary['Total Reimbursement']:,.2f} THB", fontsize=12)
    y += 20
    page.insert_text((50, y), f"Out-of-pocket: {summary['Out-of-pocket']:,.2f} THB", fontsize=12)
    y += 50
    page.insert_text((50, y), "Patient Signature: ___________________________", fontsize=12)
    doc.save(buffer)
    st.download_button("Download PDF", buffer.getvalue(), file_name="summary.pdf", mime="application/pdf")

import streamlit as st
import pandas as pd
import numpy as np
import random
import datetime
import json

st.set_page_config(page_title="BMS Dashboard", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>🔋 Battery Management System Dashboard</h1>",
    unsafe_allow_html=True,
)

# ------------------------------------
# Sidebar Navigation
# ------------------------------------
page = st.sidebar.radio(
    "📁 Navigate",
    ["Main Monitoring", "Configure Cells", "User Controls", "Data Logging", "Real-Time Sensor"],
    format_func=lambda x: f"🔹 {x}",
)

# ------------------------------------
# Simulate Battery Data Function
# ------------------------------------
def simulate_cell_data(cell_type):
    voltage = round(random.uniform(3.0, 3.6), 3) if cell_type == "lfp" else round(random.uniform(3.3, 4.2), 3)
    current = round(random.uniform(-5.0, 5.0), 2)
    temp = round(random.uniform(25.0, 45.0), 1)
    soc = round(random.uniform(50, 100), 1)
    soh = round(random.uniform(85, 100), 1)
    return {
        "Voltage (V)": voltage,
        "Current (A)": current,
        "Temperature (°C)": temp,
        "Capacity (Wh)": round(voltage * current, 2),
        "SoC (%)": soc,
        "SoH (%)": soh,
        "Alert": "None" if temp < 42 else "Overheat"
    }

# ------------------------------------
# Main Monitoring
# ------------------------------------
if page == "Main Monitoring":
    st.subheader("📊 Real-Time Battery Monitoring")
    cell_type = st.selectbox("Cell Type", ["lfp", "nmc"], index=0)
    cycle_count = st.slider("🔁 Cycle Count", 0, 5000, 200)

    df = pd.DataFrame([simulate_cell_data(cell_type) for _ in range(8)])
    df.index = [f"Cell {i+1}" for i in range(8)]

    # KPIs
    total_voltage = df["Voltage (V)"].sum()
    total_current = df["Current (A)"].sum()
    total_power = total_voltage * total_current
    avg_temp = df["Temperature (°C)"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔋 Total Voltage", f"{total_voltage:.2f} V")
    col2.metric("⚡ Total Current", f"{total_current:.2f} A")
    col3.metric("🔌 Total Power", f"{total_power:.2f} W")
    col4.metric("🔁 Cycles", f"{cycle_count}")

    st.markdown("### Individual Cell Overview")
    for i in range(8):
        with st.expander(f"🔎 Cell {i+1} Details"):
            cdata = df.iloc[i]
            st.progress(int(cdata["SoC (%)"]), f"SoC: {cdata['SoC (%)']}%")
            st.write("📐 Voltage:", cdata["Voltage (V)"], "V")
            st.write("🔥 Temp:", cdata["Temperature (°C)"], "°C")
            st.write("🔋 Current:", cdata["Current (A)"], "A")
            st.write("💠 SoH:", cdata["SoH (%)"], "%")
            if cdata["Alert"] != "None":
                st.error(f"🚨 Alert: {cdata['Alert']}")

    st.markdown("### 📈 Voltage Distribution")
    st.bar_chart(df["Voltage (V)"])

# ------------------------------------
# Configure Cells
# ------------------------------------
elif page == "Configure Cells":
    st.subheader("🔧 Configure Battery Cells")
    if "cell_types" not in st.session_state:
        st.session_state.cell_types = ["lfp"] * 8

    cols = st.columns(8)
    for i in range(8):
        with cols[i]:
            st.session_state.cell_types[i] = st.selectbox(
                f"Cell {i+1}",
                ["lfp", "nmc"],
                key=f"cell_type_{i}",
                index=["lfp", "nmc"].index(st.session_state.cell_types[i])
            )

    st.markdown("---")
    st.subheader("📋 Configured Cell Data")

    config_data = {}
    for idx, cell_type in enumerate(st.session_state.cell_types, 1):
        data = simulate_cell_data(cell_type)
        config_data[f"Cell_{idx}_{cell_type.upper()}"] = data

    df_config = pd.DataFrame.from_dict(config_data, orient="index")
    df_config.index.name = "Cell"
    st.dataframe(df_config.style.highlight_max(axis=0))

    csv = df_config.to_csv().encode("utf-8")
    st.download_button("📥 Download Config Data", csv, "cell_config.csv", "text/csv")

# ------------------------------------
# User Controls
# ------------------------------------
elif page == "User Controls":
    st.subheader("🎛️ BMS User Controls")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Start Charging"):
            st.success("🔌 Charging started.")
        if st.button("⏹️ Stop Charging"):
            st.warning("Charging stopped.")

    with col2:
        if st.button("▶️ Start Discharging"):
            st.success("🔋 Discharging started.")
        if st.button("⏹️ Stop Discharging"):
            st.warning("Discharging stopped.")

    st.markdown("### ⚙️ Advanced Options")
    balance = st.checkbox("🔄 Enable Cell Balancing")
    voltage_limit = st.slider("⚡ Overvoltage Limit", 3.0, 4.5, 4.2)
    st.info("Note: These controls are placeholders for integration with real hardware.")

# ------------------------------------
# Data Logging
# ------------------------------------
elif page == "Data Logging":
    st.subheader("📝 Log Battery Data")

    log_data = {
        "Cell": [f"Cell {i+1}" for i in range(8)],
        "Voltage": [round(3.2 + i * 0.05, 3) for i in range(8)],
        "Temperature": [round(30 + i, 1) for i in range(8)],
        "Current": [round(0.5 + i * 0.1, 2) for i in range(8)],
    }
    df_log = pd.DataFrame(log_data)
    st.dataframe(df_log)

    if st.button("💾 Save Log Snapshot"):
        df_log["Timestamp"] = datetime.datetime.now().isoformat()
        df_log.to_csv("bms_log.csv", mode="a", index=False, header=True)
        st.success("📁 Log saved to `bms_log.csv`")

# ------------------------------------
# Real-Time Sensor
# ------------------------------------
elif page == "Real-Time Sensor":
    st.subheader("📡 Real-Time Sensor Input")
    try:
        import serial
        ser = serial.Serial('COM3', 9600, timeout=2)
        line = ser.readline().decode("utf-8").strip()
        sensor_data = json.loads(line)
        if "cells" in sensor_data:
            df_sensor = pd.DataFrame(sensor_data["cells"])
            st.dataframe(df_sensor)
        else:
            st.warning("⚠️ No sensor data received.")
    except Exception as e:
        st.error(f"❌ Sensor Error: {e}")

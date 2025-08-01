import streamlit as st
import pandas as pd
import numpy as np
import random
import datetime
import json
import time
import io

st.set_page_config(page_title="BMS Dashboard", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>🔋 Battery Management System Dashboard</h1>",
    unsafe_allow_html=True,
)

# Initialize session state for workflow management
if "workflow_active" not in st.session_state:
    st.session_state.workflow_active = False
if "current_phase" not in st.session_state:
    st.session_state.current_phase = "idle"
if "phase_start_time" not in st.session_state:
    st.session_state.phase_start_time = None
if "workflow_logs" not in st.session_state:
    st.session_state.workflow_logs = []
if "cell_working_conditions" not in st.session_state:
    st.session_state.cell_working_conditions = ["Normal"] * 8

# ------------------------------------
# Sidebar Navigation
# ------------------------------------
page = st.sidebar.radio(
    "📁 Navigate",
    ["Main Monitoring", "Workflow Management", "Configure Cells", "User Controls", "Data Logging", "Real-Time Sensor"],
    format_func=lambda x: f"🔹 {x}",
)

# ------------------------------------
# Enhanced Cell Data Simulation
# ------------------------------------
def simulate_cell_data(cell_type, working_condition="Normal", phase="idle"):
    # Base voltage ranges
    if cell_type == "lfp":
        base_voltage = random.uniform(3.0, 3.6)
    else:
        base_voltage = random.uniform(3.3, 4.2)
    
    # Adjust parameters based on phase
    if phase == "charging":
        current = round(random.uniform(1.0, 5.0), 2)  # Positive current for charging
        voltage = min(base_voltage * 1.1, 4.2 if cell_type == "nmc" else 3.6)
        temp = round(random.uniform(30.0, 50.0), 1)  # Higher temp during charging
        soc_change = 2.0
    elif phase == "discharging":
        current = round(random.uniform(-5.0, -1.0), 2)  # Negative current for discharging
        voltage = base_voltage * 0.9
        temp = round(random.uniform(28.0, 45.0), 1)
        soc_change = -1.5
    else:  # idle
        current = round(random.uniform(-0.5, 0.5), 2)  # Minimal current
        voltage = base_voltage
        temp = round(random.uniform(25.0, 35.0), 1)  # Lower temp when idle
        soc_change = 0
    
    # Adjust for working condition
    if working_condition == "Degraded":
        voltage *= 0.95
        temp += 5
        soc_change *= 0.8
    elif working_condition == "Critical":
        voltage *= 0.85
        temp += 10
        soc_change *= 0.5
    elif working_condition == "Faulty":
        voltage *= 0.7
        temp += 15
        current = 0
        soc_change = 0
    
    # Calculate SoC (simulate gradual change)
    base_soc = random.uniform(50, 100)
    if "last_soc" not in st.session_state:
        st.session_state.last_soc = [base_soc] * 8
    
    soc = max(0, min(100, base_soc + soc_change))
    soh = round(random.uniform(85, 100), 1)
    
    # Determine alerts
    alerts = []
    if temp > 45:
        alerts.append("Overheat")
    if voltage < 2.5:
        alerts.append("Undervoltage")
    if voltage > (4.2 if cell_type == "nmc" else 3.6):
        alerts.append("Overvoltage")
    if working_condition in ["Critical", "Faulty"]:
        alerts.append(f"Cell {working_condition}")
    
    return {
        "Voltage (V)": round(voltage, 3),
        "Current (A)": current,
        "Temperature (°C)": temp,
        "Capacity (Wh)": round(voltage * abs(current), 2),
        "SoC (%)": round(soc, 1),
        "SoH (%)": soh,
        "Working_Condition": working_condition,
        "Phase": phase.capitalize(),
        "Alert": "; ".join(alerts) if alerts else "None"
    }

def get_working_condition_color(condition):
    colors = {
        "Normal": "🟢",
        "Degraded": "🟡",
        "Critical": "🟠", 
        "Faulty": "🔴"
    }
    return colors.get(condition, "⚪")

# ------------------------------------
# Main Monitoring
# ------------------------------------
if page == "Main Monitoring":
    st.subheader("📊 Real-Time Battery Monitoring")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        cell_type = st.selectbox("Cell Type", ["lfp", "nmc"], index=0)
        cycle_count = st.slider("🔁 Cycle Count", 0, 5000, 200)
    
    with col2:
        if st.session_state.workflow_active:
            st.success(f"🔄 Workflow Active: {st.session_state.current_phase.upper()}")
            if st.session_state.phase_start_time:
                elapsed = datetime.datetime.now() - st.session_state.phase_start_time
                st.info(f"⏱️ Phase Duration: {str(elapsed).split('.')[0]}")
        else:
            st.info("⏸️ Workflow Inactive")

    # Generate cell data
    df = pd.DataFrame([
        simulate_cell_data(
            cell_type, 
            st.session_state.cell_working_conditions[i],
            st.session_state.current_phase
        ) for i in range(8)
    ])
    df.index = [f"Cell {i+1}" for i in range(8)]

    # KPIs
    total_voltage = df["Voltage (V)"].sum()
    total_current = df["Current (A)"].sum()
    total_power = total_voltage * total_current
    avg_temp = df["Temperature (°C)"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🔋 Total Voltage", f"{total_voltage:.2f} V")
    col2.metric("⚡ Total Current", f"{total_current:.2f} A")
    col3.metric("🔌 Total Power", f"{total_power:.2f} W")
    col4.metric("🌡️ Avg Temp", f"{avg_temp:.1f} °C")
    col5.metric("🔁 Cycles", f"{cycle_count}")

    # Working Conditions Overview
    st.markdown("### 🔍 Cell Working Conditions")
    condition_cols = st.columns(8)
    for i in range(8):
        with condition_cols[i]:
            condition = st.session_state.cell_working_conditions[i]
            color = get_working_condition_color(condition)
            st.markdown(f"**Cell {i+1}**")
            st.markdown(f"{color} {condition}")

    st.markdown("### Individual Cell Overview")
    for i in range(8):
        with st.expander(f"🔎 Cell {i+1} Details - {get_working_condition_color(st.session_state.cell_working_conditions[i])} {st.session_state.cell_working_conditions[i]}"):
            cdata = df.iloc[i]
            st.progress(int(cdata["SoC (%)"]), f"SoC: {cdata['SoC (%)']}%")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("📐 Voltage:", cdata["Voltage (V)"], "V")
                st.write("🔥 Temp:", cdata["Temperature (°C)"], "°C")
                st.write("🔋 Current:", cdata["Current (A)"], "A")
            with col2:
                st.write("💠 SoH:", cdata["SoH (%)"], "%")
                st.write("⚙️ Phase:", cdata["Phase"])
                st.write("🔧 Condition:", cdata["Working_Condition"])
            
            if cdata["Alert"] != "None":
                st.error(f"🚨 Alert: {cdata['Alert']}")

    st.markdown("### 📈 Real-time Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(df["Voltage (V)"])
    with col2:
        st.bar_chart(df["Temperature (°C)"])

# ------------------------------------
# NEW: Workflow Management
# ------------------------------------
elif page == "Workflow Management":
    st.subheader("🔄 Battery Workflow Management")
    
    # Workflow Configuration
    st.markdown("### ⚙️ Configure Workflow")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        charge_duration = st.number_input("Charging Duration (minutes)", min_value=1, max_value=1440, value=30)
    with col2:
        idle_duration = st.number_input("Idle Duration (minutes)", min_value=1, max_value=1440, value=15)
    with col3:
        discharge_duration = st.number_input("Discharge Duration (minutes)", min_value=1, max_value=1440, value=20)
    
    # Cell Working Conditions Configuration
    st.markdown("### 🔧 Set Cell Working Conditions")
    condition_options = ["Normal", "Degraded", "Critical", "Faulty"]
    
    cols = st.columns(4)
    for i in range(8):
        col_idx = i % 4
        with cols[col_idx]:
            st.session_state.cell_working_conditions[i] = st.selectbox(
                f"Cell {i+1}",
                condition_options,
                key=f"condition_{i}",
                index=condition_options.index(st.session_state.cell_working_conditions[i])
            )
    
    st.markdown("---")
    
    # Workflow Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Workflow", disabled=st.session_state.workflow_active):
            st.session_state.workflow_active = True
            st.session_state.current_phase = "charging"
            st.session_state.phase_start_time = datetime.datetime.now()
            st.session_state.workflow_config = {
                "charge_duration": charge_duration,
                "idle_duration": idle_duration,
                "discharge_duration": discharge_duration
            }
            st.success("Workflow started with charging phase!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause Workflow", disabled=not st.session_state.workflow_active):
            st.session_state.workflow_active = False
            st.warning("Workflow paused!")
            st.rerun()
    
    with col3:
        if st.button("🛑 Stop Workflow"):
            st.session_state.workflow_active = False
            st.session_state.current_phase = "idle"
            st.session_state.phase_start_time = None
            st.error("Workflow stopped!")
            st.rerun()
    
    # Current Status
    if st.session_state.workflow_active and st.session_state.phase_start_time:
        st.markdown("### 📊 Current Workflow Status")
        elapsed_time = datetime.datetime.now() - st.session_state.phase_start_time
        elapsed_minutes = elapsed_time.total_seconds() / 60
        
        current_phase = st.session_state.current_phase
        if "workflow_config" in st.session_state:
            config = st.session_state.workflow_config
            
            if current_phase == "charging" and elapsed_minutes >= config["charge_duration"]:
                st.session_state.current_phase = "idle"
                st.session_state.phase_start_time = datetime.datetime.now()
                st.rerun()
            elif current_phase == "idle" and elapsed_minutes >= config["idle_duration"]:
                st.session_state.current_phase = "discharging"
                st.session_state.phase_start_time = datetime.datetime.now()
                st.rerun()
            elif current_phase == "discharging" and elapsed_minutes >= config["discharge_duration"]:
                st.session_state.workflow_active = False
                st.session_state.current_phase = "idle"
                st.session_state.phase_start_time = None
                st.success("Workflow completed!")
                st.rerun()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Phase", current_phase.upper())
        col2.metric("Elapsed Time", f"{int(elapsed_minutes)}m {int(elapsed_time.seconds % 60)}s")
        
        if "workflow_config" in st.session_state:
            phase_duration = st.session_state.workflow_config.get(f"{current_phase}_duration", 0)
            remaining = max(0, phase_duration - elapsed_minutes)
            col3.metric("Time Remaining", f"{int(remaining)}m")
            
            # Progress bar
            progress = min(1.0, elapsed_minutes / phase_duration) if phase_duration > 0 else 0
            st.progress(progress, f"Phase Progress: {progress*100:.0f}%")
    
    # Workflow Logs Display
    if st.session_state.workflow_logs:
        st.markdown("### 📋 Recent Workflow Logs")
        recent_logs = st.session_state.workflow_logs[-10:]  # Show last 10 entries
        for log in reversed(recent_logs):
            st.text(f"{log['timestamp']} - {log['phase'].upper()}: {log['message']}")

# ------------------------------------
# Configure Cells (Updated)
# ------------------------------------
elif page == "Configure Cells":
    st.subheader("🔧 Configure Battery Cells")
    if "cell_types" not in st.session_state:
        st.session_state.cell_types = ["lfp"] * 8

    st.markdown("### Cell Types Configuration")
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
    st.subheader("📋 Current Cell Configuration")

    config_data = {}
    for idx, (cell_type, condition) in enumerate(zip(st.session_state.cell_types, st.session_state.cell_working_conditions), 1):
        data = simulate_cell_data(cell_type, condition, st.session_state.current_phase)
        config_data[f"Cell_{idx}_{cell_type.upper()}"] = data

    df_config = pd.DataFrame.from_dict(config_data, orient="index")
    df_config.index.name = "Cell"
    st.dataframe(df_config.style.highlight_max(axis=0))

    csv = df_config.to_csv().encode("utf-8")
    st.download_button("📥 Download Config Data", csv, f"cell_config_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")

# ------------------------------------
# User Controls (Enhanced)
# ------------------------------------
elif page == "User Controls":
    st.subheader("🎛️ BMS User Controls")
    
    # Manual Phase Control
    st.markdown("### 🎮 Manual Phase Control")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔌 Start Charging"):
            st.session_state.current_phase = "charging"
            st.session_state.phase_start_time = datetime.datetime.now()
            st.success("🔌 Charging started manually.")
            
    with col2:
        if st.button("⏸️ Set Idle"):
            st.session_state.current_phase = "idle"
            st.session_state.phase_start_time = datetime.datetime.now()
            st.info("⏸️ System set to idle.")
            
    with col3:
        if st.button("🔋 Start Discharging"):
            st.session_state.current_phase = "discharging"
            st.session_state.phase_start_time = datetime.datetime.now()
            st.success("🔋 Discharging started manually.")

    st.markdown("### ⚙️ Advanced Options")
    balance = st.checkbox("🔄 Enable Cell Balancing")
    voltage_limit = st.slider("⚡ Overvoltage Limit", 3.0, 4.5, 4.2)
    temp_limit = st.slider("🌡️ Temperature Limit (°C)", 40, 60, 50)
    
    st.markdown("### 🚨 Emergency Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚨 Emergency Stop", type="primary"):
            st.session_state.workflow_active = False
            st.session_state.current_phase = "idle"
            st.error("🚨 Emergency stop activated!")
    
    with col2:
        if st.button("🔄 Reset All"):
            st.session_state.workflow_active = False
            st.session_state.current_phase = "idle"
            st.session_state.workflow_logs = []
            st.session_state.cell_working_conditions = ["Normal"] * 8
            st.success("🔄 System reset completed!")

# ------------------------------------
# Enhanced Data Logging
# ------------------------------------
elif page == "Data Logging":
    st.subheader("📝 Advanced Data Logging")
    
    # Auto-log workflow data
    if st.session_state.workflow_active:
        current_data = {}
        for i in range(8):
            cell_data = simulate_cell_data(
                st.session_state.cell_types[i] if "cell_types" in st.session_state else "lfp",
                st.session_state.cell_working_conditions[i],
                st.session_state.current_phase
            )
            current_data[f"Cell_{i+1}"] = cell_data
        
        # Add timestamp and phase info
        log_entry = {
            "Timestamp": datetime.datetime.now().isoformat(),
            "Phase": st.session_state.current_phase,
            "Workflow_Active": st.session_state.workflow_active,
            **current_data
        }
        
        # Auto-save every few seconds (simulated)
        if len(st.session_state.workflow_logs) == 0 or \
           (datetime.datetime.now() - datetime.datetime.fromisoformat(st.session_state.workflow_logs[-1]["timestamp"])).seconds > 10:
            st.session_state.workflow_logs.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "phase": st.session_state.current_phase,
                "message": f"Auto-logged data during {st.session_state.current_phase} phase"
            })

    # Display current session data
    log_data = {
        "Cell": [f"Cell {i+1}" for i in range(8)],
        "Voltage": [round(3.2 + i * 0.05 + random.uniform(-0.1, 0.1), 3) for i in range(8)],
        "Temperature": [round(30 + i + random.uniform(-2, 2), 1) for i in range(8)],
        "Current": [round((0.5 + i * 0.1) * (1 if st.session_state.current_phase == "charging" else -1 if st.session_state.current_phase == "discharging" else 0), 2) for i in range(8)],
        "Working_Condition": st.session_state.cell_working_conditions,
        "Phase": [st.session_state.current_phase.capitalize()] * 8
    }
    df_log = pd.DataFrame(log_data)
    st.dataframe(df_log)

    # Download options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Current Snapshot"):
            df_log["Timestamp"] = datetime.datetime.now().isoformat()
            csv_data = df_log.to_csv(index=False)
            st.download_button(
                "📥 Download Current Data",
                csv_data,
                f"bms_snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
            st.success("📁 Snapshot ready for download!")
    
    with col2:
        if st.button("📊 Generate Phase Report"):
            if st.session_state.workflow_logs:
                phase_data = []
                for log in st.session_state.workflow_logs:
                    phase_data.append({
                        "Timestamp": log["timestamp"],
                        "Phase": log["phase"],
                        "Message": log["message"]
                    })
                df_phases = pd.DataFrame(phase_data)
                csv_phases = df_phases.to_csv(index=False)
                st.download_button(
                    "📥 Download Phase Report",
                    csv_phases,
                    f"phase_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
                st.success("📊 Phase report ready!")
    
    with col3:
        if st.button("🗂️ Export All Data"):
            # Combine all data
            all_data = {
                "current_snapshot": df_log.to_dict(),
                "workflow_logs": st.session_state.workflow_logs,
                "cell_conditions": st.session_state.cell_working_conditions,
                "current_phase": st.session_state.current_phase,
                "export_timestamp": datetime.datetime.now().isoformat()
            }
            json_data = json.dumps(all_data, indent=2)
            st.download_button(
                "📥 Download Complete Dataset",
                json_data,
                f"complete_bms_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
            st.success("🗂️ Complete dataset ready!")

# ------------------------------------
# Real-Time Sensor (Enhanced)
# ------------------------------------
elif page == "Real-Time Sensor":
    st.subheader("📡 Real-Time Sensor Input")
    
    # Simulated sensor data (replace with actual sensor integration)
    st.markdown("### 🔌 Sensor Connection Status")
    sensor_connected = st.checkbox("Simulate Sensor Connection", value=False)
    
    if sensor_connected:
        st.success("✅ Sensor connected successfully")
        
        # Simulate real-time data
        sensor_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cells": []
        }
        
        for i in range(8):
            cell_data = simulate_cell_data(
                st.session_state.cell_types[i] if "cell_types" in st.session_state else "lfp",
                st.session_state.cell_working_conditions[i],
                st.session_state.current_phase
            )
            sensor_data["cells"].append({
                "cell_id": f"Cell_{i+1}",
                **cell_data
            })
        
        df_sensor = pd.DataFrame(sensor_data["cells"])
        st.dataframe(df_sensor)
        
        # Real-time charts
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(df_sensor.set_index("cell_id")["Voltage (V)"])
        with col2:
            st.line_chart(df_sensor.set_index("cell_id")["Temperature (°C)"])
            
    else:
        st.warning("⚠️ No sensor connection. Enable simulation to see data.")
        st.code("""
# For real hardware integration, replace this section with:
try:
    import serial
    ser = serial.Serial('COM3', 9600, timeout=2)
    line = ser.readline().decode("utf-8").strip()
    sensor_data = json.loads(line)
    # Process sensor_data...
except Exception as e:
    st.error(f"❌ Sensor Error: {e}")
        """)

# Auto-refresh for active workflows
if st.session_state.workflow_active:
    time.sleep(1)  # Add small delay for demo purposes
    st.rerun()

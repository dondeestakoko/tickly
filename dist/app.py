import streamlit as st
import subprocess
import os
import pandas as pd
import time
import signal

# Paths
EXE_PATH = "detectimage.exe"
CSV_PATH = "receipt_data.csv"

# Store process ID
process = None

st.title("Receipt Data Viewer")

# Start the executable
if st.button("Run Program"):
    if os.path.exists(EXE_PATH):
        with st.spinner("Processing... Please wait"):
            try:
                process = subprocess.Popen(EXE_PATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                st.success("Program started! The CSV file will be updated live.")
            except Exception as e:
                st.error(f"Error executing file: {e}")
    else:
        st.error("Executable file not found!")

# Live update CSV
st.subheader("Live Receipt Data")
data_placeholder = st.empty()

while True:
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        data_placeholder.dataframe(df)  # Refresh table
    time.sleep(2)  # Refresh every 2 seconds

# Stop the process when the app is closed
def stop_process():
    global process
    if process:
        process.terminate()  # Stop gracefully
        process.wait()
        st.warning("Process stopped.")

# Catch Streamlit shutdown
st.on_session_end(stop_process)

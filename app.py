from cryptography.fernet import Fernet
from datetime import datetime
import streamlit as st
import pandas as pd
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom
from io import BytesIO
from soap_client import send_to_uiic  #  SOAP sending function
from excel_to_xml import convert_excel_to_xml  #  Excel → XML converter
import socket
import os
import csv
import pytz

# ------------------------------

# Key generate once & save to file
# Load pre-generated Fernet key
def load_key(path="fernet_key.key"):
    with open(path, "rb") as f:
        return f.read()

KEY = load_key()  # Load your single master key
fernet = Fernet(KEY)

# Encrypt file bytes
def encrypt_file(file_bytes):
    return fernet.encrypt(file_bytes)

LOG_FILE = "logs.csv"

def log_upload(filename, ip):
    ist = pytz.timezone('Asia/Kolkata')
    ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")  # IST timestamp
    header = ["filename", "timestamp_ist", "client_ip"]
    
    
    # Create file with header if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
    
    # Append log entry
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([filename, ts, ip])

st.set_page_config(page_title="UIIC Claim Upload", page_icon="🧾", layout="wide")
st.title("🧾 UIIC Claim XML Upload Tool")
st.write("Convert Excel files to SOAP-compatible XML and upload to UIIC Portal.")

# ------------------------------
# Upload Excel File
# ------------------------------
uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])
if uploaded_file:
    st.success("✅ File uploaded successfully!")
    #st.rerun()  # optional if you want rerun
    time.sleep(0.5)  # wait 2 seconds

    # Show progress bar during conversion
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)
    st.info("Processing your Excel file...")
    time.sleep(2) 
    
    try:
        df = pd.read_excel(uploaded_file)
        st.write("### Preview of Uploaded Data:")
        st.dataframe(df.head())
        # ------------------------------

        # 2. Save encrypted copy
        os.makedirs("encrypted_uploads", exist_ok=True)
        encrypted_data = encrypt_file(uploaded_file.getvalue())
        encrypted_file_path = f"encrypted_uploads/{uploaded_file.name}.enc"
        with open(encrypted_file_path, "wb") as ef:
            ef.write(encrypted_data)


        # 3. Log entry with IP (only once per upload)
        if not st.session_state.get("logged", False):
         ip = socket.gethostbyname(socket.gethostname())
         log_upload(uploaded_file.name, ip)
         st.session_state.logged = True  # mark as logged


        #st.info(f"Encrypted backup stored ✅\nLog entry created ✅")

        # Convert to XML
        with st.spinner("🔄 Converting Excel to SOAP XML..."):
            xml_data = convert_excel_to_xml(df)
            
        # DEBUG: Check if data conversion failed silently
        if not xml_data or len(xml_data) < 50:
             raise ValueError("XML conversion failed or resulted in empty data. Check Excel data and 'excel_to_xml.py'.")
        progress.progress(100)
        st.success("✅ File successfully converted to XML!")
        # Store in session
        st.session_state.converted_xml = xml_data
        # Show next action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Convert to SOAP XML Again"):
                st.session_state.converted_xml = convert_excel_to_xml(df)
                st.success("✅ Re-converted successfully!")
        with col2:
            if st.button("👁️ View Converted XML"):
                st.session_state.show_xml = True
                st.rerun()
    except Exception as e:
        # This will now catch silent failures from convert_excel_to_xml
        st.error(f"❌ Error processing Excel file: {e}")
# ------------------------------
# View XML Section
# ------------------------------
if st.session_state.get("show_xml", False) and "converted_xml" in st.session_state:
    st.subheader("🧾 Converted SOAP XML Preview")
    try:
        # Pretty Print XML
        xml_pretty = xml.dom.minidom.parseString(st.session_state.converted_xml)
        # Note: I standardized indent to two spaces for consistency
        formatted_xml = xml_pretty.toprettyxml(indent="  ") 
    except Exception:
        formatted_xml = st.session_state.converted_xml
    # Show scrollable XML viewer
    st.text_area(
        "Converted XML",
        value=formatted_xml,
        height=500,
        key="xml_view",
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        # Correcting file save path to the Streamlit download button style
        st.download_button(
            label="💾 Download XML File",
            data=st.session_state.converted_xml,
            file_name="converted_claim_data.xml",
            mime="text/xml"
        )

    with col2:
        if st.button("❌ Close View"):
            st.session_state.show_xml = False
            st.rerun()
# ------------------------------
#  Upload to UIIC Portal
# ------------------------------
# Check if XML exists AND is not currently showing the XML preview
if "converted_xml" in st.session_state and st.session_state.converted_xml and not st.session_state.get("show_xml", False):
    st.markdown("---")
    st.subheader("🚀 Upload Converted XML to UIIC Portal")
    # This print statement confirms that XML data is present before sending
    print(f"DEBUG: XML Length ready to send: {len(st.session_state.converted_xml)} bytes")

    if st.button("📤 Upload to UIIC Portal"):
        # The data being sent is now guaranteed to be non-empty due to checks above
        with st.spinner("Connecting to UIIC WebService..."):
            response_text, status_code = send_to_uiic(st.session_state.converted_xml)
        if status_code == 200:
            st.success("✅ Uploaded successfully to UIIC portal!")
            # We must show the raw response including the embedded XML response
            st.text_area("Server Response (Status 200 - Check XML):", response_text, height=300)
        else:
            st.error(f"❌ Upload failed with status {status_code}")
            st.text_area("Error Response:", response_text, height=300)
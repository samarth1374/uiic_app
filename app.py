from cryptography.fernet import Fernet
from datetime import datetime
import streamlit as st
import pandas as pd
import time
import xml.dom.minidom
from io import BytesIO
from soap_client import send_to_uiic
from excel_to_xml import convert_excel_to_xml
import socket
import os
import csv
import pytz
import html
import re
import xml.etree.ElementTree as ET
from streamlit.components.v1 import html as st_html

# ============================================================
# Load Encryption Key
# ============================================================

def load_key(path="fernet_key.key"):
    with open(path, "rb") as f:
        return f.read()

KEY = load_key()
fernet = Fernet(KEY)

def encrypt_file(file_bytes):
    return fernet.encrypt(file_bytes)

# ============================================================
# Convert UIIC XML RESPONSE → DataFrame
# ============================================================

def parse_uiic_response_to_df(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except:
        return pd.DataFrame()

    data = []
    for rec in root.findall(".//RECORD"):
        row = {child.tag: child.text for child in rec}
        data.append(row)
    return pd.DataFrame(data)

# ============================================================
# Logging
# ============================================================

LOG_FILE = "logs.csv"

def log_upload(filename, ip):
    ist = pytz.timezone("Asia/Kolkata")
    ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    header = ["filename", "timestamp_ist", "client_ip"]

    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([filename, ts, ip])

# ============================================================
# Streamlit Page Setup
# ============================================================

st.set_page_config(
    page_title="HITPA UIIC CLAIM UPLOAD WEB SERVICE",
    page_icon="🏥",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
html, body { font-family: 'Segoe UI', sans-serif; }
.navbar {
    background: linear-gradient(135deg, #003a7c, #0059c8);
    padding: 18px 30px;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    border: 1px solid rgba(0,150,255,0.55);
}
.nav-title {
    color: white;
    font-size: 23px;
    font-weight: 700;
    text-shadow: 0 0 5px rgba(0,150,255,0.5);
}
.stButton>button {
    background: linear-gradient(135deg, #0066ff, #003a99);
    color: white;
    padding: 12px 25px;
    border-radius: 12px;
    border: none;
    font-size: 16px;
    font-weight: 600;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}
.stButton>button:hover {
    background: linear-gradient(135deg, #1a7bff, #004ecc);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Navbar
# ============================================================

st.markdown("""
<div class="navbar">
    <span class="nav-title">🏥 HITPA UIIC CLAIM UPLOAD WEB SERVICE</span>
</div>
""", unsafe_allow_html=True)

# Navigation State
if "page" not in st.session_state:
    st.session_state.page = "upload"

st.sidebar.title("📊 Dashboard Menu")
if st.sidebar.button("📊 View Upload Logs"):
    st.session_state.page = "logs"

# ============================================================
# PAGE 1: UPLOAD PAGE
# ============================================================

if st.session_state.page == "upload":

    st.title("📤 Claim XML Upload Panel")

    # Step 1: Service
    st.subheader("1️⃣ Select Service Type")
    service = st.selectbox(
        "Choose Service:",
        ["-- Select Service --", "Intimation", "Sattlement", "Modification", "Repudiation", "Reopen"]
    )

    if service == "-- Select Service --":
        st.warning("⚠ Please select a service to continue.")
        st.stop()

    st.toast(f"Selected Service: {service}", icon="✅")

    # Step 2: Upload Excel
    st.subheader("2️⃣ Upload Excel File")
    uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

    if uploaded_file:
        st.toast("File uploaded successfully! 📁", icon="✅")

        progress = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress.progress(i + 1)

        try:
            df = pd.read_excel(uploaded_file)
            st.write("### 👀 Preview of Uploaded Data")
            st.dataframe(df, use_container_width=True)

            os.makedirs("encrypted_uploads", exist_ok=True)
            encrypted_data = encrypt_file(uploaded_file.getvalue())
            with open(f"encrypted_uploads/{uploaded_file.name}.enc", "wb") as ef:
                ef.write(encrypted_data)

            if not st.session_state.get("logged", False):
                try:
                    ip = socket.gethostbyname(socket.gethostname())
                except:
                    ip = "Unknown"
                log_upload(uploaded_file.name, ip)
                st.session_state.logged = True

            with st.spinner("🔄 Converting Excel to XML..."):
                xml_data = convert_excel_to_xml(df)

            if not xml_data or len(xml_data) < 50:
                raise ValueError("XML conversion failed!")

            st.session_state.converted_xml = xml_data
            st.toast("✅ XML Conversion Successful!", icon="✅")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔁 Re-Generate XML"):
                    st.session_state.converted_xml = convert_excel_to_xml(df)
                    st.toast("Re-converted XML!", icon="🔄")

            with col2:
                if st.button("👁️ Preview Converted XML"):
                    st.session_state.show_xml = True
                    st.rerun()

        except Exception as e:
            st.toast(f"❌ Error: {e}", icon="⚠️")

    # Step 3: XML Viewer
    if st.session_state.get("show_xml") and st.session_state.get("converted_xml"):

        st.subheader("🧾 XML Preview")
        try:
            xml_pretty = xml.dom.minidom.parseString(st.session_state.converted_xml)
            formatted_xml = xml_pretty.toprettyxml(indent="  ")
        except:
            formatted_xml = st.session_state.converted_xml

        st.text_area("Converted XML", formatted_xml, height=500)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="💾 Download XML",
                data=st.session_state.converted_xml,
                file_name="converted_claim.xml",
                mime="text/xml"
            )
        with col2:
            if st.button("❌ Close XML Viewer"):
                st.session_state.show_xml = False
                st.rerun()

    # Step 4: Send XML to UIIC
    if st.session_state.get("converted_xml") and not st.session_state.get("show_xml"):

        st.subheader("🚀 Upload Converted XML to UIIC Portal")

        if st.button("📤 Upload To UIIC Portal"):
            with st.spinner("Connecting to UIIC WebService..."):
                response_text, status_code = send_to_uiic(
                    st.session_state.converted_xml,
                    service_type=service
                )
                st.session_state.uiic_response_text = response_text
                st.session_state.uiic_status_code = status_code
                st.session_state.converted_uiic_response = None

        if st.session_state.get("uiic_response_text"):

            response_text = st.session_state.uiic_response_text
            status_code = st.session_state.uiic_status_code

            if status_code == 200:
                st.success("✅ Uploaded successfully to UIIC portal!")
                st.text_area("UIIC Raw Response", response_text, height=300)

                # ----------- FIXED BLOCK START ------------
                if st.button("🛠 Convert UIIC Response XML to Human-Readable Format"):
                    try:
                        root = ET.fromstring(response_text)
                        ns = {
                            "s": "http://schemas.xmlsoap.org/soap/envelope/",
                            "temp": "http://tempuri.org/"
                        }

                        possible_tags = [
                            "ClaimIntimationResult",
                            "ClaimSattlementResult",
                            "ClaimModificationResult",
                            "ClaimRepudiationResult",
                            "ClaimReopenResult",
                        ]

                        inner_xml_escaped = None

                        for tag in possible_tags:
                            found = root.find(f".//temp:{tag}", ns)
                            if found is not None:
                                inner_xml_escaped = found.text
                                break

                        if inner_xml_escaped is None:
                            raise Exception("UIIC Response Tag Not Found in SOAP Response")

                        inner_xml = html.unescape(inner_xml_escaped).strip()
                        #inner_xml = re.sub(r"^<\?xml.*?\?>", "", inner_xml).strip()
                        # Fix possible mismatched quotes in XML declaration
                        # Remove XML header
                        inner_xml = re.sub(r'<\?xml.*?\?>', '', inner_xml).strip()

# Replace escaped quotes
                        inner_xml = inner_xml.replace('\\"', '"')

# **Clean problematic HTML tags**
                        inner_xml = re.sub(r'<BR\s*/?>', '\n', inner_xml, flags=re.IGNORECASE)  # <BR> → newline
                        inner_xml = re.sub(r'</?B>', '', inner_xml, flags=re.IGNORECASE)         # remove <B> tags

# Now safe to parse
                        pretty_xml = xml.dom.minidom.parseString(inner_xml).toprettyxml(indent="  ")


                        st.session_state.converted_uiic_response = pretty_xml

                    except Exception as e:
                        st.error(f"❌ Failed to parse UIIC response: {e}")
                # ----------- FIXED BLOCK END --------------

                if st.session_state.get("converted_uiic_response"):
                    st.subheader("📝 Human-Readable UIIC Response")
                    st.text_area(
                        "Converted UIIC Response",
                        st.session_state.converted_uiic_response,
                        height=400,
                    )

            else:
                st.error(f"❌ Upload Failed (Status: {status_code})")
                st.text_area("Error Response:", response_text, height=250)

    # Step 5: Download UIIC Response as Excel
    st.subheader("📥 Download UIIC Response as Excel")

    if st.session_state.get("converted_uiic_response"):
        try:
            df_response = parse_uiic_response_to_df(
                st.session_state.converted_uiic_response
            )

            excel_output = BytesIO()
            df_response.to_excel(excel_output, index=False)
            excel_bytes = excel_output.getvalue()

            st.download_button(
                label="📊 Download UIIC Excel Response",
                data=excel_bytes,
                file_name="uiic_response.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            history_file = "response_history.xlsx"

            if os.path.exists(history_file):
                old_df = pd.read_excel(history_file)
                final_df = pd.concat([old_df, df_response], ignore_index=True)
            else:
                final_df = df_response

            final_df.to_excel(history_file, index=False)
            st.success("📁 Response saved in history!")

        except Exception as e:
            st.error(f"Failed generating Excel: {e}")

# ============================================================
# PAGE 2: LOGS
# ============================================================

elif st.session_state.page == "logs":

    st.title("📋 Upload History Logs")

    if os.path.exists(LOG_FILE):
        logs_df = pd.read_csv(LOG_FILE)
        logs_df = logs_df.sort_values(by="timestamp_ist", ascending=False)
        st.success(f"Total Uploads: {len(logs_df)}")
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("No logs found.")

    if st.button("⬅ Back to Upload Panel"):
        st.session_state.page = "upload"
        st.rerun()


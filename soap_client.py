import requests
import streamlit as st
from xml.dom import minidom


def send_to_uiic(xml_data: str, user_id: str = "HEA00", password: str = "Tcs@1010"):
    """
    Sends SOAP request to UIIC ClaimIntimation endpoint (UAT/Production).

    Args:
        xml_data (str): XML payload (the <INPUT>...</INPUT> content)
        user_id (str): UIIC User ID
        password (str): UIIC Password

    Returns:
        tuple: (response_text, status_code)
    """

    # --- SAFETY FIX: Ensure CDATA content doesn’t break if user XML contains "]]>" ---
    xml_safe = xml_data.replace("]]>", "]]]]><![CDATA[>")

    # --- UIIC SOAP Endpoint (Change for PROD if required) ---
    url = "https://training.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc"

    # --- BUILD FULL SOAP ENVELOPE (EXACTLY AS UIIC expects) ---
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:ClaimIntimation>
         <tem:v_sInputXML><![CDATA[{xml_safe}]]></tem:v_sInputXML>
         <tem:v_sUserId>{user_id}</tem:v_sUserId>
         <tem:v_sPassword>{password}</tem:v_sPassword>
      </tem:ClaimIntimation>
   </soapenv:Body>
</soapenv:Envelope>"""

    # --- SOAP HEADERS ---
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/IClaimIntimation/ClaimIntimation"
    }

    try:
        # --- MAKE THE SOAP REQUEST ---
        response = requests.post(
            url,
            data=soap_body.encode("utf-8"),
            headers=headers,
            timeout=90,
            verify=False  # ❗ Only disable in UAT; enable in PROD with valid certs
        )

        # --- PRETTY PRINT XML RESPONSE (for UI display) ---
        try:
            parsed = minidom.parseString(response.text)
            pretty_xml = parsed.toprettyxml(indent="   ")
        except Exception:
            pretty_xml = response.text  # fallback if invalid XML

        # --- Streamlit display ---
        st.subheader("🧾 SOAP Request Sent")
        st.code(soap_body, language="xml")

        st.subheader("📩 UIIC SOAP Response")
        st.code(pretty_xml, language="xml")

        # --- Print to console/log ---
        print(f"✅ Status Code: {response.status_code}")
        print("Response XML:", pretty_xml)

        return response.text, response.status_code

    except requests.exceptions.RequestException as e:
        error_msg = f"❌ SOAP Request failed: {str(e)}"
        st.error(error_msg)
        print(error_msg)
        return error_msg, 500

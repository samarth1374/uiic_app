# import requests
# import streamlit as st
# from xml.dom import minidom

# def send_to_uiic(xml_data: str, user_id: str = "Healim00", password: str = "Hitpa@2026"):
#     """
#     Sends SOAP request to UIIC AccountsInsertRecords endpoint (Production).
#     """

#     # Safety fix for CDATA content
#     xml_safe = xml_data.replace("]]>", "]]]]><![CDATA[>")

#     # Production URL
#     url = "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc"

#     # Correct SOAP Envelope for Production
#     soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
# <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
#    <soapenv:Header/>
#    <soapenv:Body>
#       <tem:ClaimIntimation>
#          <tem:v_sInputXML><![CDATA[{xml_safe}]]></tem:v_sInputXML>
#          <tem:v_sUserId>{user_id}</tem:v_sUserId>
#          <tem:v_sPassword>{password}</tem:v_sPassword>
#       </tem:ClaimIntimation>
#    </soapenv:Body>
# </soapenv:Envelope>"""

#     headers = {
#         "Content-Type": "text/xml; charset=utf-8",
#         "SOAPAction": "http://tempuri.org/IClaimIntimation/ClaimIntimation"
#     }

#     try:
#         response = requests.post(
#             url,
#             data=soap_body.encode("utf-8"),
#             headers=headers,
#             timeout=90,
#             verify=True   # keep False only for testing
#         )

#         try:
#             parsed = minidom.parseString(response.text)
#             pretty_xml = parsed.toprettyxml(indent="   ")
#         except Exception:
#             pretty_xml = response.text

#         st.subheader("🧾 SOAP Request Sent")
#         st.code(soap_body, language="xml")

#         st.subheader("📩 UIIC SOAP Response")
#         st.code(pretty_xml, language="xml")

#         print(f"✅ Status Code: {response.status_code}")
#         print("Response XML:", pretty_xml)

#         return response.text, response.status_code

#     except requests.exceptions.RequestException as e:
#         error_msg = f"❌ SOAP Request failed: {str(e)}"
#         st.error(error_msg)
#         print(error_msg)
#         return error_msg, 500

import requests
import streamlit as st
from xml.dom import minidom


# ======================================================
# Mapping for Each UIIC Service
# ======================================================
SERVICE_MAP = {
    "Intimation": {
        "url": "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc",
        "method": "ClaimIntimation",
        "soap_action": "http://tempuri.org/IClaimIntimation/ClaimIntimation"
    },
    "Sattlement": {
        "url": "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc",
        "method": "ClaimSattlement",
        "soap_action": "http://tempuri.org/IClaimIntimation/ClaimSattlement"
    },
    "Modification": {
        "url": "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc",
        "method": "ClaimProvisionModification",
        "soap_action": "http://tempuri.org/IClaimIntimation/ClaimProvisionModification"
    },
    "Repudiation": {
        "url": "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc",
        "method": "ClaimRepudiation",
        "soap_action": "http://tempuri.org/IClaimRepudiation/ClaimRepudiation"
    },
    "Reopen": {
        "url": "https://slportal.uiic.in/Claim_Intimation_WebService/ClaimIntimation.svc",
        "method": "ClaimReopen",
        "soap_action": "http://tempuri.org/IClaimIntimation/ClaimReOpen"
    }
}



# ======================================================
# Dynamic SOAP Function
# ======================================================
def send_to_uiic(xml_data: str, service_type: str, user_id: str = "Healim00", password: str = "Hitpa@2026"):
    """
    Sends SOAP request dynamically based on selected service type.
    """

    if service_type not in SERVICE_MAP:
        return f"❌ Invalid service: {service_type}", 400

    service = SERVICE_MAP[service_type]

    url = service["url"]
    method = service["method"]
    soap_action = service["soap_action"]

    # Fix CDATA end tags inside XML
    xml_safe = xml_data.replace("]]>", "]]]]><![CDATA[>")

    # Build SOAP Envelope Dynamically
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:{method}>
         <tem:v_sInputXML><![CDATA[{xml_safe}]]></tem:v_sInputXML>
         <tem:v_sUserId>{user_id}</tem:v_sUserId>
         <tem:v_sPassword>{password}</tem:v_sPassword>
      </tem:{method}>
   </soapenv:Body>
</soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": soap_action
    }

    try:
        response = requests.post(
            url,
            data=soap_body.encode("utf-8"),
            headers=headers,
            timeout=90,
            verify=True
        )

        try:
            parsed = minidom.parseString(response.text)
            pretty_xml = parsed.toprettyxml(indent="   ")
        except:
            pretty_xml = response.text

        # Show request + response on UI
        st.subheader("📤 SOAP Request Sent")
        st.code(soap_body, language="xml")

        st.subheader("📩 UIIC SOAP Response")
        st.code(pretty_xml, language="xml")

        return response.text, response.status_code

    except requests.exceptions.RequestException as e:
        return f"❌ SOAP Request failed: {str(e)}", 500

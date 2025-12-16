import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
import re


def convert_excel_to_xml(df: pd.DataFrame) -> str:
    """
    Converts Excel DataFrame to UIIC-compatible XML structure.
    Includes stricter cleaning to prevent "Input String is Not Proper" errors.
    """

    root = Element("INPUT")

    def format_date(val, with_time=False):
        if pd.isna(val) or str(val).strip() == "":
            return ""

        try:
            if isinstance(val, (int, float)):
                dt = pd.to_datetime(val, unit="D", origin="1899-12-30")
            else:
                dt = pd.to_datetime(val, dayfirst=True)

            if with_time:
                return dt.strftime("%d/%m/%Y %H:%M")
            return dt.strftime("%d/%m/%Y")

        except Exception:
            return str(val)

    if df.empty:
        print("DEBUG: DataFrame is empty. Returning empty XML.")
        return "<INPUT></INPUT>"

    for _, row in df.iterrows():
        record = SubElement(root, "RECORD")

        for col in df.columns:
            tag_name = str(col).strip().replace(" ", "_").upper()

            value = "" if pd.isna(row[col]) else str(row[col]).strip()

            # Fix 1: Numeric cleanup (except IFSC)
            if tag_name.startswith("NUM_") and tag_name not in ["NUM_IFSC_CODE"]:
                if "e" in value.lower():
                    try:
                        value = "{:.0f}".format(float(value))
                    except Exception:
                        pass

                value = re.sub(r"[^\d.]", "", value)

            # Fix 2: Date formatting
            if tag_name.startswith("DAT_"):
                with_time = any(
                    x in tag_name
                    for x in ["INTIMATION", "PREAUTH", "DISCHARGE"]
                )
                value = format_date(row[col], with_time)

            # Fix 3: Clean special characters from text fields
            if tag_name in [
                "TXT_DIAGNOSIS_CODE_LEVEL1",
                "TXT_NAME_OF_HOSPITAL_CLINIC",
                "TXT_ADDRESS_OF_HOSPITAL_CLINIC",
            ]:
                value = re.sub(r"[^\w\s\.,]", "", value).strip()

            SubElement(record, tag_name).text = value

    xml_data = tostring(root, encoding="utf-8").decode("utf-8")
    return xml_data

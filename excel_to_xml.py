import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
import re
def convert_excel_to_xml(df: pd.DataFrame) -> str:
    """
    Converts Excel DataFrame to UIIC-compatible XML structure.
    
    This version includes stricter cleaning for potential problematic
    text fields to prevent "Input String is Not Proper" errors.
    """
    root = Element("INPUT")
    def format_date(val, with_time=False):
        if pd.isna(val) or str(val).strip() == "":
            return ""
        
        try:
            if isinstance(val, (int, float)):
                 dt = pd.to_datetime(val, unit='D', origin='1899-12-30')
            else:
                 dt = pd.to_datetime(val)
                 
            if with_time:
                # Format: DD/MM/YYYY HH:MM
                return dt.strftime("%d/%m/%Y %H:%M") 
            # Format: DD/MM/YYYY
            return dt.strftime("%d/%m/%Y") 
        except Exception:
            # Fallback: if parsing fails, return the original string value
            return str(val)
    if df.empty:
        print("DEBUG: DataFrame is empty. Returning empty XML.")
        return "<INPUT></INPUT>"
    for _, row in df.iterrows():
        record = SubElement(root, "RECORD")
        for col in df.columns:
            tag_name = str(col).strip().replace(" ", "_").upper()
            
            value = str(row[col]) if not pd.isna(row[col]) else ""
            value = value.strip()
            # Fix 1: Prevent scientific notation in codes/numbers
            if "CODE" in tag_name.upper() or "NUMBER" in tag_name.upper() or tag_name.startswith("NUM_"):
                if "e" in value.lower():
                    try:
                        value = '{:.0f}'.format(float(value))
                    except:
                        pass
                
                # Further clean non-digit characters from NUM_ fields
                if tag_name.startswith("NUM_"):
                     value = re.sub(r'[^\d.]', '', value)
                     
            # Fix 2: Stricter Date formatting
            if tag_name.startswith("DAT_"):
                date_val = row[col] 
                with_time = any(x in tag_name for x in ["INTIMATION", "PREAUTH", "DISCHARGE"])
                value = format_date(date_val, with_time)
            # Fix 3 (NEW): Clean special characters from specific text fields (e.g., diagnosis)
            # This targets fields that might have hyphens or special spacing that UIIC rejects
            if tag_name in ["TXT_DIAGNOSIS_CODE_LEVEL1", "TXT_NAME_OF_HOSPITAL_CLINIC", "TXT_ADDRESS_OF_HOSPITAL_CLINIC"]:
                 # Keep only alphanumeric characters, spaces, and standard punctuation (dots/commas)
                 value = re.sub(r'[^\w\s\.\,]', '', value)
                 value = value.strip()

            SubElement(record, tag_name).text = value
    xml_data = tostring(root, encoding="utf-8").decode("utf-8")
    return xml_data

import re
from datetime import datetime
import cv2
import numpy as np
from PIL import Image

# Verhoeff Algorithm Tables

verhoeff_table_d = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0]
]

verhoeff_table_p = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8]
]

def validate_verhoeff(number: str) -> bool:
    """Check if the 12-digit Aadhaar number is valid using Verhoeff algorithm."""
    c = 0
    num = number[::-1]
    for i, item in enumerate(num):
        c = verhoeff_table_d[c][verhoeff_table_p[i % 8][int(item)]]
    return c == 0

# Regex Patterns for PII

aadhaar_pattern = re.compile(r'\b(?:\d[ -]?){4}(?:\d[ -]?){4}(?:\d[ -]?){4}\b')
pan_pattern = re.compile(r'\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b')
email_pattern = re.compile(r'\b\S+@\S+\.\S+\b')
mobile_pattern = re.compile(r'(\+91[-\s]?|0)?[6-9]\d{9}\b')
vid_pattern = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
dl_pattern = re.compile(r'\b[A-Z]{2}[ -]?\d{2}[ -]?\d{4}[ -]?\d{7}\b')
dob_pattern = re.compile(r'\b(?:\d{2}[-/\s]?\d{2}[-/\s]?\d{4}|\d{4}[-/\s]?\d{2}[-/\s]?\d{2})\b')
short_date_pattern = re.compile(r'\b(0[1-9]|1[0-2])[/\-](\d{2})\b')


# Keywords for Name & Address
ADDRESS_KEYWORDS = [
     # English
    "address", "s/o", "d/o", "c/o", "w/o", "house", "road",
    "village", "dist", "taluka", "pin", "post", "pincode",
    "residence", "location", "street", "lane", "colony",
    "nagar", "city", "town", "district", "state", "country", "zip",

    # Hindi
    "पता", "गांव", "ग्राम", "पोस्ट", "जिला", "तालुका", "राज्य",
    "देश", "पिन", "पिनकोड", "नगर", "वार्ड", "कॉलोनी", "रोड",
    "सड़क", "गली", "स्थान", "लोकलिटी", "ठिकाना"
]
# NAME_KEYWORDS = ["name", "father", "mother", "guardian"]


def is_valid_date(date_str):
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d %m %Y", "%Y-%m-%d", "%Y/%m/%d", "%Y %m %d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if dt <= today:
                return True
            else:
                return False
        except ValueError:
            continue
    return False


def detect_pii_dob(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
    
    # DOB with validation
    for match in dob_pattern.findall(text):
        cleaned = re.sub(r'[-/\s]', '-', match)
        if is_valid_date(cleaned):
            matches.append("DOB")
            pii_values.append({"type": "DOB", "value": match})


    # Compact DOB format (ddmmyyyy)
    compact_dob = re.findall(r'\b\d{8}\b', text)
    for dob in compact_dob:
        try:
            datetime.strptime(dob, "%d%m%Y")
            matches.append("DOB")
            pii_values.append({"type": "DOB", "value": dob})
        except ValueError:
            continue
        
    # Short date detection (MM/YY or MM/DD)
    for match in short_date_pattern.findall(text):
        month_str, part2_str = match
        month = int(month_str)
        part2 = int(part2_str)
        if 1 <= month <= 12:
            # Part2 can be day (<=31) or year (any 2-digit usually)
            if part2 <= 31:
                matches.append("SHORT_DATE")
                pii_values.append({"type": "SHORT_DATE", "value": f"{month:02d}/{part2:02d}"})
        
    return {
        "matches": matches,
        "contains_pii_dob": bool(matches),
        "pii_details": pii_values
    }
    
def detect_pii_address(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
    
    # Address
    if any(kw in lower_text for kw in ADDRESS_KEYWORDS):
        matches.append("ADDRESS")
        pii_values.append({"type": "ADDRESS", "value": "Found by keyword"})
        
    # Pincode
    pin_match = re.search(r"\b[1-9][0-9]{5}\b", text)
    if pin_match:
        matches.append("ADDRESS_PINCODE")
        pii_values.append({"type": "ADDRESS", "value": f"PIN Code: {pin_match.group()}"})
        
    return {
        "matches": matches,
        "contains_pii_address": bool(matches),
        "pii_details": pii_values
    }
    

def detect_pii(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
                
    # Aadhaar detection with Verhoeff check
    for match in aadhaar_pattern.findall(text):
        digits = re.sub(r'\D', '', match)
        if len(digits) == 12 and validate_verhoeff(digits):
            matches.append("AADHAAR")
            pii_values.append({"type": "AADHAAR", "value": match})

    # PAN
    for match in pan_pattern.findall(text):
        matches.append("PAN")
        pii_values.append({"type": "PAN", "value": match})

    # Email
    for match in email_pattern.findall(text):
        matches.append("EMAIL")
        pii_values.append({"type": "EMAIL", "value": match})

    # Mobile
    for match in mobile_pattern.findall(text):
        matches.append("MOBILE")
        pii_values.append({"type": "MOBILE", "value": match})

    # VID
    for match in vid_pattern.findall(text):
        matches.append("VID")
        pii_values.append({"type": "VID", "value": match})

    # DL
    for match in dl_pattern.findall(text):
        matches.append("DRIVING_LICENSE")
        pii_values.append({"type": "DRIVING_LICENSE", "value": match})
        
    return {
        "matches": matches,
        "contains_pii": bool(matches),
        "pii_details": pii_values
    }

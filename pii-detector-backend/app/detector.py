import re
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
from .verhoeff_algorithm import validate_verhoeff

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

SIGNATURE_KEYWORDS = [
    "signature", "signed", "signatory", "authorised signatory", "sig."
]

def detect_signature_keywords(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    for kw in SIGNATURE_KEYWORDS:
        if kw in lower_text:
            matches.append("SIGNATURE_KEYWORD")
            pii_values.append({"type": "SIGNATURE", "value": kw})

    return {
        "matches": matches,
        "contains_signature_keyword": bool(matches),
        "pii_details": pii_values
    }
    
def detect_aadhar_card_no(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # Aadhaar detection with Verhoeff check
    for match in aadhaar_pattern.findall(text):
        digits = re.sub(r'\D', '', match)
        if len(digits) == 12 and validate_verhoeff(digits):
            matches.append("AADHAAR")
            pii_values.append({"type": "AADHAAR", "value": match})

    return {
        "matches": matches,
        "contains_aadhar_card_no": bool(matches),
        "aadhar_card_no_details": pii_values
    }
    
def detect_driving_licence_no(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # DL
    for match in dl_pattern.findall(text):
        matches.append("DRIVING_LICENSE")
        pii_values.append({"type": "DRIVING_LICENSE", "value": match})

    return {
        "matches": matches,
        "contains_driving_licence_no": bool(matches),
        "driving_licence_no_details": pii_values
    }


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


# def detect_pii_dob(text: str) -> dict:
#     matches = []
#     pii_values = []
#     lower_text = text.lower()
    
#     # DOB with validation
#     for match in dob_pattern.findall(text):
#         cleaned = re.sub(r'[-/\s]', '-', match)
#         if is_valid_date(cleaned):
#             matches.append("DOB")
#             pii_values.append({"type": "DOB", "value": match})


#     # Compact DOB format (ddmmyyyy)
#     compact_dob = re.findall(r'\b\d{8}\b', text)
#     for dob in compact_dob:
#         try:
#             datetime.strptime(dob, "%d%m%Y")
#             matches.append("DOB")
#             pii_values.append({"type": "DOB", "value": dob})
#         except ValueError:
#             continue
        
#     # Short date detection (MM/YY or MM/DD)
#     for match in short_date_pattern.findall(text):
#         month_str, part2_str = match
#         month = int(month_str)
#         part2 = int(part2_str)
#         if 1 <= month <= 12:
#             # Part2 can be day (<=31) or year (any 2-digit usually)
#             if part2 <= 31:
#                 matches.append("SHORT_DATE")
#                 pii_values.append({"type": "SHORT_DATE", "value": f"{month:02d}/{part2:02d}"})
        
#     return {
#         "matches": matches,
#         "contains_pii_dob": bool(matches),
#         "pii_details": pii_values
#     }

def detect_pii_dob(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
    
    # Full DOB formats
    for match in dob_pattern.findall(text):
        cleaned = re.sub(r'[-/\s]', '-', match)
        if is_valid_date(cleaned):
            try:
                # Try parsing date
                dt = None
                for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d %m %Y", "%Y-%m-%d", "%Y/%m/%d", "%Y %m %d"):
                    try:
                        dt = datetime.strptime(cleaned, fmt)
                        break
                    except ValueError:
                        continue

                if dt:
                    matches.append("DOB")
                    pii_values.append({
                        "type": "DOB",
                        "value": match,
                        "day": dt.day,
                        "month": dt.month,
                        "year": dt.year
                    })
            except ValueError:
                continue

    # Compact DOB format (ddmmyyyy)
    compact_dob = re.findall(r'\b\d{8}\b', text)
    for dob in compact_dob:
        try:
            dt = datetime.strptime(dob, "%d%m%Y")
            matches.append("DOB")
            pii_values.append({
                "type": "DOB",
                "value": dob,
                "day": dt.day,
                "month": dt.month,
                "year": dt.year
            })
        except ValueError:
            continue
        
    # Short date detection (MM/YY or MM/DD) → treat only as month+day
    for match in short_date_pattern.findall(text):
        month_str, part2_str = match
        month = int(month_str)
        part2 = int(part2_str)
        if 1 <= month <= 12 and part2 <= 31:
            matches.append("SHORT_DATE")
            pii_values.append({
                "type": "SHORT_DATE",
                "value": f"{month:02d}/{part2:02d}",
                "day": part2,
                "month": month,
                "year": None
            })
        
    return {
        "matches": matches,
        "contains_pii_dob": bool(matches),
        "dob_details": pii_values
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
        "address_details": pii_values
    }
    

def detect_pii(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

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
        
    return {
        "matches": matches,
        "contains_pii": bool(matches),
        "pii_details": pii_values
    }

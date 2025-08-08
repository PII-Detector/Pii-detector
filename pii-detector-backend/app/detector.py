import re

# ----------------------------
# Verhoeff Algorithm Tables
# ----------------------------

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

# ----------------------------
# Regex Patterns for PII
# ----------------------------
aadhaar_pattern = re.compile(r'\b(?:\d[ -]?){4}(?:\d[ -]?){4}(?:\d[ -]?){4}\b')
pan_pattern = re.compile(r'\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b')
email_pattern = re.compile(r'\b\S+@\S+\.\S+\b')
mobile_pattern = re.compile(r'(\+91[-\s]?|0)?[6-9]\d{9}\b')
vid_pattern = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
dl_pattern = re.compile(r'\b[A-Z]{2}[ -]?\d{2}[ -]?\d{4}[ -]?\d{7}\b')
dob_pattern = re.compile(r'\b(?:\d{2}[-/\s]?\d{2}[-/\s]?\d{4}|\d{4}[-/\s]?\d{2}[-/\s]?\d{2})\b'
)

# Keywords for Name & Address
ADDRESS_KEYWORDS = [
    "address", "s/o", "d/o", "c/o", "w/o", "house", "road",
    "village", "dist", "taluka", "pin", "post", "pincode"
]
NAME_KEYWORDS = ["name", "father", "mother", "guardian"]

# ----------------------------
# Main Detection Function
# ----------------------------
# def detect_pii(text: str) -> dict:
#     matches = []
#     lower_text = text.lower()

#     # Aadhaar detection with Verhoeff check
#     for match in aadhaar_pattern.findall(text):
#         digits = re.sub(r'\D', '', match)
#         if len(digits) == 12 and validate_verhoeff(digits):
#             matches.append("AADHAAR")

#     # Other patterns
#     if pan_pattern.search(text):
#         matches.append("PAN")
#     if email_pattern.search(text):
#         matches.append("EMAIL")
#     if mobile_pattern.search(text):
#         matches.append("MOBILE")
#     if vid_pattern.search(text):
#         matches.append("VID")
#     if dl_pattern.search(text):
#         matches.append("DRIVING_LICENSE")
#     if dob_pattern.search(text):
#      matches.append("DOB")

#     compact_dob = re.findall(r'\b\d{8}\b', text)
#     for dob in compact_dob:
#         if (
#         1 <= int(dob[0:2]) <= 31 and
#         1 <= int(dob[2:4]) <= 12 and
#         1900 <= int(dob[4:]) <= 2100
#         ):
#             matches.append("DOB")
#     if any(kw in lower_text for kw in ADDRESS_KEYWORDS):
#         matches.append("ADDRESS")
#     if any(kw in lower_text for kw in NAME_KEYWORDS):
#         matches.append("NAME")

#     return {
#         "matches": matches,
#         "contains_pii": bool(matches)
#     }

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

    # DOB
    for match in dob_pattern.findall(text):
        matches.append("DOB")
        pii_values.append({"type": "DOB", "value": match})

    # Compact DOB format (ddmmyyyy)
    compact_dob = re.findall(r'\b\d{8}\b', text)
    for dob in compact_dob:
        if (
            1 <= int(dob[0:2]) <= 31 and
            1 <= int(dob[2:4]) <= 12 and
            1900 <= int(dob[4:]) <= 2100
        ):
            matches.append("DOB")
            pii_values.append({"type": "DOB", "value": dob})

    # Address
    if any(kw in lower_text for kw in ADDRESS_KEYWORDS):
        matches.append("ADDRESS")
        pii_values.append({"type": "ADDRESS", "value": "Found by keyword"})

    # Name
    if any(kw in lower_text for kw in NAME_KEYWORDS):
        matches.append("NAME")
        pii_values.append({"type": "NAME", "value": "Found by keyword"})

    return {
        "matches": matches,
        "contains_pii": bool(matches),
        "pii_details": pii_values
    }

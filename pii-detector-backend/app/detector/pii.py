from app.utils.regex import pan_pattern, email_pattern, mobile_pattern, vid_pattern

def detect_pii(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    

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

def warnai_status(val):
    if "PAS / HABIS KUOTA" in val:
        return "background-color: #ff4d4d; color: white; font-weight: bold;"
    elif "KRITIS" in val:
        return "background-color: #fff2cc; color: #997a00; font-weight: bold;"
    elif "Aman" in val:
        return "background-color: #e6ffed; color: #006622;"
    return ""

def color_status(val):
    # Using background with transparency (alpha 0.2) for a softer, elegant look
    if "EXHAUSTED / NO QUOTA" in val:
        return "background-color: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: bold; border-left: 4px solid #ef4444;"
    elif "CRITICAL" in val:
        return "background-color: rgba(234, 179, 8, 0.2); color: #fde047; font-weight: bold; border-left: 4px solid #eab308;"
    elif "Safe" in val:
        return "background-color: rgba(16, 185, 129, 0.2); color: #6ee7b7; font-weight: bold; border-left: 4px solid #10b981;"
    return ""

def render_custom_table(df):
    # Table background color adjusted to dark theme (#1e293b)
    html = "<div style='overflow-x: auto;'><table style='width: 100%; border-collapse: collapse; background-color: #1e293b; color: #e2e8f0; font-family: sans-serif; font-size: 14px; border-radius: 8px; overflow: hidden; border: 1px solid #334155;'>"
    
    # Table Header
    html += "<tr style='background-color: #0f172a; color: #94a3b8; text-align: left;'>"
    for col in df.columns:
        html += f"<th style='padding: 12px 15px; border-bottom: 2px solid #334155;'>{col}</th>"
    html += "</tr>"
    
    # Table Body Rows
    for idx, row in df.iterrows():
        html += "<tr style='border-bottom: 1px solid #334155;'>"
        for col in df.columns:
            val = str(row[col])
            if col == "Status":
                style = color_status(val)
                html += f"<td style='padding: 10px 15px; {style}'>{val}</td>"
            else:
                html += f"<td style='padding: 10px 15px;'>{val}</td>"
        html += "</tr>"
        
    html += "</table></div>"
    return html
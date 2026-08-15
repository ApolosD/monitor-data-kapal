import pandas as pd

def warnai_status(val):
    # Menggunakan warna yang lebih soft / pastel gelap agar elegan di mata
    if "PAS / HABIS KUOTA" in val:
        return "background-color: rgba(239, 68, 68, 0.25); color: #fca5a5; font-weight: bold; border-left: 4px solid #ef4444;"
    elif "KRITIS" in val:
        return "background-color: rgba(234, 179, 8, 0.25); color: #fde047; font-weight: bold; border-left: 4px solid #eab308;"
    elif "Aman" in val:
        return "background-color: rgba(16, 185, 129, 0.25); color: #6ee7b7; font-weight: bold; border-left: 4px solid #10b981;"
    return ""

def render_custom_table(df):
    html = "<div style='overflow-x: auto;'><table style='width: 100%; border-collapse: collapse; background-color: #1e293b; color: #f8fafc; font-family: sans-serif; font-size: 14px; border-radius: 8px; overflow: hidden;'>"
    
    # Header Tabel
    html += "<tr style='background-color: #0f172a; color: #94a3b8; text-align: left; border-bottom: 2px solid #334155;'>"
    for col in df.columns:
        html += f"<th style='padding: 12px 15px;'>{col}</th>"
    html += "</tr>"
    
    # Isi Baris Tabel
    for idx, row in df.iterrows():
        html += "<tr style='border-bottom: 1px solid #334155;'>"
        for col in df.columns:
            val = str(row[col])
            if col == "Status":
                style = warnai_status(val)
                html += f"<td style='padding: 10px 15px; {style}'>{val}</td>"
            else:
                html += f"<td style='padding: 10px 15px; color: #e2e8f0;'>{val}</td>"
        html += "</tr>"
        
    html += "</table></div>"
    return html
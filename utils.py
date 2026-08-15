import pandas as pd

def warnai_status(val):
    if "PAS / HABIS KUOTA" in val:
        return "background-color: #ef4444; color: white; font-weight: bold;"
    elif "KRITIS" in val:
        return "background-color: #eab308; color: #1e1b4b; font-weight: bold;"
    elif "Aman" in val:
        return "background-color: #10b981; color: white; font-weight: bold;"
    return ""

def render_custom_table(df):
    """
    Merender tabel HTML kustom agar warnanya benar-benar menyatu dengan dark mode
    dan tidak berubah putih walau tema Streamlit diganti-ganti.
    """
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
            # Cek jika kolom status untuk memberikan warna latar belakang khusus
            if col == "Status":
                style = warnai_status(val)
                html += f"<td style='padding: 10px 15px; {style}'>{val}</td>"
            else:
                html += f"<td style='padding: 10px 15px; color: #e2e8f0;'>{val}</td>"
        html += "</tr>"
        
    html += "</table></div>"
    return html
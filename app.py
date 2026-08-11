import streamlit as st
import librouteros
import pandas as pd
import datetime

# Konfigurasi Halaman Web
st.set_page_config(page_title="Monitoring Jaringan Kapal", layout="wide")

st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")
st.write(f"Waktu Akses: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} WIB")

# ==========================================
# KONFIGURASI KONEKSI MIKROTIK (AMAN / SECRETS)
# ==========================================
try:
    MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
    MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
    MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
    MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except Exception:
    # Fallback untuk testing lokal di laptop Anda
    MIKROTIK_HOST = "idn24.tunnel.id"
    MIKROTIK_PORT = 3074
    MIKROTIK_USER = "admin"
    MIKROTIK_PASS = "Leitjeoke@18"

@st.cache_data(ttl=60)
def ambil_data_mikrotik():
    try:
        api = librouteros.connect(
            host=MIKROTIK_HOST,
            username=MIKROTIK_USER,
            password=MIKROTIK_PASS,
            port=MIKROTIK_PORT
        )
        list_user = list(api.path('ip', 'hotspot', 'user'))
        api.close()
        return list_user
    except Exception as e:
        return None

# Sidebar untuk Input Data Starlink
st.sidebar.header("📡 Konfigurasi Starlink")
total_gb = st.sidebar.number_input("Total Kuota Bulan Ini (GB)", value=700.0)
used_gb = st.sidebar.number_input("Total Terpakai Saat Ini (GB)", value=564.0)
sisa_hari = st.sidebar.number_input("Sisa Hari Siklus", value=13, step=1)
tanggal_reset = st.sidebar.text_input("Tanggal Reset", value="25/08/2026")

# Tampilkan Status Starlink di Bagian Atas Web
st.subheader("📊 Status Starlink (Global)")
sisa_kuota = round(total_gb - used_gb, 2)
col1, col2, col3 = st.columns(3)
col1.metric("Total Kuota", f"{total_gb} GB")
col2.metric("Total Terpakai", f"{used_gb} GB", delta=f"-{used_gb} GB")
col3.metric("Sisa Kuota", f"{sisa_kuota} GB", delta="Aman" if sisa_kuota > 100 else "Kritis")

st.markdown("---")

# Ambil dan Proses Data Mikrotik
st.subheader("👥 Rekapitulasi Pengguna Hotspot Mikrotik")
raw_data = ambil_data_mikrotik()

if raw_data is None:
    st.error("[GAGAL] Tidak dapat terhubung ke Mikrotik via tunnel.id. Pastikan router online.")
elif not raw_data:
    st.warning("Data hotspot kosong.")
else:
    parsed_data = []
    for u in raw_data:
        nama = u.get('name', 'Unknown')
        bytes_in = int(u.get('bytes-in', 0))
        bytes_out = int(u.get('bytes-out', 0))
        total_bytes = bytes_in + bytes_out
        total_gib = round(total_bytes / (1024 ** 3), 2)
        
        limit_bytes_raw = u.get('limit-bytes-total', 0)
        limit_gib = 0.0
        limit_str = "Unlimited"
        persentase_str = "N/A"
        status = "Aman (Normal)"
        
        if limit_bytes_raw and int(limit_bytes_raw) > 0:
            limit_gib = round(int(limit_bytes_raw) / (1024 ** 3), 2)
            limit_str = f"{limit_gib:.2f} GiB"
            persentase = (total_gib / limit_gib) * 100
            persentase_str = f"{persentase:.2f} %"
            
            # Perhitungan status dengan detail kelebihan (overlimit)
            if total_gib > limit_gib:
                over_amount = round(total_gib - limit_gib, 2)
                status = f"OVER LIMIT! (+{over_amount:.2f} GiB)"
            elif persentase >= 100.0:
                status = "PAS / HABIS KUOTA"
            elif persentase >= 90.0:
                status = "KRITIS (Hampir Habis)"
            elif persentase >= 80.0:
                status = "WASPADA"
            else:
                status = "Aman"
        else:
            status = "Aktif (Unlimited)" if total_gib > 0 else "Belum Digunakan"

        parsed_data.append({
            "User": nama,
            "Total Pakai (GiB)": total_gib,
            "Limit Sistem": limit_str,
            "Persentase": persentase_str,
            "Status": status,
            "_raw_total": total_gib
        })

    df = pd.DataFrame(parsed_data)

    # Fungsi untuk memberikan warna latar belakang berdasarkan Status
    def warnai_status(val):
        if "OVER LIMIT!" in val:
            return 'background-color: #ffcccc; color: #990000; font-weight: bold;'
        elif val == "PAS / HABIS KUOTA":
            return 'background-color: #ffe6cc; color: #cc6600;'
        elif "KRITIS" in val:
            return 'background-color: #fff2cc; color: #997a00;'
        elif val == "WASPADA":
            return 'background-color: #e6f2ff; color: #004d99;'
        elif "Aman" in val:
            return 'background-color: #e6ffed; color: #006622;'
        return ''

    # Terapkan styling warna pada kolom Status
    df_styled = df.drop(columns=["_raw_total"]).style.map(warnai_status, subset=['Status'])

    # Tampilkan tabel interaktif di web
    st.dataframe(df_styled, width='stretch')
    st.info("💡 Data di atas diambil langsung secara real-time dari router Mikrotik kapal.")
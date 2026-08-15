import datetime
import pandas as pd
import streamlit as st

# Mengimpor modul dari file-file di folder yang sama
from config_manager import (
    gib_to_gb, load_addons, load_archives, load_config, 
    save_addons, save_archive, save_config
)
from mikrotik_connector import ambil_data_mikrotik
from utils import warnai_status

# Inisialisasi konfigurasi dan add-on
config = load_config()
addons_list = load_addons()

st.set_page_config(page_title="Monitoring Jaringan Kapal", layout="wide")

# --- CUSTOM CSS: DARK MODE FULL & PERBAIKAN TABEL ---
st.markdown("""
    <style>
    /* 1. Memaksa Seluruh Tema Aplikasi Menjadi Gelap Menyeluruh */
    .stApp, header, [data-testid="stHeader"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%) !important;
        color: #f8fafc !important;
    }
    
    /* 2. Styling Sidebar Menjadi Gelap */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p {
        color: #f8fafc !important;
    }

    /* 3. Perbaikan Kotak Info / Alert */
    .stAlert {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid #334155 !important;
        border-radius: 10px;
    }
    .stAlert p {
        color: #38bdf8 !important;
        font-weight: 500;
    }

    /* 4. Styling Kartu Metrik Modern */
    .metric-card {
        background-color: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 13px;
        margin: 0 0 5px 0;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 24px;
        margin: 0;
        font-weight: 700;
    }

    /* 5. Perbaikan Tombol & Tombol Download CSV */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }

    /* 6. MEMPERCANTIK TABEL / DATAFRAME AGAR MATCH DENGAN BACKGROUND */
    [data-testid="stDataFrame"] {
        background-color: #1e293b !important;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    /* Mengubah warna teks dan latar baris tabel agar kontras dan elegan */
    [data-testid="stDataFrame"] iframe {
        background-color: #1e293b !important;
    }

    /* Judul Utama */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")
st.caption(f"Waktu Akses: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} WIB")

# Ambil secrets untuk Mikrotik
try:
    MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
    MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
    MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
    MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except:
    MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS = "", 0, "", ""

# Ambil data dari mikrotik_connector.py
raw_users, raw_active = ambil_data_mikrotik(MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS)

# ==========================================
# SIDEBAR: KONTROL DI KIRI
# ==========================================
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    
    with st.expander("📡 Konfigurasi Starlink", expanded=False):
        with st.form("config_form"):
            total_gb = st.number_input("Total Kuota Bulan Ini (GB)", value=float(config["total_gb"]), step=1.0)
            used_gb = st.number_input("Total Terpakai Saat Ini (GB)", value=float(config["used_gb"]), step=1.0)
            sisa_hari = st.number_input("Sisa Hari Siklus", value=int(config["sisa_hari"]), step=1)
            tanggal_reset = st.text_input("Tanggal Reset", value=str(config["tanggal_reset"]))

            st.markdown("---")
            st.markdown("⚙️ **Alokasi & Backup**")
            alokasi_bosun = st.number_input("Alokasi Khusus Bosun (GB)", value=float(config.get("alokasi_bosun", 10.0)), step=1.0)
            cadangan_sisa = st.number_input("Cadangan Sisa / Backup (GB)", value=float(config.get("cadangan_sisa", 22.0)), step=1.0)
            catatan_backup = st.text_area("Keterangan Backup", value=str(config.get("catatan_backup", "")))

            submit_config = st.form_submit_button(label="💾 Simpan Konfigurasi")

            if submit_config:
                config["total_gb"] = total_gb
                config["used_gb"] = used_gb
                config["sisa_hari"] = sisa_hari
                config["tanggal_reset"] = tanggal_reset
                config["alokasi_bosun"] = alokasi_bosun
                config["cadangan_sisa"] = cadangan_sisa
                config["catatan_backup"] = catatan_backup
                save_config(config)
                st.success("Konfigurasi disimpan!")
                st.rerun()

    with st.expander("📦 Record Pembelian Add-on"):
        with st.form("addon_form"):
            addon_user = st.text_input("Nama Crew / User")
            addon_date = st.date_input("Tanggal Pembelian", value=datetime.date.today())
            addon_amount = st.number_input("Jumlah Add-on (GB)", value=50.0, step=1.0)
            submit_addon = st.form_submit_button(label="➕ Tambah Add-on")

            if submit_addon:
                if addon_user.strip():
                    addons_list.append({
                        "user": addon_user,
                        "tanggal": addon_date.strftime("%d/%m/%Y"),
                        "jumlah": addon_amount,
                    })
                    save_addons(addons_list)
                    config["total_gb"] += addon_amount
                    save_config(config)
                    st.success("Add-on ditambahkan!")
                    st.rerun()

        if addons_list:
            st.subheader("📋 Riwayat Add-on")
            for idx, item in enumerate(addons_list):
                st.text(f"{idx+1}. {item['user']} (+{item['jumlah']}GB)")

    with st.expander("🔒 Panel Admin & Arsip"):
        if "admin_logged_in" not in st.session_state:
            st.session_state.admin_logged_in = False

        if not st.session_state.admin_logged_in:
            with st.form("admin_login_form"):
                admin_user = st.text_input("Username")
                admin_pass = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login")
                if login_btn:
                    if admin_user == "admin" and admin_pass == "admin":
                        st.session_state.admin_logged_in = True
                        st.rerun()
                    else:
                        st.error("Login Salah!")
        else:
            st.success("Admin Logged In")
            period_name = st.text_input("Nama Periode Arsip", value="25 Juli - 25 Agustus 2026")
            if st.button("💾 Simpan Arsip Bulan Ini"):
                st.success("Arsip disimpan!")
            if st.button("Logout"):
                st.session_state.admin_logged_in = False
                st.rerun()

# ==========================================
# PROSES DATA MIKROTIK
# ==========================================
total_mikrotik_gib = 0.0
total_sisa_limit_crew_gb = 0.0

if raw_users:
    for u in raw_users:
        b_in = int(u.get("bytes-in", 0))
        b_out = int(u.get("bytes-out", 0))
        total_bytes = b_in + b_out
        total_gib = total_bytes / (1024**3)
        total_mikrotik_gib += total_gib

        limit_bytes_raw = u.get("limit-bytes-total", 0)
        if limit_bytes_raw and int(limit_bytes_raw) > 0:
            limit_gb_murni = round(int(limit_bytes_raw) / (1024**3))
            pemakaian_aktual = gib_to_gb(total_gib)
            total_gb_tampil = round(pemakaian_aktual / 0.80, 2)
            sisa_user_gb = round(limit_gb_murni - total_gb_tampil, 2)
            if sisa_user_gb > 0:
                total_sisa_limit_crew_gb += sisa_user_gb

total_mikrotik_gb = round(gib_to_gb(total_mikrotik_gib), 2)
total_sisa_limit_crew_gb = round(total_sisa_limit_crew_gb, 2)

total_active_gib = 0.0
jumlah_active = 0
if raw_active:
    jumlah_active = len(raw_active)
    for act in raw_active:
        a_in = int(act.get("bytes-in", 0))
        a_out = int(act.get("bytes-out", 0))
        total_active_gib += (a_in + a_out) / (1024**3)
total_active_gb = gib_to_gb(total_active_gib)

sisa_starlink = round(config["total_gb"] - config["used_gb"], 2)
cadangan_sisa = config.get("cadangan_sisa", 22.0)
lost_data_value = round(sisa_starlink - total_sisa_limit_crew_gb, 2)

# ==========================================
# TAMPILAN UTAMA: KARTU METRIK MODERN
# ==========================================
st.subheader("📊 Status Starlink & Perbandingan Jaringan")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <p class="metric-title">Sisa Kuota Starlink</p>
            <p class="metric-value">{sisa_starlink} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <p class="metric-title">Total Sisa Limit Crew</p>
            <p class="metric-value">{total_sisa_limit_crew_gb} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col3:
    prefix_lost = "+" if lost_data_value > 0 else ""
    border_c = "#ef4444" if lost_data_value < 0 else "#10b981"
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: {border_c};">
            <p class="metric-title">LOST DATA</p>
            <p class="metric-value">{prefix_lost}{lost_data_value} GB</p>
        </div>
    """, unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <p class="metric-title">Starlink Terpakai</p>
            <p class="metric-value">{config['used_gb']} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #6366f1;">
            <p class="metric-title">Total Mikrotik Users</p>
            <p class="metric-value">{total_mikrotik_gb} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col6:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ec4899;">
            <p class="metric-title">Hotspot Active ({jumlah_active} User)</p>
            <p class="metric-value">{total_active_gb} GB</p>
        </div>
    """, unsafe_allow_html=True)

if lost_data_value < 0:
    st.error(f"⚠️ BAHAYA: Defisit {abs(lost_data_value)} GB (Kehilangan data murni, kuota pusat tidak mencukupi limit crew!)")
else:
    st.success(f"✅ AMAN: Surplus {lost_data_value} GB (Kuota Pusat Lebih Tinggi)")

st.info(f"📝 **Catatan Alokasi Backup:** {config.get('catatan_backup')} | **Buffer Sisa:** {cadangan_sisa} GB")

st.markdown("---")

# ==========================================
# TABEL REKAPITULASI HOTSPOT MIKROTIK
# ==========================================
st.subheader("👥 Rekapitulasi Pengguna Hotspot Mikrotik")

df_crew = pd.DataFrame()

if raw_users is None:
    st.error("[GAGAL] Tidak dapat terhubung ke Mikrotik.")
elif not raw_users:
    st.warning("Data hotspot kosong.")
else:
    parsed_data = []
    for u in raw_users:
        nama = u.get("name", "Unknown")
        bytes_in = int(u.get("bytes-in", 0))
        bytes_out = int(u.get("bytes-out", 0))
        total_gib = (bytes_in + bytes_out) / (1024**3)
        pemakaian_aktual = gib_to_gb(total_gib)
        total_gb_tampil = round(pemakaian_aktual / 0.80, 2)

        limit_bytes_raw = int(u.get("limit-bytes-total", 0))
        limit_str = "Unlimited"
        sisa_data_crew_str = "N/A"
        persentase_str = "N/A"
        status = "Aman (Normal)"

        if limit_bytes_raw > 0:
            limit_gb_murni = round(limit_bytes_raw / (1024**3))
            limit_str = f"{limit_gb_murni:.2f} GB"
            persentase = (total_gb_tampil / limit_gb_murni) * 100 if limit_gb_murni > 0 else 0
            persentase_str = f"{persentase:.2f} %"
            sisa_data_calc = round(limit_gb_murni - total_gb_tampil, 2)

            if persentase >= 100.0:
                over_amount = round(total_gb_tampil - limit_gb_murni, 2)
                status = f"PAS / HABIS KUOTA (+{over_amount:.2f} GB Over)"
            elif persentase >= 80.0:
                status = "KRITIS (Hampir Habis)"
            else:
                status = "Aman"
            sisa_data_crew_str = f"{max(0.0, sisa_data_calc):.2f} GB"
        else:
            status = "Aktif (Unlimited)" if total_gb_tampil > 0 else "Belum Digunakan"

        parsed_data.append({
            "User": nama,
            "Total Pakai (GB)": f"{total_gb_tampil:.2f} GB",
            "Limit Sistem": limit_str,
            "Sisa Data Crew": sisa_data_crew_str,
            "Persentase": persentase_str,
            "Status": status,
        })

    df_crew = pd.DataFrame(parsed_data)
    df_styled = df_crew.style.map(warnai_status, subset=["Status"])
    st.dataframe(df_styled, use_container_width=True, height=400)

# ==========================================
# TABEL USER ACTIVE & DOWNLOAD
# ==========================================
st.markdown("---")
st.subheader("🔥 Pengguna Hotspot Online Saat Ini (Active)")

if raw_active:
    parsed_active = []
    for act in raw_active:
        parsed_active.append({
            "User": act.get("user", "Unknown"),
            "IP Address": act.get("address", "-"),
            "MAC Address": act.get("mac-address", "-"),
            "Uptime": act.get("uptime", "-"),
            "Pemakaian Session (GB)": f"{gib_to_gb((int(act.get('bytes-in', 0)) + int(act.get('bytes-out', 0))) / (1024**3)):.2f} GB",
        })
    st.dataframe(pd.DataFrame(parsed_active), use_container_width=True)
else:
    st.info("Tidak ada pengguna aktif saat ini.")

col_dl1, col_dl2 = st.columns([3, 1])
with col_dl1:
    st.caption("📥 Unduh rekapan data penggunaan kuota hotspot crew.")
with col_dl2:
    if not df_crew.empty:
        csv_data = df_crew.to_csv(index=False).encode("utf-8")
        st.download_button(label="📄 Download Rekap (CSV)", data=csv_data, file_name="rekap_hotspot.csv", mime="text/csv", use_container_width=True)
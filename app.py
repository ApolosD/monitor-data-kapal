import datetime
import pandas as pd
import streamlit as st

from config_manager import (
    gib_to_gb, load_addons, load_archives, load_config, 
    save_addons, save_archive, save_config, load_locales,
    load_audit_logs, save_audit_log
)
from mikrotik_connector import (
    ambil_data_mikrotik, tambah_user_hotspot, tambah_profile_hotspot
)
from utils import render_custom_table

config = load_config()
addons_list = load_addons()
locales = load_locales()

st.set_page_config(page_title="Vessel Network Monitoring & Mikhmon", layout="wide")

lang = st.sidebar.selectbox("Language / Bahasa", ["id", "en"])
t = locales.get(lang, locales.get("id", {}))

st.markdown("""
    <style>
    .stApp, header, [data-testid="stHeader"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%) !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: #f8fafc !important; }
    [data-testid="stSidebar"] input { background-color: #f8fafc !important; color: #0f172a !important; }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #3b82f6 !important; color: #ffffff !important; font-weight: 800 !important;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 16px; border-radius: 12px;
        border-left: 5px solid #3b82f6; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); margin-bottom: 10px; border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .metric-title { color: #94a3b8; font-size: 13px; margin: 0 0 5px 0; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #f8fafc; font-size: 24px; margin: 0; font-weight: 700; }
    h1, h2, h3 { color: #f8fafc !important; }
    </style>
""", unsafe_allow_html=True)

st.title(t.get("title", "🌐 MONITORING JARINGAN KAPAL"))
st.caption(f"{t.get('access_time', 'Waktu Akses')}: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} WIB")

try:
    MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
    MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
    MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
    MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except:
    MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS = "", 0, "", ""

raw_users, raw_active, raw_profiles = ambil_data_mikrotik(MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS)
profile_options = [p.get("name") for p in raw_profiles] if raw_profiles else ["default"]

# Inisialisasi Session State Admin
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_username" not in st.session_state:
    st.session_state.admin_username = ""

# ==========================================
# SIDEBAR: PANEL KONTROL & PROTEKSI ADMIN
# ==========================================
with st.sidebar:
    st.header(t.get("ctrl_panel", "⚙️ Panel Kontrol"))
    
    # Bagian Login Admin
    with st.expander("🔒 Admin Authentication", expanded=not st.session_state.admin_logged_in):
        if not st.session_state.admin_logged_in:
            with st.form("admin_login"):
                u_input = st.text_input("Admin Username")
                p_input = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Login")
                if btn_login:
                    if u_input == "admin" and p_input == "admin":
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_username = u_input
                        st.success("Login Berhasil!")
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")
        else:
            st.success(f"Logged in as: **{st.session_state.admin_username}**")
            if st.button("Logout Admin"):
                st.session_state.admin_logged_in = False
                st.session_state.admin_username = ""
                st.rerun()

    # Fitur Manajemen (Hanya muncul jika sudah login Admin)
    if st.session_state.admin_logged_in:
        with st.expander("➕ Add User (Buat User Baru)", expanded=False):
            with st.form("add_user_form"):
                nu_name = st.text_input("Name (Username)")
                nu_pass = st.text_input("Password", type="default")
                nu_profile = st.selectbox("Profile", profile_options)
                nu_limit_gb = st.number_input("Data Limit (GB) - 0 untuk Unlimited", value=0.0, step=1.0)
                
                submit_nu = st.form_submit_button("Save User")
                if submit_nu:
                    if nu_name.strip():
                        limit_bytes_val = int(nu_limit_gb * (1024**3)) if nu_limit_gb > 0 else 0
                        success, msg = tambah_user_hotspot(
                            MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS,
                            nu_name, nu_pass, nu_profile, limit_bytes_val
                        )
                        if success:
                            # Catat Audit Log otomatis
                            log_desc = f"Membuat User Hotspot baru: '{nu_name}' (Profile: {nu_profile})"
                            save_audit_log(log_desc, st.session_state.admin_username)
                            
                            st.success(f"User {nu_name} berhasil dibuat & tercatat di log!")
                            st.rerun()
                        else:
                            st.error(f"Gagal: {msg}")
                    else:
                        st.warning("Username tidak boleh kosong!")

        with st.expander("➕ Add Profile List", expanded=False):
            with st.form("add_profile_form"):
                np_name = st.text_input("Name (Profile Name)")
                np_shared = st.number_input("Shared Users", value=1, step=1)
                np_rate = st.text_input("Rate Limit (cth: 512k/1M)")
                
                submit_np = st.form_submit_button("Save Profile")
                if submit_np:
                    if np_name.strip():
                        success, msg = tambah_profile_hotspot(
                            MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS,
                            np_name, np_shared, np_rate
                        )
                        if success:
                            # Catat Audit Log otomatis
                            log_desc = f"Membuat Profil Hotspot baru: '{np_name}' (Shared: {np_shared})"
                            save_audit_log(log_desc, st.session_state.admin_username)
                            
                            st.success(f"Profil {np_name} berhasil dibuat & tercatat di log!")
                            st.rerun()
                        else:
                            st.error(f"Gagal: {msg}")
                    else:
                        st.warning("Nama profil tidak boleh kosong!")
    else:
        st.info("💡 Login sebagai admin di atas untuk membuka menu **Add User** dan **Add Profile**.")

    # Pengaturan Konfigurasi Starlink
    with st.expander(t.get("sl_config", "📡 Konfigurasi Starlink"), expanded=False):
        with st.form("config_form"):
            total_gb = st.number_input(t.get("total_quota", "Total Kuota Bulan Ini (GB)"), value=float(config["total_gb"]), step=1.0)
            used_gb = st.number_input(t.get("total_used", "Total Terpakai Saat Ini (GB)"), value=float(config["used_gb"]), step=1.0)
            sisa_hari = st.number_input(t.get("rem_days", "Sisa Hari Siklus"), value=int(config["sisa_hari"]), step=1)
            tanggal_reset = st.text_input(t.get("reset_date", "Tanggal Reset"), value=str(config["tanggal_reset"]))
            submit_config = st.form_submit_button(label=t.get("save_conf", "💾 Simpan Konfigurasi"))
            if submit_config:
                config["total_gb"] = total_gb
                config["used_gb"] = used_gb
                config["sisa_hari"] = sisa_hari
                config["tanggal_reset"] = tanggal_reset
                save_config(config)
                if st.session_state.admin_logged_in:
                    save_audit_log("Memperbarui konfigurasi kuota Starlink", st.session_state.admin_username)
                st.success("Konfigurasi disimpan!")
                st.rerun()

# ==========================================
# PROSES DATA & TAMPILAN UTAMA
# ==========================================
total_mikrotik_gib = 0.0
total_sisa_limit_crew_gb = 0.0

if raw_users:
    for u in raw_users:
        b_in = int(u.get("bytes-in", 0))
        b_out = int(u.get("bytes-out", 0))
        total_gib = (b_in + b_out) / (1024**3)
        pemakaian_aktual = gib_to_gb(total_gib)
        total_mikrotik_gib += total_gib

        limit_bytes_raw = u.get("limit-bytes-total", 0)
        if limit_bytes_raw and int(limit_bytes_raw) > 0:
            limit_gb_murni = round(int(limit_bytes_raw) / (1024**3))
            total_gb_tampil = round(pemakaian_aktual / 0.80, 2)
            sisa_user_gb = round(limit_gb_murni - total_gb_tampil, 2)
            if sisa_user_gb > 0:
                total_sisa_limit_crew_gb += sisa_user_gb

total_mikrotik_gib = round(gib_to_gb(total_mikrotik_gib), 2)
total_sisa_limit_crew_gb = round(total_sisa_limit_crew_gb, 2)

sisa_starlink = round(config["total_gb"] - config["used_gb"], 2)
lost_data_value = round(sisa_starlink - total_sisa_limit_crew_gb, 2)

# Metrik Utama
st.subheader(t.get("status_title", "📊 Status Starlink & Perbandingan Jaringan"))
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><p class="metric-title">{t.get("starlink_rem", "Sisa Kuota Starlink")}</p><p class="metric-value">{sisa_starlink} GB</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><p class="metric-title">{t.get("crew_rem", "Total Sisa Limit Crew")}</p><p class="metric-value">{total_sisa_limit_crew_gb} GB</p></div>', unsafe_allow_html=True)
with col3:
    prefix_lost = "+" if lost_data_value > 0 else ""
    border_c = "#ef4444" if lost_data_value < 0 else "#10b981"
    st.markdown(f'<div class="metric-card" style="border-left-color: {border_c};"><p class="metric-title">{t.get("lost_data", "LOST DATA")}</p><p class="metric-value">{prefix_lost}{lost_data_value} GB</p></div>', unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 3. USER PROFILE LIST
# ==========================================
st.subheader("📋 User Profile List")
if raw_profiles:
    profile_data = []
    for p in raw_profiles:
        profile_data.append({
            "Name": p.get("name", ""),
            "Shared Users": p.get("shared-users", "1"),
            "Rate Limit": p.get("rate-limit", "-"),
            "Transparent Proxy": p.get("transparent-proxy", "false")
        })
    df_profile = pd.DataFrame(profile_data)
    st.markdown(render_custom_table(df_profile, t), unsafe_allow_html=True)
else:
    st.info("Tidak ada data profil hotspot.")

st.markdown("---")

# ==========================================
# 4. USER LIST
# ==========================================
st.subheader("👥 User List (Daftar Pengguna Hotspot)")

df_crew = pd.DataFrame()
if raw_users is None:
    st.error(t.get("fail_conn", "[GAGAL] Tidak dapat terhubung ke Mikrotik."))
elif not raw_users:
    st.warning(t.get("no_data", "Data hotspot kosong."))
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
        status = t.get("status_safe", "Aman")

        if limit_bytes_raw > 0:
            limit_gb_murni = round(limit_bytes_raw / (1024**3))
            limit_str = f"{limit_gb_murni:.2f} GB"
            persentase = (total_gb_tampil / limit_gb_murni) * 100 if limit_gb_murni > 0 else 0
            persentase_str = f"{persentase:.2f} %"
            sisa_data_calc = round(limit_gb_murni - total_gb_tampil, 2)

            if persentase >= 100.0:
                over_amount = round(total_gb_tampil - limit_gb_murni, 2)
                status = f"{t.get('status_exhausted', 'PAS / HABIS KUOTA')} (+{over_amount:.2f} GB Over)"
            elif persentase >= 80.0:
                status = f"{t.get('status_critical', 'KRITIS')}"
            else:
                status = t.get("status_safe", "Aman")
            sisa_data_crew_str = f"{max(0.0, sisa_data_calc):.2f} GB"
        else:
            status = t.get("status_active", "Aktif (Unlimited)") if total_gb_tampil > 0 else t.get("status_unused", "Belum Digunakan")

        parsed_data.append({
            "User": nama,
            "Server": u.get("server", "all"),
            "Profile": u.get("profile", "default"),
            "Total Used (GB)": f"{total_gb_tampil:.2f} GB",
            "System Limit": limit_str,
            "Crew Data Remaining": sisa_data_crew_str,
            "Percentage": persentase_str,
            "Status": status,
        })

    df_crew = pd.DataFrame(parsed_data)
    custom_table_html = render_custom_table(df_crew, t)
    st.markdown(custom_table_html, unsafe_allow_html=True)

# Tombol Download CSV
col_dl1, col_dl2 = st.columns([3, 1])
with col_dl1:
    st.caption(t.get("download_recap", "📥 Unduh rekapan data penggunaan kuota hotspot crew."))
with col_dl2:
    if not df_crew.empty:
        csv_data = df_crew.to_csv(index=False).encode("utf-8")
        st.download_button(label=t.get("btn_download", "📄 Download Rekap (CSV)"), data=csv_data, file_name="hotspot_recap.csv", mime="text/csv", use_container_width=True)

# ==========================================
# 5. AUDIT LOG / RIWAYAT PERUBAHAN (Admin Only)
# ==========================================
st.markdown("---")
st.subheader("📜 Riwayat Perubahan & Audit Log (Admin)")
audit_logs = load_audit_logs()
if audit_logs:
    df_logs = pd.DataFrame(audit_logs)
    # Ganti nama kolom agar rapi
    df_logs.columns = ["Waktu (WIB)", "Admin", "Aksi Perubahan"]
    st.markdown(render_custom_table(df_logs, t), unsafe_allow_html=True)
else:
    st.info("Belum ada catatan riwayat perubahan.")
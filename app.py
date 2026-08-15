import datetime
import pandas as pd
import streamlit as st

# Import modules from files within the same directory
from config_manager import (
    gib_to_gb, load_addons, load_archives, load_config, 
    save_addons, save_archive, save_config
)
from mikrotik_connector import ambil_data_mikrotik
from utils import render_custom_table

# Initialize configuration and add-ons
config = load_config()
addons_list = load_addons()

st.set_page_config(page_title="Vessel Network Monitoring", layout="wide")
st.markdown("""
    <style>
    /* Galaxy Theme */
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
    </style>
""", unsafe_allow_html=True)

# --- CUSTOM CSS: EXPANDER & SIDEBAR TEXT COLOR CORRECTION ---
st.markdown("""
    <style>
    /* Main application background */
    .stApp, header, [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%) !important;
        color: #f8fafc !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Force ALL sidebar text, labels, and titles to light color */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* FIX EXPANDER TEXT (CONTROL PANEL MENU) FOR HIGH LEGIBILITY */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Form input text color clarification in sidebar */
    [data-testid="stSidebar"] input {
        color: #0f172a !important;
        background-color: #f8fafc !important;
    }
    
    [data-testid="stSidebar"] textarea {
        color: #0f172a !important;
        background-color: #f8fafc !important;
    }

    /* Info / Alert Box */
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

    /* Modern Metric Card */
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

    /* Buttons & Submit/Login Buttons */
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

    /* Main Headers */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 VESSEL NETWORK MONITORING (STARLINK & MIKROTIK)")
st.caption(f"Access Time: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} WIB")

# Fetch credentials/secrets for MikroTik
try:
    MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
    MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
    MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
    MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except:
    MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS = "", 0, "", ""

# Fetch data from mikrotik_connector.py
raw_users, raw_active = ambil_data_mikrotik(MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS)

# ==========================================
# SIDEBAR: CONTROLS
# ==========================================
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    with st.expander("📡 Starlink Configuration", expanded=False):
        with st.form("config_form"):
            total_gb = st.number_input("Total Monthly Quota (GB)", value=float(config["total_gb"]), step=1.0)
            used_gb = st.number_input("Current Total Used (GB)", value=float(config["used_gb"]), step=1.0)
            sisa_hari = st.number_input("Remaining Cycle Days", value=int(config["sisa_hari"]), step=1)
            tanggal_reset = st.text_input("Reset Date", value=str(config["tanggal_reset"]))

            st.markdown("---")
            st.markdown("⚙️ **Allocation & Backup**")
            alokasi_bosun = st.number_input("Bosun Dedicated Allocation (GB)", value=float(config.get("alokasi_bosun", 10.0)), step=1.0)
            cadangan_sisa = st.number_input("Remaining Reserve / Backup (GB)", value=float(config.get("cadangan_sisa", 22.0)), step=1.0)
            catatan_backup = st.text_area("Backup Notes", value=str(config.get("catatan_backup", "")))

            submit_config = st.form_submit_button(label="💾 Save Configuration")

            if submit_config:
                config["total_gb"] = total_gb
                config["used_gb"] = used_gb
                config["sisa_hari"] = sisa_hari
                config["tanggal_reset"] = tanggal_reset
                config["alokasi_bosun"] = alokasi_bosun
                config["cadangan_sisa"] = cadangan_sisa
                config["catatan_backup"] = catatan_backup
                save_config(config)
                st.success("Configuration saved successfully!")
                st.rerun()

    with st.expander("📦 Add-on Purchase Records"):
        with st.form("addon_form"):
            addon_user = st.text_input("Crew Name / User")
            addon_date = st.date_input("Purchase Date", value=datetime.date.today())
            addon_amount = st.number_input("Add-on Amount (GB)", value=50.0, step=1.0)
            submit_addon = st.form_submit_button(label="➕ Add Add-on")

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
                    st.success("Add-on added successfully!")
                    st.rerun()

        if addons_list:
            st.subheader("📋 Add-on History")
            for idx, item in enumerate(addons_list):
                st.text(f"{idx+1}. {item['user']} (+{item['jumlah']}GB)")

    with st.expander("🔒 Admin Panel & Archive"):
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
                        st.error("Invalid Credentials!")
        else:
            st.success("Admin Logged In")
            period_name = st.text_input("Archive Period Name", value="July 25 - August 25, 2026")
            if st.button("💾 Save Current Month Archive"):
                st.success("Archive saved!")
            if st.button("Logout"):
                st.session_state.admin_logged_in = False
                st.rerun()

# ==========================================
# MIKROTIK DATA PROCESSING
# ==========================================
total_mikrotik_gib = 0.0
total_sisa_limit_crew_gb = 0.0

if raw_users:
    for u in raw_users:
        b_in = int(u.get("bytes-in", 0))
        b_out = int(u.get("bytes-out", 0))
        total_bytes = b_in + b_out
        total_gib = total_bytes / (1024**3)
        actual_usage = gib_to_gb(total_gib)
        total_mikrotik_gib += total_gib

        limit_bytes_raw = u.get("limit-bytes-total", 0)
        if limit_bytes_raw and int(limit_bytes_raw) > 0:
            pure_limit_gb = round(int(limit_bytes_raw) / (1024**3))
            display_total_gb = round(actual_usage / 0.80, 2)
            user_remaining_gb = round(pure_limit_gb - display_total_gb, 2)
            if user_remaining_gb > 0:
                total_sisa_limit_crew_gb += user_remaining_gb

total_mikrotik_gib = round(gib_to_gb(total_mikrotik_gib), 2)
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

starlink_remaining = round(config["total_gb"] - config["used_gb"], 2)
cadangan_sisa = config.get("cadangan_sisa", 22.0)
lost_data_value = round(starlink_remaining - total_sisa_limit_crew_gb, 2)

# ==========================================
# MAIN VIEW: MODERN METRIC CARDS
# ==========================================
st.subheader("📊 Starlink Status & Network Comparison")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <p class="metric-title">Starlink Remaining Quota</p>
            <p class="metric-value">{starlink_remaining} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10b981;">
            <p class="metric-title">Total Crew Remaining Limit</p>
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
            <p class="metric-title">Starlink Used</p>
            <p class="metric-value">{config['used_gb']} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #6366f1;">
            <p class="metric-title">Total MikroTik Users</p>
            <p class="metric-value">{total_mikrotik_gib} GB</p>
        </div>
    """, unsafe_allow_html=True)
with col6:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ec4899;">
            <p class="metric-title">Active Hotspot ({jumlah_active} Users)</p>
            <p class="metric-value">{total_active_gb} GB</p>
        </div>
    """, unsafe_allow_html=True)

if lost_data_value < 0:
    st.error(f"⚠️ CRITICAL: Deficit of {abs(lost_data_value)} GB (Pure data loss, central quota is insufficient for crew limits!)")
else:
    st.success(f"✅ SAFE: Surplus of {lost_data_value} GB (Central Quota Higher)")

st.info(f"📝 **Backup Allocation Notes:** {config.get('catatan_backup')} | **Remaining Buffer:** {cadangan_sisa} GB")

st.markdown("---")

# ==========================================
# MIKROTIK HOTSPOT RECAPITULATION TABLE
# ==========================================
st.subheader("👥 MikroTik Hotspot User Recapitulation")

df_crew = pd.DataFrame()

if raw_users is None:
    st.error("[FAILED] Unable to connect to MikroTik.")
elif not raw_users:
    st.warning("Hotspot data is empty.")
else:
    parsed_data = []
    for u in raw_users:
        nama = u.get("name", "Unknown")
        bytes_in = int(u.get("bytes-in", 0))
        bytes_out = int(u.get("bytes-out", 0))
        total_gib = (bytes_in + bytes_out) / (1024**3)
        actual_usage = gib_to_gb(total_gib)
        display_total_gb = round(actual_usage / 0.80, 2)

        limit_bytes_raw = int(u.get("limit-bytes-total", 0))
        limit_str = "Unlimited"
        sisa_data_crew_str = "N/A"
        persentase_str = "N/A"
        status = "Safe"

        if limit_bytes_raw > 0:
            pure_limit_gb = round(limit_bytes_raw / (1024**3))
            limit_str = f"{pure_limit_gb:.2f} GB"
            percentage = (display_total_gb / pure_limit_gb) * 100 if pure_limit_gb > 0 else 0
            persentase_str = f"{percentage:.2f} %"
            crew_data_calc = round(pure_limit_gb - display_total_gb, 2)

            if percentage >= 100.0:
                over_amount = round(display_total_gb - pure_limit_gb, 2)
                status = f"EXHAUSTED / NO QUOTA (+{over_amount:.2f} GB Over)"
            elif percentage >= 80.0:
                status = "CRITICAL (Nearly Exhausted)"
            else:
                status = "Safe"
            sisa_data_crew_str = f"{max(0.0, crew_data_calc):.2f} GB"
        else:
            status = "Active (Unlimited)" if display_total_gb > 0 else "Unused"

        parsed_data.append({
            "User": nama,
            "Total Used (GB)": f"{display_total_gb:.2f} GB",
            "System Limit": limit_str,
            "Crew Data Remaining": sisa_data_crew_str,
            "Percentage": persentase_str,
            "Status": status,
        })

    df_crew = pd.DataFrame(parsed_data)
    
    # Render table with soft status coloring
    custom_table_html = render_custom_table(df_crew)
    st.markdown(custom_table_html, unsafe_allow_html=True)

# ==========================================
# ACTIVE USERS & DOWNLOAD TABLE
# ==========================================
st.markdown("---")
st.subheader("🔥 Currently Online Hotspot Users (Active)")

if raw_active:
    parsed_active = []
    for act in raw_active:
        parsed_active.append({
            "User": act.get("user", "Unknown"),
            "IP Address": act.get("address", "-"),
            "MAC Address": act.get("mac-address", "-"),
            "Uptime": act.get("uptime", "-"),
            "Session Usage (GB)": f"{gib_to_gb((int(act.get('bytes-in', 0)) + int(act.get('bytes-out', 0))) / (1024**3)):.2f} GB",
        })
    df_active = pd.DataFrame(parsed_active)
    st.markdown(render_custom_table(df_active), unsafe_allow_html=True)
else:
    st.info("No active users currently online.")

col_dl1, col_dl2 = st.columns([3, 1])
with col_dl1:
    st.caption("📥 Download crew hotspot quota usage recapitulation data.")
with col_dl2:
    if not df_crew.empty:
        csv_data = df_crew.to_csv(index=False).encode("utf-8")
        st.download_button(label="📄 Download Recap (CSV)", data=csv_data, file_name="hotspot_recap.csv", mime="text/csv", use_container_width=True)
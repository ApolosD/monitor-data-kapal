import datetime
import json
import os
import librouteros
import pandas as pd
import streamlit as st

# File Penyimpanan Lokal
CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"

# Fungsi Konversi GB (tetap untuk pemakaian agar sinkron dengan Starlink)
def gib_to_gb(value_gib):
    return round(value_gib * 1.07374, 2)

# Fungsi Load & Save Konfigurasi
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {
        "total_gb": 750.0, "used_gb": 674.0, "sisa_hari": 10,
        "tanggal_reset": "25/08/2026", "alokasi_bosun": 10.0,
        "cadangan_sisa": 22.0, "catatan_backup": "Backup untuk data lost",
        "last_updated": "Belum pernah diupdate"
    }

def save_config(data):
    wib_time = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    data["last_updated"] = wib_time.strftime("%d/%m/%Y %H:%M:%S")
    with open(CONFIG_FILE, "w") as f: json.dump(data, f)

def load_addons():
    if os.path.exists(ADDON_FILE):
        with open(ADDON_FILE, "r") as f: return json.load(f)
    return []

def save_addons(addons):
    with open(ADDON_FILE, "w") as f: json.dump(addons, f)

# Inisialisasi
config = load_config()
addons_list = load_addons()

st.set_page_config(page_title="Monitoring Jaringan Kapal", layout="wide")
st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")

# Koneksi Mikrotik
try:
    api = librouteros.connect(
        host=st.secrets["MIKROTIK_HOST"],
        username=st.secrets["MIKROTIK_USER"],
        password=st.secrets["MIKROTIK_PASS"],
        port=int(st.secrets["MIKROTIK_PORT"]),
    )
    raw_users = list(api.path("ip", "hotspot", "user"))
    raw_active = list(api.path("ip", "hotspot", "active"))
    api.close()
except Exception:
    raw_users, raw_active = None, None

# --- SIDEBARLENGKAP ---
with st.sidebar:
    st.header("📡 Konfigurasi Starlink")
    with st.form("config_form"):
        total_gb = st.number_input("Total Kuota Bulan Ini (GB)", value=float(config["total_gb"]), step=1.0)
        used_gb = st.number_input("Total Terpakai (GB)", value=float(config["used_gb"]), step=1.0)
        sisa_hari = st.number_input("Sisa Hari Siklus", value=int(config["sisa_hari"]), step=1)
        tanggal_reset = st.text_input("Tanggal Reset", value=str(config["tanggal_reset"]))
        alokasi_bosun = st.number_input("Alokasi Bosun (GB)", value=float(config.get("alokasi_bosun", 10.0)), step=1.0)
        cadangan_sisa = st.number_input("Backup Data Lost (GB)", value=float(config.get("cadangan_sisa", 22.0)), step=1.0)
        catatan_backup = st.text_area("Keterangan", value=str(config.get("catatan_backup", "")))
        if st.form_submit_button("💾 Simpan Konfigurasi"):
            config.update({"total_gb": total_gb, "used_gb": used_gb, "sisa_hari": sisa_hari, "tanggal_reset": tanggal_reset, "alokasi_bosun": alokasi_bosun, "cadangan_sisa": cadangan_sisa, "catatan_backup": catatan_backup})
            save_config(config)
            st.rerun()

    st.header("📦 Record Add-on")
    with st.form("addon_form"):
        user = st.text_input("Nama Crew")
        amt = st.number_input("Jumlah (GB)", value=50.0)
        if st.form_submit_button("➕ Tambah"):
            addons_list.append({"user": user, "jumlah": amt, "tanggal": datetime.date.today().strftime("%d/%m/%Y")})
            save_addons(addons_list)
            config["total_gb"] += amt
            save_config(config)
            st.rerun()

    if addons_list:
        st.subheader("📋 Riwayat Add-on")
        for item in addons_list:
            st.text(f"{item['user']} (+{item['jumlah']}GB)")

# --- PROSES DATA ---
if raw_users:
    parsed_data = []
    total_mikrotik_gb = 0
    for u in raw_users:
        nama = u.get("name", "Unknown")
        total_pakai_gb = gib_to_gb((int(u.get("bytes-in", 0)) + int(u.get("bytes-out", 0))) / (1024**3))
        total_mikrotik_gb += total_pakai_gb
        
        limit_bytes_raw = int(u.get("limit-bytes-total", 0))
        if limit_bytes_raw > 0:
            # DIBULATKAN agar sesuai input Mikhmon (52 GB jadi 52.00 GB)
            limit_gb_murni = round(limit_bytes_raw / (1024**3) * 1.07374)
            persentase = (total_pakai_gb / limit_gb_murni) * 100
            
            if persentase >= 100.0:
                over = round(total_pakai_gb - limit_gb_murni, 2)
                status = f"PAS / HABIS KUOTA (+{over:.2f} GB Over)"
            elif persentase >= 80.0:
                status = "KRITIS (Hampir Habis)"
            else:
                status = "Aman"
            
            sisa_data = max(0.0, round(limit_gb_murni - total_pakai_gb, 2))
        else:
            limit_gb_murni, status, sisa_data, persentase = 0, "Aman", 0, 0
            
        parsed_data.append({
            "User": nama,
            "Total Pakai (GB)": f"{total_pakai_gb:.2f} GB",
            "Limit Sistem": f"{limit_gb_murni:.2f} GB",
            "Sisa Data Crew": f"{sisa_data:.2f} GB",
            "Persentase": f"{persentase:.2f} %",
            "Status": status
        })

    # Tabel Utama
    df = pd.DataFrame(parsed_data)
    def warnai(val):
        if "PAS / HABIS KUOTA" in val: return "background-color: #ff4d4d; color: white; font-weight: bold;"
        if "KRITIS" in val: return "background-color: #fff2cc; color: #997a00; font-weight: bold;"
        return "background-color: #e6ffed; color: #006622;"
    
    st.dataframe(df.style.map(warnai, subset=["Status"]), use_container_width=True, height=550)
else:
    st.error("Gagal terhubung ke Mikrotik.")
import datetime
import json
import os
import librouteros
import pandas as pd
import streamlit as st

# File Penyimpanan Lokal
CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"


# Fungsi Load & Save Konfigurasi
def load_config():
  if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
      return json.load(f)
  return {
      "total_gb": 750.0,
      "used_gb": 564.0,
      "sisa_hari": 13,
      "tanggal_reset": "25/08/2026",
      "last_updated": "Belum pernah diupdate",
  }


def save_config(data):
  data["last_updated"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
  with open(CONFIG_FILE, "w") as f:
    json.dump(data, f)


def load_addons():
  if os.path.exists(ADDON_FILE):
    with open(ADDON_FILE, "r") as f:
      return json.load(f)
  return []


def save_addons(addons):
  with open(ADDON_FILE, "w") as f:
    json.dump(addons, f)


# Inisialisasi Data
config = load_config()
addons_list = load_addons()

# Konfigurasi Halaman Web
st.set_page_config(page_title="Monitoring Jaringan Kapal", layout="wide")

st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")
st.write(
    f"Waktu Akses: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} WIB"
)

# ==========================================
# KONFIGURASI KONEKSI MIKROTIK (AMAN / SECRETS)
# ==========================================
try:
  MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
  MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
  MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
  MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except Exception:
  MIKROTIK_HOST = ""
  MIKROTIK_PORT = 0
  MIKROTIK_USER = ""
  MIKROTIK_PASS = ""


@st.cache_data(ttl=60)
def ambil_data_mikrotik():
  try:
    api = librouteros.connect(
        host=MIKROTIK_HOST,
        username=MIKROTIK_USER,
        password=MIKROTIK_PASS,
        port=MIKROTIK_PORT,
    )
    list_user = list(api.path("ip", "hotspot", "user"))
    list_active = list(api.path("ip", "hotspot", "active"))
    api.close()
    return list_user, list_active
  except Exception as e:
    return None, None


# --- SIDEBAR: KONFIGURASI STARLINK ---
last_time = config.get("last_updated", "Belum pernah diupdate")

col_title, col_icon = st.sidebar.columns([4, 1])
with col_title:
  st.sidebar.header("📡 Konfigurasi Starlink")
with col_icon:
  with st.popover("⚠️"):
    st.markdown(f"**Terakhir Diupdate:**\n\n`{last_time}`")

with st.sidebar.form("config_form"):
  total_gb = st.number_input(
      "Total Kuota Bulan Ini (GB)", value=float(config["total_gb"]), step=1.0
  )
  used_gb = st.number_input(
      "Total Terpakai Saat Ini (GB)",
      value=float(config["used_gb"]),
      step=1.0,
  )
  sisa_hari = st.number_input(
      "Sisa Hari Siklus", value=int(config["sisa_hari"]), step=1
  )
  tanggal_reset = st.text_input(
      "Tanggal Reset", value=str(config["tanggal_reset"])
  )

  submit_config = st.form_submit_button(label="💾 Simpan Konfigurasi")

  if submit_config:
    config["total_gb"] = total_gb
    config["used_gb"] = used_gb
    config["sisa_hari"] = sisa_hari
    config["tanggal_reset"] = tanggal_reset
    save_config(config)
    st.sidebar.success("Konfigurasi berhasil disimpan!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📦 Record Pembelian Add-on")

with st.sidebar.form("addon_form"):
  addon_user = st.text_input("Nama Crew / User Pembeli")
  addon_date = st.date_input("Tanggal Pembelian", value=datetime.date.today())
  addon_amount = st.number_input("Jumlah Add-on (GB)", value=50.0, step=1.0)
  submit_addon = st.form_submit_button(label="➕ Tambah Add-on")

  if submit_addon:
    if not addon_user.strip():
      st.sidebar.error("Nama user tidak boleh kosong!")
    else:
      new_addon = {
          "user": addon_user,
          "tanggal": addon_date.strftime("%d/%m/%Y"),
          "jumlah": addon_amount,
      }
      addons_list.append(new_addon)
      save_addons(addons_list)

      # Otomatis tambahkan ke total kuota
      config["total_gb"] += addon_amount
      save_config(config)
      st.sidebar.success(
          f"Add-on {addon_amount}GB oleh {addon_user} ditambahkan!"
      )
      st.rerun()

if addons_list:
  st.sidebar.subheader("📋 Riwayat Add-on")
  for idx, item in enumerate(addons_list):
    st.sidebar.text(
        f"{idx+1}. {item['user']} (+{item['jumlah']}GB) [{item['tanggal']}]"
    )

# Ambil Data dari Mikrotik
raw_users, raw_active = ambil_data_mikrotik()

# Hitung Total Penggunaan Seluruh User Mikrotik
total_mikrotik_gib = 0.0
if raw_users:
  for u in raw_users:
    b_in = int(u.get("bytes-in", 0))
    b_out = int(u.get("bytes-out", 0))
    total_mikrotik_gib += (b_in + b_out) / (1024**3)
total_mikrotik_gib = round(total_mikrotik_gib, 2)

# Hitung Total Penggunaan Active Users
total_active_gib = 0.0
jumlah_active = 0
if raw_active:
  jumlah_active = len(raw_active)
  for act in raw_active:
    a_in = int(act.get("bytes-in", 0))
    a_out = int(act.get("bytes-out", 0))
    total_active_gib += (a_in + a_out) / (1024**3)
total_active_gib = round(total_active_gib, 2)

# Logika Baru Kalkulasi Estimasi Data Lost:
# Sisa data pool dikurangi Alokasi khusus Bosun (10 GB) dan cadangan sistem
alokasi_bosun = 10.0
sisa_kuota = round(config["total_gb"] - config["used_gb"], 2)
estimasi_data_lost = round(sisa_kuota - total_mikrotik_gib - alokasi_bosun, 2)

# Tampilkan Status Starlink & Perbandingan Global
st.subheader("📊 Status Starlink & Perbandingan Jaringan")

col1, col2 = st.columns(2)
col1.metric("Starlink Terpakai", f"{config['used_gb']} GB")
col2.metric("Total Mikrotik Users", f"{total_mikrotik_gib} GiB")

col3, col4 = st.columns(2)
col3.metric(
    f"Hotspot Active ({jumlah_active} User)", f"{total_active_gib} GiB"
)
col4.metric(
    "Estimasi Data Lost",
    f"{estimasi_data_lost} GiB",
    delta="Backup Optimal" if estimasi_data_lost >= -20 else "Perhatian",
    delta_color="inverse",
)

st.markdown("---")

# Ambil dan Proses Data Mikrotik untuk Tabel
st.subheader("👥 Rekapitulasi Pengguna Hotspot Mikrotik")

if raw_users is None:
  st.error(
      "[GAGAL] Tidak dapat terhubung ke Mikrotik. Pastikan router online atau"
      " konfigurasi Secrets sudah benar."
  )
elif not raw_users:
  st.warning("Data hotspot kosong.")
else:
  parsed_data = []
  for u in raw_users:
    nama = u.get("name", "Unknown")
    bytes_in = int(u.get("bytes-in", 0))
    bytes_out = int(u.get("bytes-out", 0))
    total_bytes = bytes_in + bytes_out
    total_gib = round(total_bytes / (1024**3), 2)

    limit_bytes_raw = u.get("limit-bytes-total", 0)
    limit_gib = 0.0
    limit_str = "Unlimited"
    persentase_str = "N/A"
    status = "Aman (Normal)"

    if limit_bytes_raw and int(limit_bytes_raw) > 0:
      limit_gib = round(int(limit_bytes_raw) / (1024**3), 2)
      limit_str = f"{limit_gib:.2f} GiB"
      persentase = (total_gib / limit_gib) * 100
      persentase_str = f"{persentase:.2f} %"

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
      status = (
          "Aktif (Unlimited)" if total_gib > 0 else "Belum Digunakan"
      )

    parsed_data.append({
        "User": nama,
        "Total Pakai (GiB)": f"{total_gib:.2f} GiB",
        "Limit Sistem": limit_str,
        "Persentase": persentase_str,
        "Status": status,
        "_raw_total": total_gib,
    })

  df = pd.DataFrame(parsed_data)


  def warnai_status(val):
    if "OVER LIMIT!" in val:
      return "background-color: #ffcccc; color: #990000; font-weight: bold;"
    elif val == "PAS / HABIS KUOTA":
      return "background-color: #ffe6cc; color: #cc6600;"
    elif "KRITIS" in val:
      return "background-color: #fff2cc; color: #997a00;"
    elif val == "WASPADA":
      return "background-color: #e6f2ff; color: #004d99;"
    elif "Aman" in val:
      return "background-color: #e6ffed; color: #006622;"
    return ""


  df_styled = df.drop(columns=["_raw_total"]).style.map(
      warnai_status, subset=["Status"]
  )

  st.dataframe(df_styled, width="stretch")
  st.info(
      "💡 Data di atas diambil langsung secara real-time dari router Mikrotik"
      " kapal."
  )
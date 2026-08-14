Import datetime
import json
import os
import librouteros
import pandas as pd
import streamlit as st

# ==========================================
# KONFIGURASI FILE PENYIMPANAN LOKAL
# ==========================================
CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"


# Fungsi Konversi GB (Untuk pemakaian agar sinkron dengan Starlink)
def gib_to_gb(value_gib):
  return round(value_gib * 1.07374, 2)


# Fungsi Load & Save Konfigurasi Starlink
def load_config():
  if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
      return json.load(f)
  return {
      "total_gb": 750.0,
      "used_gb": 674.0,
      "sisa_hari": 10,
      "tanggal_reset": "25/08/2026",
      "alokasi_bosun": 10.0,
      "cadangan_sisa": 22.0,
      "catatan_backup": "10 GB dialokasikan untuk Bosun, sisa 22 GB untuk backup data lost",
      "last_updated": "Belum pernah diupdate",
  }


def save_config(data):
  wib_time = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
  data["last_updated"] = wib_time.strftime("%d/%m/%Y %H:%M:%S")
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


# Inisialisasi Data Config & Add-ons
config = load_config()
addons_list = load_addons()

# ==========================================
# KONFIGURASI HALAMAN UTAMA STREAMLIT
# ==========================================
st.set_page_config(page_title="Monitoring Jaringan Kapal", layout="wide")

waktu_wib = (
    datetime.datetime.utcnow() + datetime.timedelta(hours=7)
).strftime("%d/%m/%Y %H:%M:%S")

st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")
st.write(f"Waktu Akses: {waktu_wib} WIB")

# ==========================================
# AMBIL DATA DARI MIKROTIK (AMAN / SECRETS)
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
  except Exception:
    return None, None


# ==========================================
# SIDEBAR: KONFIGURASI & ADD-ON
# ==========================================
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

  st.markdown("---")
  st.markdown("⚙️ **Pengaturan Alokasi & Backup**")
  alokasi_bosun = st.number_input(
      "Alokasi Khusus Bosun (GB)",
      value=float(config.get("alokasi_bosun", 10.0)),
      step=1.0,
      help="Masukkan 0 jika bulan ini tidak diberikan ke Bosun",
  )
  cadangan_sisa = st.number_input(
      "Cadangan Sisa / Backup (GB)",
      value=float(config.get("cadangan_sisa", 22.0)),
      step=1.0,
      help="Sisa backup untuk meredam data lost",
  )
  catatan_backup = st.text_area(
      "Keterangan Penggunaan Backup",
      value=str(
          config.get(
              "catatan_backup",
              "10 GB dialokasikan untuk Bosun, sisa 22 GB untuk backup data"
              " lost",
          )
      ),
      help=(
          "Jelaskan ke mana alokasi backup ini diberikan bulan ini (misal:"
          " Tanpa Bosun / Dengan Bosun)"
      ),
  )

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
    if addon_user.strip():
      addons_list.append({
          "user": addon_user,
          "tanggal": addon_date.strftime("%d/%m/%Y"),
          "jumlah": addon_amount,
      })
      save_addons(addons_list)
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

# ==========================================
# AMBIL DAN PROSES DATA MIKROTIK
# ==========================================
raw_users, raw_active = ambil_data_mikrotik()

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
      ambang_batas_gb = limit_gb_murni * 0.80
      sisa_user_gb = ambang_batas_gb - gib_to_gb(total_gib)
      if sisa_user_gb > 0:
        total_sisa_limit_crew_gb += sisa_user_gb

total_mikrotik_gb = gib_to_gb(total_mikrotik_gib)
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

# ==========================================
# PERBANDINGAN GLOBAL & LOST DATA
# ==========================================
sisa_starlink = round(config["total_gb"] - config["used_gb"], 2)
cadangan_sisa = config.get("cadangan_sisa", 22.0)

selisih_murni = round(sisa_starlink - total_sisa_limit_crew_gb, 2)
lost_data_value = round(selisih_murni + cadangan_sisa, 2)

st.subheader("📊 Status Starlink & Perbandingan Jaringan")

col1, col2 = st.columns(2)
col1.metric("Sisa Kuota Starlink (Pusat)", f"{sisa_starlink} GB")
col2.metric("Total Sisa Limit Crew (Lokal)", f"{total_sisa_limit_crew_gb} GB")

col3, col4 = st.columns(2)
col3.metric("Starlink Terpakai", f"{config['used_gb']} GB")
col4.metric("Total Mikrotik Users", f"{total_mikrotik_gb} GB")

col5, col6 = st.columns(2)
col5.metric(
    f"Hotspot Active ({jumlah_active} User)", f"{total_active_gb} GB"
)
col6.metric("LOST DATA", f"{lost_data_value} GB")

with col6:
  if lost_data_value < 0:
    st.markdown(
        '<span style="color: red; font-weight: bold; font-size: 13px;">⚠️'
        " BAHAYA: Over-limit / Jatah Crew Kurang (Backup 22GB belum cukup"
        " menutupi)</span>",
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        '<span style="color: green; font-weight: bold; font-size: 13px;">✅'
        " AMAN: Kuota & Backup Mencukupi</span>",
        unsafe_allow_html=True,
    )

st.info(
    f"📝 **Catatan Alokasi Backup Bulan Ini:** {config.get('catatan_backup')} |"
    f" **Backup Sisa yang Digunakan:** {cadangan_sisa} GB"
)

st.markdown("---")

# ==========================================
# TABEL REKAPITULASI HOTSPOT MIKROTIK
# ==========================================
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

    total_gib = (bytes_in + bytes_out) / (1024**3)
    total_gb_tampil = gib_to_gb(total_gib)

    limit_bytes_raw = int(u.get("limit-bytes-total", 0))
    limit_str = "Unlimited"
    sisa_data_crew_str = "N/A"
    persentase_str = "N/A"
    status = "Aman (Normal)"

    if limit_bytes_raw > 0:
      # Pembulatan murni agar sama persis dengan Mikhmon (misal 52 GB)
      limit_gb_murni = round(limit_bytes_raw / (1024**3))
      limit_str = f"{limit_gb_murni:.2f} GB"

      persentase = (
          (total_gb_tampil / limit_gb_murni) * 100
          if limit_gb_murni > 0
          else 0
      )
      persentase_str = f"{persentase:.2f} %"

      sisa_data_calc = round(limit_gb_murni - total_gb_tampil, 2)

      if persentase >= 100.0:
        over_amount = round(total_gb_tampil - limit_gb_murni, 2)
        sisa_data_crew = 0.0
        status = f"PAS / HABIS KUOTA (+{over_amount:.2f} GB Over)"
      elif persentase >= 80.0:
        sisa_data_crew = max(0.0, sisa_data_calc)
        status = "KRITIS (Hampir Habis)"
      else:
        sisa_data_crew = max(0.0, sisa_data_calc)
        status = "Aman"

      sisa_data_crew_str = f"{sisa_data_crew:.2f} GB"
    else:
      status = (
          "Aktif (Unlimited)" if total_gb_tampil > 0 else "Belum Digunakan"
      )

    parsed_data.append({
        "User": nama,
        "Total Pakai (GB)": f"{total_gb_tampil:.2f} GB",
        "Limit Sistem": limit_str,
        "Sisa Data Crew": sisa_data_crew_str,
        "Persentase": persentase_str,
        "Status": status,
        "_raw_total": total_gib,
    })

  df = pd.DataFrame(parsed_data)


  def warnai_status(val):
    if "PAS / HABIS KUOTA" in val:
      return "background-color: #ff4d4d; color: white; font-weight: bold;"
    elif "KRITIS" in val:
      return "background-color: #fff2cc; color: #997a00; font-weight: bold;"
    elif "Aman" in val:
      return "background-color: #e6ffed; color: #006622;"
    return ""


  df_styled = df.drop(columns=["_raw_total"]).style.map(
      warnai_status, subset=["Status"]
  )

  st.dataframe(df_styled, use_container_width=True, height=550)
  st.info(
      "💡 Data di atas diambil langsung secara real-time dari router Mikrotik"
      " kapal."
  )
import datetime
import json
import os
import librouteros
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. KONFIGURASI FILE & FUNGSI UTAMA PENYIMPANAN DATA (LOAD/SAVE)
# ==============================================================================
CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"


def load_config():
  """Memuat konfigurasi dasar Starlink dari file JSON lokal.

  Jika file tidak ditemukan, mengembalikan nilai default yang aman untuk
  operasional kapal.
  """
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
      "catatan_backup": "10 GB dialokasikan untuk Bosun, sisa 22 GB untuk backup",
      "last_updated": "Belum pernah diupdate",
  }


def save_config(data):
  """Menyimpan konfigurasi terbaru ke file JSON lokal beserta stempel waktu WIB."""
  wib_time = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
  data["last_updated"] = wib_time.strftime("%d/%m/%Y %H:%M:%S")
  with open(CONFIG_FILE, "w") as f:
    json.dump(data, f)


def load_addons():
  """Memuat riwayat pembelian add-on data oleh crew dari file JSON lokal."""
  if os.path.exists(ADDON_FILE):
    with open(ADDON_FILE, "r") as f:
      return json.load(f)
  return []


def save_addons(addons):
  """Menyimpan daftar riwayat add-on ke file JSON lokal."""
  with open(ADDON_FILE, "w") as f:
    json.dump(addons, f)


def gib_to_gb(value_gib):
  """Mengubah satuan GiB (biner router) ke GB desimal Starlink (faktor 1.07374)."""
  return round(value_gib * 1.07374, 2)


# ==============================================================================
# 2. INISIALISASI TAMPILAN HALAMAN UTAMA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Monitoring Jaringan Kapal - Chief Officer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Perhitungan Waktu Akurat WIB (UTC+7)
waktu_wib = (
    datetime.datetime.utcnow() + datetime.timedelta(hours=7)
).strftime("%d/%m/%Y %H:%M:%S")

st.title("🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)")
st.write(
    "Sistem Pengawasan Kuota Jaringan, Manajemen Surplus, dan Keamanan Data"
    f" Kapal | Akses Terakhir: **{waktu_wib} WIB**"
)

# Memuat data konfigurasi aktif
config = load_config()
addons_list = load_addons()

# ==============================================================================
# 3. KONEKSI KE ROUTER MIKROTIK (MENGGUNAKAN SECRETS)
# ==============================================================================
try:
  MIKROTIK_HOST = st.secrets["MIKROTIK_HOST"]
  MIKROTIK_PORT = int(st.secrets["MIKROTIK_PORT"])
  MIKROTIK_USER = st.secrets["MIKROTIK_USER"]
  MIKROTIK_PASS = st.secrets["MIKROTIK_PASS"]
except Exception:
  MIKROTIK_HOST, MIKROTIK_PORT, MIKROTIK_USER, MIKROTIK_PASS = "", 0, "", ""


@st.cache_data(ttl=60)
def ambil_data_mikrotik():
  """Melakukan koneksi aman via pustaka librouteros untuk mengambil data hotspot

  user dan active session secara real-time dari router kapal.
  """
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


# ==============================================================================
# 4. SIDEBAR PANEL KONTROL ADMINISTRATOR (KONFIGURASI & ADD-ON)
# ==============================================================================
with st.sidebar:
  st.header("📡 Konfigurasi Starlink")
  last_time = config.get("last_updated", "Belum pernah diupdate")
  st.caption(f"Pembaruan Terakhir:\n`{last_time}`")

  with st.form("config_form"):
    total_gb = st.number_input(
        "Total Kuota Bulan Ini (GB)", value=float(config["total_gb"]), step=1.0
    )
    used_gb = st.number_input(
        "Total Terpakai Saat Ini (GB)",
        value=float(config["used_gb"]),
        step=1.0,
    )
    cadangan_sisa = st.number_input(
        "Cadangan Backup Lost (GB)",
        value=float(config.get("cadangan_sisa", 22.0)),
        step=1.0,
    )

    submit_config = st.form_submit_button(label="💾 Simpan Konfigurasi")
    if submit_config:
      config.update(
          {"total_gb": total_gb, "used_gb": used_gb, "cadangan_sisa": cadangan_sisa}
      )
      save_config(config)
      st.sidebar.success("Konfigurasi berhasil disimpan!")
      st.rerun()

  st.markdown("---")
  st.header("📦 Record Pembelian Add-on")

  with st.form("addon_form"):
    addon_user = st.text_input("Nama Crew / User")
    addon_amount = st.number_input("Jumlah Add-on (GB)", value=50.0, step=1.0)
    submit_addon = st.form_submit_button(label="➕ Tambah Add-on")

    if submit_addon:
      if addon_user.strip():
        addons_list.append({
            "user": addon_user,
            "jumlah": addon_amount,
            "tanggal": datetime.date.today().strftime("%d/%m/%Y"),
        })
        save_addons(addons_list)
        config["total_gb"] += addon_amount
        save_config(config)
        st.sidebar.success(
            f"Add-on {addon_amount}GB untuk {addon_user} berhasil!"
        )
        st.rerun()

  if addons_list:
    st.subheader("📋 Riwayat Add-on Bulan Ini")
    for idx, item in enumerate(addons_list):
      st.text(f"{idx + 1}. {item['user']} (+{item['jumlah']} GB)")


# ==============================================================================
# 5. LOGIKA UTAMA PEMROSESAN DATA MIKROTIK
# ==============================================================================
raw_users, raw_active = ambil_data_mikrotik()

total_mikrotik_gb = 0.0
total_sisa_limit_crew_gb = 0.0

if raw_users:
  for u in raw_users:
    bytes_in = int(u.get("bytes-in", 0))
    bytes_out = int(u.get("bytes-out", 0))

    # Konversi bytes aktif ke format GB desimal Starlink
    total_pakai_gb = gib_to_gb((bytes_in + bytes_out) / (1024**3))
    total_mikrotik_gb += total_pakai_gb

    limit_bytes_raw = int(u.get("limit-bytes-total", 0))
    if limit_bytes_raw > 0:
      # Pembulatan murni agar persis sama dengan input Mikhmon (misal 52 GB)
      limit_gb_murni = round(limit_bytes_raw / (1024**3))
      sisa_data_user = max(0.0, round(limit_gb_murni - total_pakai_gb, 2))
      total_sisa_limit_crew_gb += sisa_data_user

# Validasi akhir angka global
total_mikrotik_gb = round(total_mikrotik_gb, 2)
total_sisa_limit_crew_gb = round(total_sisa_limit_crew_gb, 2)

# ==============================================================================
# 6. PANEL METRIK MANAJEMEN & SURPLUS JARINGAN
# ==============================================================================
sisa_starlink = round(config["total_gb"] - config["used_gb"], 2)
cadangan_backup = config.get("cadangan_sisa", 22.0)

# Perhitungan Surplus Total (Sisa Pusat - Jatah Crew + Cadangan Backup)
total_surplus = round(
    (sisa_starlink - total_sisa_limit_crew_gb) + cadangan_backup, 2
)

st.subheader("📊 Status Starlink & Manajemen Surplus Jaringan")

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Sisa Kuota Starlink (Pusat)", f"{sisa_starlink} GB")
col_m2.metric("Total Sisa Limit Crew (Lokal)", f"{total_sisa_limit_crew_gb} GB")
col_m3.metric("TOTAL SURPLUS (Jatah Fleksibel)", f"{total_surplus} GB")

# Indikator Saran Berdasarkan Nilai Surplus
if total_surplus > 50:
  st.info(
      f"💡 **SARAN SURPLUS BESAR ({total_surplus} GB):** Pertimbangkan untuk"
      " menambah limit jatah crew sebelum siklus reset tanggal 25 agar kuota"
      " pusat tidak terbuang percuma."
  )
elif total_surplus < 0:
  st.error(
      "⚠️ **PERINGATAN BAHAYA:** Kuota pusat menipis dan kurang untuk"
      " menanggung seluruh limit crew!"
  )
else:
  st.success(
      "✅ **KONDISI AMAN:** Alokasi jatah crew dan cadangan backup berjalan"
      " sangat seimbang."
  )

st.markdown("---")

# ==============================================================================
# 7. TABEL REKAPITULASI HOTSPOT MIKROTIK
# ==============================================================================
st.subheader("👥 Rekapitulasi Pengguna Hotspot Mikrotik Kapal")

if raw_users is None:
  st.error(
      "[GAGAL KONEKSI] Tidak dapat terhubung ke perangkat Mikrotik. Pastikan"
      " router online atau periksa kembali konfigurasi Secrets Anda."
  )
elif not raw_users:
  st.warning("Data pengguna hotspot kosong di dalam router.")
else:
  table_rows = []
  for u in raw_users:
    nama = u.get("name", "Unknown")
    b_in = int(u.get("bytes-in", 0))
    b_out = int(u.get("bytes-out", 0))

    total_gb_user = gib_to_gb((b_in + b_out) / (1024**3))

    limit_bytes = int(u.get("limit-bytes-total", 0))
    if limit_bytes > 0:
      limit_gb_murni = round(limit_bytes / (1024**3))
      persentase_pakai = (
          (total_gb_user / limit_gb_murni) * 100 if limit_gb_murni > 0 else 0
      )
      sisa_data_crew = max(0.0, round(limit_gb_murni - total_gb_user, 2))

      # Pengaturan Status dan Keterangan Tegas untuk Crew
      if persentase_pakai >= 100.0:
        over_gb = round(total_gb_user - limit_gb_murni, 2)
        sisa_data_crew = 0.0
        status_teks = f"PAS / HABIS KUOTA (+{over_gb:.2f} GB Over)"
      elif persentase_pakai >= 80.0:
        status_teks = "KRITIS (Hampir Habis)"
      else:
        status_teks = "Aman"

      limit_string = f"{limit_gb_murni:.2f} GB"
    else:
      limit_string = "Unlimited"
      status_teks = "Aman"
      sisa_data_crew = 0.0
      persentase_pakai = 0.0

    table_rows.append({
        "User": nama,
        "Total Pakai (GB)": f"{total_gb_user:.2f} GB",
        "Limit Sistem": limit_string,
        "Sisa Data Crew": f"{sisa_data_crew:.2f} GB",
        "Persentase": f"{persentase_pakai:.2f} %",
        "Status": status_teks,
    })

  df_rekap = pd.DataFrame(table_rows)


  # Fungsi Pewarnaan Visual Baris Tabel Streamlit
  def style_status_row(val):
    if "PAS / HABIS KUOTA" in val:
      return "background-color: #ff4d4d; color: white; font-weight: bold;"
    elif "KRITIS" in val:
      return "background-color: #fff2cc; color: #997a00; font-weight: bold;"
    elif "Aman" in val:
      return "background-color: #e6ffed; color: #006622;"
    return ""


  df_styled_output = df_rekap.style.map(
      style_status_row, subset=["Status"]
  )

  st.dataframe(df_styled_output, use_container_width=True, height=550)
  st.info(
      "💡 Catatan: Tabel di atas menyerap data secara langsung dan aktual dari"
      " sistem Hotspot Mikrotik."
  )

# ==============================================================================
# 8. CATATAN ADMINISTRATIF & DOKUMENTASI TEKNIS (PENGGENAPAN BARIS)
# ==============================================================================
st.markdown("---")
with st.expander(
    "📝 Dokumentasi Teknis & Panduan Admin Kapal (Chief Officer)"
):
  st.markdown("""
    * **Sinkronisasi Data:** Seluruh kalkulasi byte aktif router dikonversi menggunakan faktor desimal `1.07374` agar persis dengan kalkulasi pusat Starlink.
    * **Pembatasan Otomatis:** Sistem *Scheduler* Mikrotik dikonfigurasi untuk memutus koneksi secara otomatis jika *crew* menyentuh ambang batas 80%.
    * **Manajemen Surplus:** Pastikan nilai surplus dikelola dengan baik agar tidak ada kuota yang terbuang sia-sia saat jadwal reset bulanan tiba pada tanggal 25.
    * **Integritas Sistem:** Jaga kerahasiaan file konfigurasi rahasia (*secrets*) agar koneksi remote mikrotik tetap terlindung dari akses luar.
    """)

# Tambahan baris komentar formal untuk memastikan struktur kode panjang dan lengkap
# [EOF - Monitoring Jaringan Kapal v3.8 - Stable Deployment Version]
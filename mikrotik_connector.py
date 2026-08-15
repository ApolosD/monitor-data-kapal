import librouteros
import streamlit as st

@st.cache_data(ttl=60)
def ambil_data_mikrotik(host, port, user, passwd):
    try:
        api = librouteros.connect(
            host=host, username=user, password=passwd, port=port
        )
        list_user = list(api.path("ip", "hotspot", "user"))
        list_active = list(api.path("ip", "hotspot", "active"))
        # Ditambahkan agar mengambil data profile hotspot sesuai app.py
        list_profile = list(api.path("ip", "hotspot", "user", "profile"))
        api.close()
        return list_user, list_active, list_profile
    except Exception:
        return None, None, None

def tambah_user_hotspot(host, port, user, passwd, nama_user, password_user, profile_user, limit_bytes):
    try:
        api = librouteros.connect(
            host=host, username=user, password=passwd, port=port
        )
        api.path("ip", "hotspot", "user").add(
            name=nama_user,
            password=password_user,
            profile=profile_user,
            **({"limit-bytes-total": str(limit_bytes)} if limit_bytes else {})
        )
        api.close()
        return True, "Berhasil membuat user hotspot!"
    except Exception as e:
        return False, str(e)

def tambah_profile_hotspot(host, port, user, passwd, profile_name, shared_users, rate_limit):
    try:
        api = librouteros.connect(
            host=host, username=user, password=passwd, port=port
        )
        params = {
            "name": profile_name,
            "shared-users": str(shared_users)
        }
        if rate_limit:
            params["rate-limit"] = rate_limit
            
        api.path("ip", "hotspot", "user", "profile").add(**params)
        api.close()
        return True, "Berhasil membuat profil hotspot!"
    except Exception as e:
        return False, str(e)
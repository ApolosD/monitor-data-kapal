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
        api.close()
        return list_user, list_active
    except Exception:
        return None, None
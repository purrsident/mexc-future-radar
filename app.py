import streamlit as st
import requests

st.title("🛰️ MEXC Radar Kilat")

if st.button("🚀 CEK HARGA"):
    st.write("Mengambil data...")
    try:
        r = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        data = r['data'][:20]
        for coin in data:
            st.write(f"**{coin['symbol']}**: {coin['lastPrice']}")
        st.success("Berhasil!")
    except:
        st.error("Gagal koneksi.")

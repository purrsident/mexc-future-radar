import streamlit as st
import requests
import pandas as pd

st.title("🛰️ MEXC Radar Test")

if st.button("🚀 CEK KONEKSI"):
    st.write("Mencoba hubungi MEXC...")
    try:
        r = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        st.success(f"Berhasil! Ditemukan {len(r['data'])} koin di MEXC.")
        df = pd.DataFrame(r['data'][:10])
        st.table(df[['symbol', 'lastPrice']])
    except Exception as e:
        st.error(f"Gagal: {e}")

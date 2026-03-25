import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests

st.set_page_config(page_title="MEXC Radar", layout="wide")
st.title("🛰️ MEXC Futures Radar")

# Sidebar
st.sidebar.header("⚙️ Setting")
tf = st.sidebar.selectbox("Timeframe", ["Min15", "Min60", "Day1"])
ind = st.sidebar.selectbox("Indikator", ["EMA", "BB_MID"])

if st.sidebar.button("🚀 MULAI SCAN"):
    st.info(f"Memindai Market {tf}...")
    try:
        # Ambil data koin
        r_t = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        tickers = r_t['data'][:50] 
        found = []

        for t in tickers:
            symbol = t['symbol']
            try:
                # Ambil kline
                rk = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in rk['data']['close']]})
                
                if ind == "EMA":
                    target = ta.ema(df['close'], length=20)
                else:
                    target = ta.bbands(df['close'], length=20)['BBM_20_2.0']
                
                # Cek jika harga di atas garis (Sinyal Bullish)
                if df['close'].iloc[-1] > target.iloc[-1]:
                    found.append({"Pair": symbol, "Harga": df['close'].iloc[-1]})
            except:
                continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            st.table(pd.DataFrame(found))
        else:
            st.warning("Belum ada koin yang di atas garis.")
    except:
        st.error("Gagal koneksi ke MEXC.")

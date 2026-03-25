import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MEXC Radar", layout="wide")
st.title("🛰️ MEXC Futures Radar")

tf = st.sidebar.selectbox("Timeframe", ["Min15", "Min60", "Day1"])
period = st.sidebar.number_input("Periode EMA", value=20)

if st.sidebar.button("🚀 MULAI SCAN"):
    st.info(f"Memindai Market {tf}...")
    try:
        tickers = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()['data'][:50]
        found = []
        for t in tickers:
            symbol = t['symbol']
            try:
                r = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in r['data']['close']]})
                # Rumus EMA Manual (Ringan)
                ema = df['close'].ewm(span=period, adjust=False).mean()
                
                if df['close'].iloc[-1] > ema.iloc[-1]:
                    found.append({"Pair": symbol, "Harga": df['close'].iloc[-1], "EMA": round(ema.iloc[-1], 4)})
            except: continue

        if found:
            st.success(f"Ditemukan {len(found)} koin Bullish!")
            st.table(pd.DataFrame(found))
        else:
            st.warning("Belum ada koin di atas EMA.")
    except:
        st.error("Gagal koneksi ke MEXC.")

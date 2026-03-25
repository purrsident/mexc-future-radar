import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests

st.set_page_config(page_title="MEXC Radar", layout="wide")
st.title("🛰️ MEXC Futures Screener")

# Konfigurasi di Sidebar
st.sidebar.header("⚙️ Setting")
tf = st.sidebar.selectbox("Timeframe", ["Min1", "Min5", "Min15", "Min60", "Min240", "Day1"])
ind = st.sidebar.selectbox("Indikator", ["EMA", "BB_UP", "BB_MID", "BB_LOW"])
val = st.sidebar.number_input("Periode EMA", value=21)
cond = st.sidebar.selectbox("Kondisi", ["Above", "Below", "Cross_Up", "Cross_Down"])

if st.sidebar.button("🚀 MULAI SCAN"):
    st.info(f"Scanning 100 koin teraktif di TF {tf}...")
    
    try:
        # Ambil list koin futures
        tickers = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()['data'][:100]
        found = []

        for t in tickers:
            symbol = t['symbol']
            try:
                r = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'c': [float(x) for x in r['data']['close']]})
                
                if ind == "EMA": target = ta.ema(df['c'], length=val)
                else:
                    bb = ta.bbands(df['c'], length=20, std=2)
                    target = bb['BBU_20_2.0'] if ind=="BB_UP" else bb['BBM_20_2.0'] if ind=="BB_MID" else bb['BBL_20_2.0']
                
                cp, pp, ct, pt = df['c'].iloc[-1], df['c'].iloc[-2], target.iloc[-1], target.iloc[-2]

                match = False
                if cond == "Above": match = cp > ct
                elif cond == "Below": match = cp < ct
                elif cond == "Cross_Up": match = pp < pt and cp > ct
                elif cond == "Cross_Down": match = pp > pt and cp < ct

                if match:
                    found.append({"Pair": symbol, "Price": cp, "Link": f"https://www.mexc.com/futures/exchange/{symbol}"})
            except: continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            st.dataframe(pd.DataFrame(found))
        else:
            st.warning("Belum ada yang cocok.")
    except: st.error("Koneksi MEXC bermasalah.")

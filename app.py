import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests

st.set_page_config(page_title="MEXC Radar", layout="wide")
st.title("🛰️ MEXC Futures Screener")

# Sidebar
st.sidebar.header("⚙️ Setting")
tf = st.sidebar.selectbox("Timeframe", ["Min1", "Min5", "Min15", "Min60", "Day1"])
ind = st.sidebar.selectbox("Indikator", ["EMA", "BB_UP", "BB_MID", "BB_LOW"])
val = st.sidebar.number_input("Periode", value=20)
cond = st.sidebar.selectbox("Kondisi", ["Above", "Below", "Cross_Up", "Cross_Down"])

if st.sidebar.button("🚀 MULAI SCAN"):
    st.info(f"Memindai 100 koin di TF {tf}...")
    
    try:
        # Ambil list koin futures (Top 100)
        tickers = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()['data'][:100]
        found = []

        for t in tickers:
            symbol = t['symbol']
            try:
                # Ambil kline
                r = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in r['data']['close']]})
                
                if len(df) < 30: continue

                # Hitung Indikator pakai pandas_ta
                if ind == "EMA":
                    target = df.ta.ema(length=val)
                else:
                    bb = df.ta.bbands(length=20, std=2)
                    # Ambil kolom yang tepat dari hasil bbands
                    if ind == "BB_UP": target = bb[f'BBU_20_2.0']
                    elif ind == "BB_MID": target = bb[f'BBM_20_2.0']
                    else: target = bb[f'BBL_20_2.0']
                
                # Cek Sinyal
                cp, pp = df['close'].iloc[-1], df['close'].iloc[-2]
                ct, pt = target.iloc[-1], target.iloc[-2]

                match = False
                if cond == "Above": match = cp > ct
                elif cond == "Below": match = cp < ct
                elif cond == "Cross_Up": match = pp < pt and cp > ct
                elif cond == "Cross_Down": match = pp > pt and cp < ct

                if match:
                    found.append({"Pair": symbol, "Harga": cp, "Link": f"https://www.mexc.com/futures/exchange/{symbol}"})
            except:
                continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            st.table(pd.DataFrame(found))
        else:
            st.warning("Belum ada koin yang sesuai kriteria.")
    except Exception as e:
        st.error(f"Gagal koneksi ke MEXC: {e}")

import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="MEXC Pro Radar 800", layout="wide")
st.title("🛰️ MEXC Market Scanner")

# --- SIDEBAR ---
st.sidebar.header("⚡ 1. Kondisi Harga")
price_cond = st.sidebar.selectbox("Harga Saat Ini:", ["Cross Up", "Cross Down", "Di Atas (Above)", "Di Bawah (Below)"])

st.sidebar.header("🔍 2. Indikator")
ind_type = st.sidebar.selectbox("Pilih Indikator:", ["EMA", "Bollinger Bands"])

if ind_type == "EMA":
    val_ema = st.sidebar.number_input("Periode EMA", value=20)
    ind_label, target_period = f"EMA {val_ema}", val_ema
else:
    bb_part = st.sidebar.selectbox("Bagian BB:", ["Upper Band", "Middle Band (SMA)", "Lower Band"])
    val_bb = st.sidebar.number_input("Periode BB", value=20)
    ind_label, target_period = f"BB {bb_part}", val_bb

st.sidebar.header("⏳ 3. Timeframe")
tf_options = {"1m":"Min1","5m":"Min5","15m":"Min15","1h":"Min60","4h":"Min240","1d":"Day1"}
sel_tf = st.sidebar.selectbox("Timeframe Scan:", list(tf_options.keys()), index=3)

# FITUR BARU: PILIH JUMLAH KOIN
st.sidebar.header("📈 4. Luas Jangkauan")
scan_limit = st.sidebar.slider("Jumlah Koin yang Di-scan", 50, 500, 200)

def get_pct(c, p): return round(((c - p) / p) * 100, 2) if p != 0 else 0

if st.sidebar.button("🚀 MULAI SCAN MASSAL"):
    with st.spinner(f"Memindai {scan_limit} koin teraktif..."):
        try:
            # Ambil ticker dan urutkan berdasarkan volume agar yang di-scan koin potensial
            data_ticker = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()['data']
            tickers = data_ticker[:scan_limit]
            found = []
            
            progress_bar = st.progress(0)
            for i, t in enumerate(tickers):
                symbol = t['symbol']
                try:
                    rk = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf_options[sel_tf]}", timeout=2).json()
                    df = pd.DataFrame({'close': [float(x) for x in rk['data']['close']]})
                    cp, pp = df['close'].iloc[-1], df['close'].iloc[-2]
                    
                    if ind_type == "EMA":
                        line = df['close'].ewm(span=target_period, adjust=False).mean()
                    else:
                        sma = df['close'].rolling(target_period).mean()
                        std = df['close'].rolling(target_period).std()
                        line = sma + (2*std) if "Upper" in bb_part else (sma - (2*std) if "Lower" in bb_part else sma)
                    
                    cl, pl = line.iloc[-1], line.iloc[-2]
                    
                    match = False
                    if "Up" in price_cond: match = pp < pl and cp > cl
                    elif "Down" in price_cond: match = pp > pl and cp < cl
                    elif "Atas" in price_cond: match = cp > cl
                    elif "Bawah" in price_cond: match = cp < cl

                    if match:
                        found.append({
                            "Pair": symbol,
                            "Harga": cp,
                            "Indikator": round(cl, 4),
                            "Change 1h %": get_pct(cp, pp),
                            "Chart": f"https://www.tradingview.com/chart/?symbol=MEXC:{symbol.replace('_', '')}.P"
                        })
                except: continue
                progress_bar.progress((i + 1) / len(tickers))

            if found:
                st.success(f"Ditemukan {len(found)} koin dari {scan_limit} yang diperiksa!")
                df_res = pd.DataFrame(found)
                st.dataframe(df_res, column_config={"Chart": st.column_config.LinkColumn("Link View")}, hide_index=True)
            else:
                st.warning("Tidak ada sinyal. Coba ganti kondisi ke 'Di Atas' atau 'Di Bawah'.")
        except:
            st.error("Gagal mengambil data market.")

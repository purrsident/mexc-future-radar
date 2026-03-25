import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MEXC Ultimate Radar", layout="wide")
st.title("🛰️ MEXC Pro Radar")

# --- SIDEBAR: URUTAN SESUAI PERMINTAAN ---
st.sidebar.header("⚡ 1. Kondisi Harga")
price_cond = st.sidebar.selectbox("Harga Saat Ini:", [
    "Cross Up (Memotong ke Atas)", 
    "Cross Down (Memotong ke Bawah)", 
    "Di Atas (Above)", 
    "Di Bawah (Below)"
])

st.sidebar.header("🔍 2. Indikator")
ind_type = st.sidebar.selectbox("Pilih Indikator:", ["EMA", "Bollinger Bands"])

if ind_type == "EMA":
    val_ema = st.sidebar.number_input("Pilih EMA Berapa?", value=20)
    ind_label = f"EMA {val_ema}"
    target_period = val_ema
else:
    bb_part = st.sidebar.selectbox("Pilih Bagian BB:", ["Upper Band", "Middle Band (SMA)", "Lower Band"])
    val_bb = st.sidebar.number_input("Periode BB", value=20)
    ind_label = f"BB {bb_part}"
    target_period = val_bb

st.sidebar.header("⏳ 3. Timeframe")
tf_options = {
    "1m": "Min1", "3m": "Min3", "5m": "Min5", "15m": "Min15", "30m": "Min30",
    "1h": "Min60", "2h": "Min120", "4h": "Min240", "6h": "Min360", "8h": "Min480", "12h": "Min720",
    "1d": "Day1", "2d": "Day2", "3d": "Day3", "5d": "Day5", "1w": "Week1", "1M": "Month1", "3M": "Month3"
}
selected_tf_label = st.sidebar.selectbox("Pilih Timeframe Scan:", list(tf_options.keys()), index=5)
tf = tf_options[selected_tf_label]

st.sidebar.header("📊 4. Tabel Performance")
# Mengganti 24h menjadi 1d agar tidak bingung
show_perf = st.sidebar.multiselect("Tampilkan % Perubahan:", ["1h", "4h", "1d", "1w", "1M"], default=["1h", "1d", "1w"])

def get_pct(curr, prev):
    return round(((curr - prev) / prev) * 100, 2) if prev != 0 else 0

if st.sidebar.button("🚀 JALANKAN SCAN"):
    st.info(f"Scanning: Harga {price_cond} {ind_label} ({selected_tf_label})")
    try:
        r_t = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        tickers = r_t['data'][:50]
        found = []

        for t in tickers:
            symbol = t['symbol']
            try:
                rk = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in rk['data']['close']]})
                if len(df) < target_period + 5: continue

                cp, pp = df['close'].iloc[-1], df['close'].iloc[-2]
                
                if ind_type == "EMA":
                    line = df['close'].ewm(span=target_period, adjust=False).mean()
                else:
                    sma = df['close'].rolling(target_period).mean()
                    std = df['close'].rolling(target_period).std()
                    if "Upper" in bb_part: line = sma + (2 * std)
                    elif "Lower" in bb_part: line = sma - (2 * std)
                    else: line = sma
                
                curr_l, prev_l = line.iloc[-1], line.iloc[-2]

                match = False
                if "Cross Up" in price_cond: match = pp < prev_l and cp > curr_l
                elif "Cross Down" in price_cond: match = pp > prev_l and cp < curr_l
                elif "Atas" in price_cond: match = cp > curr_l
                elif "Bawah" in price_cond: match = cp < curr_l

                if match:
                    res = {"Pair": symbol, "Harga": cp, "Nilai Ind": round(curr_l, 4)}
                    
                    # Data Harian untuk Performance 1d, 1w, 1M
                    rd = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Day1", timeout=5).json()
                    df_d = pd.DataFrame({'close': [float(x) for x in rd['data']['close']]})
                    
                    if "1h" in show_perf: 
                        r_1h = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Min60", timeout=5).json()
                        df_1h = pd.DataFrame({'close': [float(x) for x in r_1h['data']['close']]})
                        res["1h %"] = get_pct(cp, df_1h['close'].iloc[-2] if len(df_1h)>1 else cp)
                    
                    # 4h Performance
                    if "4h" in show_perf:
                        r_4h = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Min240", timeout=5).json()
                        df_4h = pd.DataFrame({'close': [float(x) for x in r_4h['data']['close']]})
                        res["4h %"] = get_pct(cp, df_4h['close'].iloc[-2] if len(df_4h)>1 else cp)

                    if "1d" in show_perf: res["1d %"] = get_pct(cp, df_d['close'].iloc[-2] if len(df_d)>1 else cp)
                    if "1w" in show_perf: res["1w %"] = get_pct(cp, df_d['close'].iloc[-8] if len(df_d)>7 else df_d['close'].iloc[0])
                    if "1M" in show_perf: res["1M %"] = get_pct(cp, df_d['close'].iloc[0])

                    res["Chart"] = f"https://www.tradingview.com/chart/?symbol=MEXC:{symbol.replace('_', '')}.P"
                    found.append(res)
            except: continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            st.dataframe(
                pd.DataFrame(found), 
                column_config={
                    "Chart": st.column_config.LinkColumn("Buka TradingView"),
                    "1h %": st.column_config.NumberColumn(format="%.2f%%"),
                    "4h %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1d %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1w %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1M %": st.column_config.NumberColumn(format="%.2f%%"),
                }, 
                hide_index=True
            )
        else:
            st.warning("Tidak ada koin yang sesuai kriteria.")
    except:
        st.error("Gagal koneksi server.")

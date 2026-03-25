import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MEXC Ultimate Radar", layout="wide")
st.title("🛰️ MEXC Pro Radar & Performance")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("🔍 Konfigurasi Scan")
tf = st.sidebar.selectbox("1. Timeframe Indikator", ["Min1", "Min5", "Min15", "Min60", "Day1"])
ind_type = st.sidebar.selectbox("2. Pilih Indikator", ["EMA", "RSI", "Bollinger Bands"])
period = st.sidebar.number_input("3. Periode Indikator", value=20)

st.sidebar.header("⚡ Kondisi Sinyal")
cond = st.sidebar.selectbox("Pilih Kondisi", [
    "Above (Di Atas)", 
    "Below (Di Bawah)", 
    "Cross Up (Memotong ke Atas)", 
    "Cross Down (Memotong ke Bawah)"
])

# --- FUNGSI HITUNG CHANGE % ---
def get_change(current, previous):
    if previous == 0: return 0
    return round(((current - previous) / previous) * 100, 2)

if st.sidebar.button("🚀 JALANKAN SCAN"):
    st.info(f"Memindai Market {tf}...")
    try:
        r_t = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        tickers = r_t['data'][:50] 
        found = []

        for t in tickers:
            symbol = t['symbol']
            tv_url = f"https://www.tradingview.com/chart/?symbol=MEXC:{symbol.replace('_', '')}.P"

            try:
                # Ambil data kline (untuk indikator)
                rk = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in rk['data']['close']]})
                
                # Ambil data kline tambahan untuk Performance (Harian, Mingguan, Bulanan)
                # Catatan: Kita ambil TF Day1 untuk menghitung % harian/mingguan/bulanan
                r_day = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Day1", timeout=5).json()
                df_day = pd.DataFrame({'close': [float(x) for x in r_day['data']['close']]})

                if len(df) < period + 5 or len(df_day) < 30: continue

                cp, pp = df['close'].iloc[-1], df['close'].iloc[-2]
                
                # Hitung Indikator
                if ind_type == "EMA":
                    line = df['close'].ewm(span=period, adjust=False).mean()
                elif ind_type == "RSI":
                    delta = df['close'].diff()
                    g, l = delta.where(delta > 0, 0), -delta.where(delta < 0, 0)
                    line = 100 - (100 / (1 + (g.rolling(period).mean() / l.rolling(period).mean())))
                else:
                    line = df['close'].rolling(period).mean()
                
                curr_l, prev_l = line.iloc[-1], line.iloc[-2]

                # Logika Filter
                match = False
                if "Above" in cond: match = cp > curr_l
                elif "Below" in cond: match = cp < curr_l
                elif "Cross Up" in cond: match = pp < prev_l and cp > curr_l
                elif "Cross Down" in cond: match = pp > prev_l and cp < curr_l

                if match:
                    # Hitung Persentase (Estimasi dari data Kline)
                    ch_1h = get_change(cp, df['close'].iloc[-2] if len(df)>1 else cp)
                    ch_1d = get_change(cp, df_day['close'].iloc[-2])
                    ch_1w = get_change(cp, df_day['close'].iloc[-8] if len(df_day)>7 else df_day['close'].iloc[0])
                    ch_1m = get_change(cp, df_day['close'].iloc[0])

                    found.append({
                        "Pair": symbol,
                        "Harga": cp,
                        "1h %": ch_1h,
                        "1d %": ch_1d,
                        "1w %": ch_1w,
                        "1M %": ch_1m,
                        "Nilai Ind": round(curr_l, 4),
                        "Chart": tv_url
                    })
            except: continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            # Tampilkan tabel dengan sorting dan warna
            df_final = pd.DataFrame(found)
            st.dataframe(
                df_final,
                column_config={
                    "Chart": st.column_config.LinkColumn("TradingView"),
                    "1h %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1d %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1w %": st.column_config.NumberColumn(format="%.2f%%"),
                    "1M %": st.column_config.NumberColumn(format="%.2f%%"),
                },
                hide_index=True
            )
        else:
            st.warning("Tidak ada koin yang cocok.")
    except:
        st.error("Gagal koneksi.")

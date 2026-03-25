import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MEXC Pro Radar", layout="wide")
st.title("🛰️ MEXC Futures Pro Radar")

# --- SIDEBAR SETTING ---
st.sidebar.header("🔍 Filter Indikator")
tf = st.sidebar.selectbox("Timeframe", ["Min1", "Min5", "Min15", "Min60", "Day1"])
ind_type = st.sidebar.selectbox("Pilih Indikator", ["EMA", "RSI", "Bollinger Bands"])
period = st.sidebar.number_input("Periode", value=20)

st.sidebar.header("⚡ Kondisi Sinyal")
if ind_type == "EMA":
    cond = st.sidebar.selectbox("Kondisi EMA", ["Harga di Atas EMA", "Harga di Bawah EMA", "Cross Up EMA", "Cross Down EMA"])
elif ind_type == "RSI":
    cond = st.sidebar.selectbox("Kondisi RSI", ["Overbought (>70)", "Oversold (<30)", "RSI Naik", "RSI Turun"])
else:
    cond = st.sidebar.selectbox("Kondisi BB", ["Sentuh Upper Band", "Sentuh Lower Band", "Harga di Tengah (Mid)"])

if st.sidebar.button("🚀 JALANKAN SCAN"):
    st.info(f"Memindai Market {tf} dengan {ind_type}...")
    try:
        # Ambil Top 50 Koin Futures
        r_t = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
        tickers = r_t['data'][:50] 
        found = []

        for t in tickers:
            symbol = t['symbol'] # Format: BTC_USDT
            # Buat Link TradingView (Format: MEXC:BTCUSDT.P)
            tv_symbol = symbol.replace("_", "") + ".P"
            tv_url = f"https://www.tradingview.com/chart/?symbol=MEXC:{tv_symbol}"

            try:
                r = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=5).json()
                df = pd.DataFrame({'close': [float(x) for x in r['data']['close']]})
                if len(df) < period + 5: continue

                cp = df['close'].iloc[-1] 
                pp = df['close'].iloc[-2] 

                match = False
                val_display = ""

                # --- LOGIKA EMA ---
                if ind_type == "EMA":
                    ema = df['close'].ewm(span=period, adjust=False).mean()
                    curr_ema, prev_ema = ema.iloc[-1], ema.iloc[-2]
                    val_display = round(curr_ema, 4)
                    if cond == "Harga di Atas EMA": match = cp > curr_ema
                    elif cond == "Harga di Bawah EMA": match = cp < curr_ema
                    elif cond == "Cross Up EMA": match = pp < prev_ema and cp > curr_ema
                    elif cond == "Cross Down EMA": match = pp > prev_ema and cp < curr_ema

                # --- LOGIKA RSI ---
                elif ind_type == "RSI":
                    delta = df['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rsi = 100 - (100 / (1 + (gain / loss)))
                    curr_rsi = rsi.iloc[-1]
                    val_display = round(curr_rsi, 2)
                    if cond == "Overbought (>70)": match = curr_rsi > 70
                    elif cond == "Oversold (<30)": match = curr_rsi < 30
                    elif cond == "RSI Naik": match = curr_rsi > rsi.iloc[-2]
                    elif cond == "RSI Turun": match = curr_rsi < rsi.iloc[-2]

                # --- LOGIKA BB ---
                elif ind_type == "Bollinger Bands":
                    sma = df['close'].rolling(window=period).mean()
                    std = df['close'].rolling(window=period).std()
                    upper, lower = sma + (2 * std), sma - (2 * std)
                    val_display = f"M:{round(sma.iloc[-1], 2)}"
                    if cond == "Sentuh Upper Band": match = cp >= upper.iloc[-1]
                    elif cond == "Sentuh Lower Band": match = cp <= lower.iloc[-1]
                    elif cond == "Harga di Tengah (Mid)": match = lower.iloc[-1] < cp < upper.iloc[-1]

                if match:
                    found.append({
                        "Pair": symbol, 
                        "Harga": cp, 
                        "Indikator": val_display,
                        "TradingView": tv_url
                    })
            except: continue

        if found:
            st.success(f"Ditemukan {len(found)} koin!")
            # Tampilkan tabel dengan link yang bisa diklik
            st.dataframe(
                pd.DataFrame(found),
                column_config={
                    "TradingView": st.column_config.LinkColumn("Buka Chart")
                }
            )
        else:
            st.warning("Tidak ada koin yang cocok.")
    except:
        st.error("Gagal koneksi.")

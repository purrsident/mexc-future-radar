if st.sidebar.button("🚀 JALANKAN SCAN"):
    with st.spinner("Memindai Market... Mohon tunggu"):
        try:
            # Mengambil data ticker terbaru dari MEXC
            r_t = requests.get("https://contract.mexc.com/api/v1/contract/ticker").json()
            tickers = r_t['data'][:40] # Dibatasi 40 koin biar tidak berat di iPhone
            found = []

            for t in tickers:
                symbol = t['symbol']
                try:
                    # Ambil data kline sesuai timeframe pilihan
                    rk = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={tf}", timeout=3).json()
                    df = pd.DataFrame({'close': [float(x) for x in rk['data']['close']]})
                    if len(df) < target_period + 2: continue

                    cp, pp = df['close'].iloc[-1], df['close'].iloc[-2]
                    
                    # Hitung Indikator (EMA atau BB)
                    if ind_type == "EMA":
                        line = df['close'].ewm(span=target_period, adjust=False).mean()
                    else:
                        sma = df['close'].rolling(target_period).mean()
                        std = df['close'].rolling(target_period).std()
                        if "Upper" in bb_part: line = sma + (2 * std)
                        elif "Lower" in bb_part: line = sma - (2 * std)
                        else: line = sma
                    
                    curr_l, prev_l = line.iloc[-1], line.iloc[-2]

                    # Logika Pencocokan Sinyal
                    match = False
                    if "Cross Up" in price_cond: match = pp < prev_l and cp > curr_l
                    elif "Cross Down" in price_cond: match = pp > prev_l and cp < curr_l
                    elif "Atas" in price_cond: match = cp > curr_l
                    elif "Bawah" in price_cond: match = cp < curr_l

                    if match:
                        # Langsung masukkan data dasar dulu agar hasil cepat muncul
                        res = {"Pair": symbol, "Harga": cp, "Indikator": round(curr_l, 4)}
                        
                        # Data Performance (Ambil Day1 hanya jika dibutuhkan)
                        if show_perf:
                            rd = requests.get(f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=Day1", timeout=3).json()
                            df_d = pd.DataFrame({'close': [float(x) for x in rd['data']['close']]})
                            if "1h" in show_perf: res["1h %"] = get_pct(cp, df['close'].iloc[-2] if len(df)>1 else cp)
                            if "1d" in show_perf: res["1d %"] = get_pct(cp, df_d['close'].iloc[-2] if len(df_d)>1 else cp)
                            if "1w" in show_perf: res["1w %"] = get_pct(cp, df_d['close'].iloc[-8] if len(df_d)>7 else df_d['close'].iloc[0])
                            if "1M" in show_perf: res["1M %"] = get_pct(cp, df_d['close'].iloc[0])

                        res["Chart"] = f"https://www.tradingview.com/chart/?symbol=MEXC:{symbol.replace('_', '')}.P"
                        found.append(res)
                except: continue

            if found:
                st.success(f"Ditemukan {len(found)} koin!")
                st.dataframe(pd.DataFrame(found), column_config={"Chart": st.column_config.LinkColumn("Buka TV")}, hide_index=True)
            else:
                st.warning("Tidak ada koin yang sesuai kriteria saat ini. Coba ganti Timeframe atau Indikator.")
        except Exception as e:
            st.error(f"Gagal koneksi: {e}")

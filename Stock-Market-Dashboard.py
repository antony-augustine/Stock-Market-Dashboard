import streamlit as st
import pandas as pd
import yfinance as yf
# import requests
# import time
# import random
# from io import StringIO
# from concurrent.futures import ThreadPoolExecutor
# import pytz
# from datetime import datetime, time
# import plotly.graph_objects as go

import ta
import matplotlib.pyplot as plt

# --- PAGE CONFIG ---
st.set_page_config(page_title="📊 S&P 500 Stock Market Dashboard", layout="wide")
#st.header("📊 Stock Market Dashboard")
sp500 = pd.read_csv("D:/Py/SP500_SYMBOL_LIST.csv") 
# --- SIDEBAR INPUT ---

col1, col2, col3, col4, col5   = st.columns(([1.25,0.5,0.5,0.5,0.5]))
 
   
with col1: 
    st.info("""
            ### 📊 Stock Market Trend Dashboard 
""")

with col2: 
    

    sym_list = sorted(sp500["Ticker"].dropna().unique())
 
    selected_sym = st.selectbox("Select Symbol:", sym_list)
    
    
with col3: period = st.selectbox("Select Time Period", ["1y", "1mo", "3mo", "6mo", "2y", "5y"])
with col4: interval = st.selectbox("Select Interval", ["1d", "1h"])
with col5: pe_Sym_input = st.text_input("Enter Stock Symbol (optional)") 


    
vsecurity_name = "x" 
pe_Sym = pe_Sym_input.strip() or selected_sym
# --- FETCH DATA ---
try:
    data = yf.download(pe_Sym, period=period, interval=interval, auto_adjust=False)
    ticker = yf.Ticker(pe_Sym)
     

    info = ticker.info  # avoid multiple API calls

    security_name = info.get("longName", info.get("shortName", "Name Not Available"))
    sector = info.get("sector", "Sector Not Available")
    industry = info.get("industry", "Industry Not Available")

    # --- CLEAN COLUMN NAMES ---
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # --- ENSURE ALL COLUMNS ARE 1D ---
    for col in data.columns:
        if isinstance(data[col], pd.DataFrame):
            data[col] = data[col].squeeze()

    if data.empty:
        st.warning("⚠️ No data found for this ticker or interval.")
        st.stop()
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

vsecurity_name = vsecurity_name

col1, col2 = st.columns(([2.5,4]))
 
   
with col1: 
    st.info("""             
This dashboard combines **RSI Trend Zones** with **EMA-based price trend**  
to identify overall market strength and momentum direction.
""")

with col2:
     
    col1, col2, col3 = st.columns([1,1,1])
   
    col1.markdown(f"""
    <div style='background:white;padding:5px;border-radius:12px;
                text-align:center;border:1px solid #444;'>
        <div style='font-size:16px;color:#aaa;'>Security</div>
        <div style='font-size:14px;font-weight:700;color:#1F597F;'>{security_name}</div>
    </div>
    """, unsafe_allow_html=True)
    col2.markdown(f"""
    <div style='background:white;padding:5px;border-radius:12px;
                text-align:center;border:1px solid #444;'>
        <div style='font-size:16px;color:#aaa;'>Sector</div>
        <div style='font-size:14px;font-weight:700;color:#1F597F;'>{sector}</div>
    </div>
    """, unsafe_allow_html=True)
    col3.markdown(f"""
    <div style='background:white;padding:5px;border-radius:12px;
                text-align:center;border:1px solid #444;'>
        <div style='font-size:16px;color:#aaa;'>Industry</div>
        <div style='font-size:14px;font-weight:700;color:#1F597F;'>{industry}</div>
    </div>
    """, unsafe_allow_html=True)

     
 # --- CALCULATE INDICATORS ---
# Ensure 'Close' is a 1D Series
close_series = data["Close"].squeeze()

data["EMA_20"] = ta.trend.ema_indicator(close_series, window=20)
data["EMA_50"] = ta.trend.ema_indicator(close_series, window=50)
data["RSI_14"] = ta.momentum.RSIIndicator(close_series, window=14).rsi()


# --- METRICS ---
latest = data.iloc[-1]
prev = data.iloc[-2]

# Convert any 1-element Series to scalar values
price = float(latest["Close"])
prev_price = float(prev["Close"])
change = price - prev_price
pct_change = (change / prev_price) * 100
volume = int(latest["Volume"])
rsi_value = float(latest["RSI_14"])

ema_pct_change20 = ((float(latest["EMA_20"])-float(prev["EMA_20"])) / float(prev["EMA_20"])) * 100
ema_pct_change50 = ((float(latest["EMA_50"])-float(prev["EMA_50"])) / float(prev["EMA_50"])) * 100
rsi_change14 = (float(latest["RSI_14"])-float(prev["RSI_14"]))  

# -------------------------------
# 4. Detect Price Trend using EMA20/EMA50 cross and slope
# -------------------------------
def price_trend(row):
    if row["EMA_20"] > row["EMA_50"]:
        return "Uptrend"
    else:
        return "Downtrend"

data["Price_Trend"] = data.apply(price_trend, axis=1)
# -------------------------------
# 2. Calculate RSI (14)
# -------------------------------
 
# -------------------------------
# 3. Detect RSI Trend Zones
# -------------------------------
def rsi_zone(rsi):
    if rsi >= 60:
        return "Strong Bullish Zone (RSI ≥ 60)"
    elif 50 <= rsi < 60:
        return "Moderate Bullish Momentum"
    elif 40 <= rsi < 50:
        return "Bullish Support Zone (RSI 40–50)"
    elif 20 <= rsi < 40:
        return "Bearish Zone (RSI 20–40)"
    else:
        return "Extreme Bearish Zone (RSI < 20)"

# Apply detection
data["RSI_Zone"] = data["RSI_14"].apply(rsi_zone)

# -------------------------------
# 4. Print latest RSI trend zone
# -------------------------------
latest_rsi = data["RSI_14"].iloc[-1]
latest_zone = data["RSI_Zone"].iloc[-1]

print("Latest RSI:", round(latest_rsi, 2))
print("RSI Trend Zone:", latest_zone)


# -------------------------------
# 5. Combine RSI Trend + Price Trend
# -------------------------------
def combined_signal(row):
    trend = row["Price_Trend"]
    rsi = row["RSI_14"]

    # Strong Uptrend
    if trend == "Uptrend" and rsi > 60:
        return "Strong Uptrend (Price rising + RSI momentum strong)"

    # Weak Uptrend
    if trend == "Uptrend" and 50 < rsi <= 60:
        return "Weak Uptrend (Price rising but RSI moderate)"

    # Trend losing strength
    if trend == "Uptrend" and rsi < 50:
        return "Uptrend weakening (RSI losing momentum)"

    # Strong Downtrend
    if trend == "Downtrend" and rsi < 40:
        return "Strong Downtrend (Price falling + RSI weak)"

    # Weak Downtrend
    if trend == "Downtrend" and 40 <= rsi < 50:
        return "Weak Downtrend (Price falling but RSI stabilizing)"

    # Downtrend weakening
    if trend == "Downtrend" and rsi > 50:
        return "Downtrend weakening (RSI turning bullish)"

    return "Neutral"

data["Combined_Signal"] = data.apply(combined_signal, axis=1)

Combined_Signal= data["Combined_Signal"].iloc[-1]





def ema_trend(pct_change):
    if pct_change > 0.2:
        return "Strong Uptrend"
    elif pct_change > 0:
        return "Mild Uptrend"
    elif pct_change > -0.2:
        return "Mild Downtrend"
    else:
        return "Strong Downtrend"
    
trend20 = ema_trend(ema_pct_change20)
trend50 = ema_trend(ema_pct_change50)

def ema_score(trend):
    if "Strong Up" in trend: return 2
    if "Mild Up" in trend:   return 1
    if "Mild Down" in trend: return -1
    return -2

alignment_score = ema_score(trend20) + ema_score(trend50)
 
 
#data["alignment_score"] = data.apply(alignment_score, axis=1)

#C_alignment_score= data["alignment_score"].iloc[-1]

#def alignment_score(row):
#    return ema_score(row["trend20"]) + ema_score(row["trend50"])

#data["alignment_score"] = data.apply(alignment_score, axis=1)

#C_alignment_score = data["alignment_score"].iloc[-1]



if alignment_score >= 3:
    market_signal = "🚀 Strong Bullish"
elif alignment_score == 2:
    market_signal = "📈 Bullish"
elif alignment_score == 1:
    market_signal = "⚠️ Mild Bullish"
elif alignment_score == 0:
    market_signal = "➖ Neutral"
elif alignment_score == -1:
    market_signal = "⚠️ Mild Bearish"
elif alignment_score == -2:
    market_signal = "📉 Bearish"
else:
    market_signal = "🔥 Strong Bearish"

 

col1, col2, col3, col4, col5, col6 = st.columns([0.75,1.25,0.75,0.75,0.75,1.75])
col1.metric("Current Price", f"${price:.2f}", f"{pct_change:.2f}%")
#col2.metric("Volume", f"{volume:,}")
#col2.markdown(f"""
#<div style='background:#1e1e1e;padding:15px;border-radius:12px;
#            text-align:center;border:1px solid #444;'>
#    <div style='font-size:16px;color:#aaa;'>RSI (14)</div>
#    <div style='font-size:34px;font-weight:700;color:white;'>{rsi_value:.2f}</div>
#</div>
#""", unsafe_allow_html=True)

col2.metric("RSI (14)", f"{rsi_value:.2f}", f"{rsi_change14:.1f} | {latest_zone}")
col3.metric("EMA (20)", f"{float(latest["EMA_20"]):.1f}", f"{ema_pct_change20:.1f}% | {trend20}")
col4.metric("EMA (50)", f"{float(latest["EMA_50"]):.1f}", f"{ema_pct_change50:.1f}% | {trend50}") 
col5.metric("EMA Signal", f"Score: {alignment_score:.0f}", f"{alignment_score:.0f} | {market_signal}")
col6.metric("RSI Trend + Price Trend Combination", f"{market_signal}", f"{alignment_score:.0f} | {Combined_Signal}")
# --- PRICE CHART ---

st.subheader("📉 Price Chart with EMA")
import matplotlib.dates as mdates
# --- Create Matplotlib Figure ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(data.index, data["Close"], label="Close Price", color="blue", linewidth=1)
ax.plot(data.index, data["EMA_20"], label="EMA 20", color="orange", linestyle="-", linewidth=1)
ax.plot(data.index, data["EMA_50"], label="EMA 50", color="green", linestyle="-", linewidth=1)

# --- Formatting ---
ax.legend(loc="best", frameon=False)
ax.set_xlabel("Date")
ax.set_ylabel("Price ($)")
ax.set_title("Price vs EMA Trend", fontsize=12, fontweight="bold")
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
fig.autofmt_xdate()
fig.tight_layout()

 


# --- Display in Streamlit ---
     
st.plotly_chart(fig, use_container_width=True)
 
st.markdown("""
### 📊 Market Trend Dashboard

This dashboard analyzes market strength using **RSI momentum** and **EMA trend direction**.  
- RSI values are classified into key **trend zones** (Bullish, Neutral, Bearish).  
- EMA20 and EMA50 determine the overall **price trend**.  
- By combining both indicators, the system generates signals like  
  **Strong Uptrend**, **Weak Uptrend**, **Strong Downtrend**,  
  or **Trend Weakening**.

Use these signals to quickly understand **momentum**, **trend strength**, and **potential market reversals**.
""")
 
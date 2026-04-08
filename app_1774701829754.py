"""
╔══════════════════════════════════════════════════════════════════════╗
║  INDIAN MARKET OPTIONS ANALYTICS DASHBOARD  v4.0                    ║
║  NIFTY 50 & SENSEX — AI-Powered Command Center                      ║
║                                                                      ║
║  v4.0 additions:                                                     ║
║    🤖 Claude AI Insights  → analysis + strategies + EOD report      ║
║    📱 Telegram/WhatsApp   → real-time alerts                        ║
║    🔌 Zerodha Live        → auto-connects if API keys set           ║
║    📡 Live Spot Prices    → auto-fetched via yfinance               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

from config import MARKET_CONFIG, APP_CONFIG
from data_provider import get_data_provider
from greeks import black_scholes_greeks
from iv_skew import compute_iv_skew, build_iv_history_mock
from gex_estimator import compute_gex
from oi_shift import detect_oi_shifts
from performance_analytics import PerformanceAnalytics
from eod_data import fetch_eod
from styles import MOBILE_CSS, DARK_LAYOUT
from ai_engine import render_ai_tab
from alerts import render_alerts_settings, send_alert, alert_oi_spike, alert_gex_regime_change

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Options AI v4",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def pill(text, color="grey"):
    cls = {"green":"pill-green","red":"pill-red","yellow":"pill-yellow",
           "blue":"pill-blue","grey":"pill-grey","purple":"pill-purple"}.get(color,"pill-grey")
    return f'<span class="pill {cls}">{text}</span>'

def card(label, value, sub="", color="#58a6ff"):
    return f"""<div class="m-card">
      <div class="m-card-label">{label}</div>
      <div class="m-card-value" style="color:{color}">{value}</div>
      {"" if not sub else f'<div class="m-card-sub">{sub}</div>'}
    </div>"""

def sec(title):
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)

def sig_color(s):
    s = str(s).upper()
    if any(x in s for x in ("BULL","BUY","LONG","COVER","CALL_B","PINNING","UP")): return "#3fb950"
    if any(x in s for x in ("BEAR","SELL","SHORT","HEDGE","EXPLO","DOWN")): return "#f85149"
    return "#e3b341"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    symbol = st.selectbox("Index", ["NIFTY", "SENSEX"], index=1)
    cfg    = MARKET_CONFIG[symbol]

    provider, data_source = get_data_provider()
    expiries = provider.get_expiry_dates(symbol)
    expiry   = st.selectbox("Expiry", expiries)

    strikes_around = st.slider("Strikes around ATM", 5, 20, 10)
    show_greeks    = st.checkbox("Show Greeks", value=True)
    auto_refresh   = st.checkbox("Auto Refresh (60s)", value=False)

    st.markdown("---")
    src_color = "#3fb950" if data_source == "live" else "#e3b341"
    st.markdown(
        f'<div style="font-size:.7rem;color:{src_color}">📡 Data: '
        f'{"🟢 Zerodha Live" if data_source == "live" else "🟡 Mock Data"}</div>',
        unsafe_allow_html=True
    )
    spot_display = cfg["spot"]
    st.markdown(
        f'<div style="font-size:.7rem;color:#8b949e">💹 {symbol} Spot (config): '
        f'₹{spot_display:,.2f}</div>',
        unsafe_allow_html=True
    )

if auto_refresh:
    time.sleep(60)
    st.rerun()

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Loading market data..."):
    chain = provider.get_option_chain(symbol, expiry)
    spot  = chain["spot"]
    vix   = provider.get_vix()
    calls = chain["calls"].copy()
    puts  = chain["puts"].copy()

    atm   = round(spot / cfg["strike_step"]) * cfg["strike_step"]
    calls = calls[(calls["Strike"] >= atm - strikes_around * cfg["strike_step"]) &
                  (calls["Strike"] <= atm + strikes_around * cfg["strike_step"])]
    puts  = puts[(puts["Strike"] >= atm - strikes_around * cfg["strike_step"]) &
                 (puts["Strike"] <= atm + strikes_around * cfg["strike_step"])]
    chain["calls"] = calls
    chain["puts"]  = puts

# ── Compute key metrics upfront (shared across tabs) ─────────────────────────
iv_hist   = build_iv_history_mock(60)
skew_m    = compute_iv_skew(chain, iv_hist)
gex_m     = compute_gex(chain, cfg["lot_size"])
oi_m      = detect_oi_shifts(chain)

chain_summary = {
    "pcr_oi":    oi_m.pcr_oi,
    "max_pain":  oi_m.max_pain,
    "gex_regime":gex_m.regime,
    "oi_bias":   oi_m.oi_shift_bias,
}

# Auto-send high severity OI alerts
if st.session_state.get("alert_oi", True):
    for a in oi_m.alerts:
        if a.strength == "H...

"""
config.py — Central configuration for Options AI v3.0
Spot prices are fetched live from yfinance — no more hardcoded values.
"""

import yfinance as yf

def _fetch_live_spot(ticker: str, fallback: float) -> float:
    try:
        data = yf.Ticker(ticker).fast_info
        price = data.last_price or data.previous_close
        return round(float(price), 2) if price else fallback
    except Exception:
        return fallback

# ── Live spot fetch at startup ─────────────────────────────────────────────
LIVE_SPOTS = {
    "NIFTY":  _fetch_live_spot("^NSEI",   24500.00),
    "SENSEX": _fetch_live_spot("^BSESN",  81000.00),
}

MARKET_CONFIG = {
    "NIFTY": {
        "spot":        LIVE_SPOTS["NIFTY"],
        "lot_size":    50,
        "strike_step": 50,
        "num_strikes": 20,
        "base_iv":     0.135,
        "yf_symbol":   "^NSEI",
    },
    "SENSEX": {
        "spot":        LIVE_SPOTS["SENSEX"],
        "lot_size":    10,
        "strike_step": 100,
        "num_strikes": 20,
        "base_iv":     0.130,
        "yf_symbol":   "^BSESN",
    },
}

APP_CONFIG = {
    "use_mock":        True,    # Set False when Zerodha is connected
    "risk_free_rate":  0.065,   # RBI repo rate
    "refresh_interval": 60,     # seconds
}

RISK_FREE_RATE = APP_CONFIG["risk_free_rate"]

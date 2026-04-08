"""
data_provider.py — Smart provider switcher.
Automatically uses Zerodha live data if credentials are set,
otherwise falls back to MockDataProvider gracefully.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import MARKET_CONFIG, RISK_FREE_RATE
from greeks import black_scholes_greeks


class MockDataProvider:
    def get_expiry_dates(self, symbol: str) -> list:
        today = datetime.today()
        expiries = []
        d = today
        while len(expiries) < 4:
            d += timedelta(days=1)
            if d.weekday() == 3:
                expiries.append(d.strftime("%d-%b-%Y").upper())
        return expiries

    def get_spot_price(self, symbol: str) -> float:
        cfg = MARKET_CONFIG[symbol]
        return round(cfg["spot"] + np.random.normal(0, cfg["spot"] * 0.001), 2)

    def get_vix(self) -> float:
        return round(np.random.uniform(12.5, 18.5), 2)

    def get_option_chain(self, symbol: str, expiry: str) -> dict:
        cfg  = MARKET_CONFIG[symbol]
        spot = self.get_spot_price(symbol)
        step = cfg["strike_step"]
        atm  = round(spot / step) * step
        strikes = [atm + (i - cfg["num_strikes"]) * step
                   for i in range(cfg["num_strikes"] * 2 + 1)]

        try:
            exp_date = datetime.strptime(expiry, "%d-%b-%Y")
        except Exception:
            exp_date = datetime.today() + timedelta(days=7)
        T = max((exp_date - datetime.today()).days / 365, 1/365)

        calls, puts = [], []
        for K in strikes:
            moneyness = (spot - K) / spot
            skew      = abs(moneyness) * 0.3
            call_iv   = max(0.05, min(cfg["base_iv"] + skew + np.random.normal(0, 0.005), 0.80))
            put_iv    = max(0.05, min(cfg["base_iv"] + skew*1.1 + np.random.normal(0, 0.005), 0.80))

            cg = black_scholes_greeks(spot, K, T, RISK_FREE_RATE, call_iv, "call")
            pg = black_scholes_greeks(spot, K, T, RISK_FREE_RATE, put_iv, "put")

            oi_scale     = np.exp(-0.5 * (moneyness / 0.02) ** 2)
            base_call_oi = int(np.random.uniform(50_000, 800_000) * oi_scale * cfg["lot_size"])
            base_put_oi  = int(np.random.uniform(50_000, 900_000) * oi_scale * cfg["lot_size"])
            call_oi_chg  = int(np.random.normal(0, base_call_oi * 0.08))
            put_oi_chg   = int(np.random.normal(0, base_put_oi  * 0.09))
            call_vol     = max(0, int(abs(call_oi_chg) * np.random.uniform(0.8, 2.5)))
            put_vol      = max(0, int(abs(put_oi_chg)  * np.random.uniform(0.8, 2.5)))
            call_ltp     = max(0.05, cg["price"] * np.random.uniform(0.97, 1.03))
            put_ltp      = max(0.05, pg["price"] * np.random.uniform(0.97, 1.03))

            calls.append({"Strike":K,"LTP":round(call_ltp,2),"OI":base_call_oi,
                          "Chg OI":call_oi_chg,"Volume":call_vol,"IV":round(call_iv*100,2),
                          "Delta":cg["delta"],"Gamma":cg["gamma"],"Theta":cg["theta"],"Vega":cg["vega"],
                          "Bid":round(call_ltp*0.995,2),"Ask":round(call_ltp*1.005,2)})
            puts.append({"Strike":K,"LTP":round(put_ltp,2),"OI":base_put_oi,
                         "Chg OI":put_oi_chg,"Volume":put_vol,"IV":round(put_iv*100,2),
                         "Delta":pg["delta"],"Gamma":pg["gamma"],"Theta":pg["theta"],"Vega":pg["vega"],
                         "Bid":round(put_ltp*0.995,2),"Ask":round(put_ltp*1.005,2)})

        return {"calls":pd.DataFrame(calls),"puts":pd.DataFrame(puts),
                "spot":spot,"expiry":expiry,
                "timestamp":datetime.now().strftime("%H:%M:%S")}


def get_data_provider():
    """
    Auto-selects provider:
      - If KITE_API_KEY + KITE_ACCESS_TOKEN are set → ZerodhaAdapter (live)
      - Otherwise → MockDataProvider (demo)
    """
    api_key   = os.getenv("KITE_API_KEY", "")
    api_token = os.getenv("KITE_ACCESS_TOKEN", "")

    if api_key and api_token:
        try:
            from zerodha_adapter import ZerodhaAdapter
            provider = ZerodhaAdapter()
            return provider, "live"
        except Exception as e:
            import streamlit as st
            st.warning(f"⚠️ Zerodha connection failed: {e}. Falling back to mock data.")
            return MockDataProvider(), "mock"

    return MockDataProvider(), "mock"

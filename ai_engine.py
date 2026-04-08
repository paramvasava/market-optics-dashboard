"""
ai_engine.py — Claude AI Insights Engine
==========================================
Uses Anthropic Claude to generate:
  - Market regime analysis
  - Options strategy recommendations
  - Risk assessment
  - EOD summary reports
  - IV/GEX/OI interpretation

Setup:
  Set ANTHROPIC_API_KEY in Replit Secrets.
"""

import os
import json
import anthropic
import streamlit as st
import pandas as pd
from datetime import datetime


def _get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def get_claude_analysis(
    symbol: str,
    spot: float,
    vix: float,
    pcr: float,
    atm_iv: float,
    skew_signal: str,
    gex_regime: str,
    oi_bias: str,
    max_pain: float,
    trend_signal: str,
    rsi: float,
    extra_context: str = "",
) -> str:
    """
    Send market snapshot to Claude and get a structured analysis.
    Returns markdown-formatted string.
    """
    client = _get_client()
    if not client:
        return "_⚠️ ANTHROPIC_API_KEY not set. Add it in Replit Secrets to enable AI insights._"

    prompt = f"""You are an expert Indian options market analyst. Analyze this real-time market snapshot and provide actionable insights.

## Market Snapshot — {symbol} — {datetime.now().strftime('%d %b %Y %H:%M IST')}

| Metric | Value |
|--------|-------|
| Spot Price | ₹{spot:,.2f} |
| India VIX | {vix:.2f} |
| PCR (OI) | {pcr:.2f} |
| ATM IV | {atm_iv:.1f}% |
| IV Skew Signal | {skew_signal} |
| GEX Regime | {gex_regime} |
| OI Bias | {oi_bias} |
| Max Pain | ₹{max_pain:,.0f} |
| Trend (EMA) | {trend_signal} |
| RSI | {rsi:.1f} |

{f"Additional context: {extra_context}" if extra_context else ""}

Please provide:

1. **Market Regime** (2-3 sentences on current market character)
2. **Key Levels** (support, resistance, max pain significance)
3. **Options Strategy** (1-2 specific strategies suited for current conditions, with strikes if possible)
4. **Risk Factors** (what could invalidate this view)
5. **Bias** (one word: BULLISH / BEARISH / NEUTRAL + confidence %)

Keep it concise, practical, and specific to Indian options market structure (weekly expiries, lot sizes). No generic advice."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"_⚠️ Claude API error: {e}_"


def get_eod_report(
    symbol: str,
    eod_df: pd.DataFrame,
    chain_summary: dict,
) -> str:
    """Generate end-of-day summary report using Claude."""
    client = _get_client()
    if not client:
        return "_⚠️ ANTHROPIC_API_KEY not set._"

    if eod_df.empty:
        return "_No EOD data available for report generation._"

    latest = eod_df.iloc[-1]
    prev   = eod_df.iloc[-2] if len(eod_df) > 1 else latest

    daily_chg     = float(latest["Close"] - prev["Close"])
    daily_chg_pct = float(daily_chg / prev["Close"] * 100)

    prompt = f"""Generate a professional EOD market report for {symbol} for {datetime.now().strftime('%d %b %Y')}.

## EOD Data
- Close: ₹{latest['Close']:,.2f} ({daily_chg:+.2f}, {daily_chg_pct:+.2f}%)
- RSI(14): {latest.get('RSI', 'N/A'):.1f}
- MACD: {latest.get('MACD', 0):.2f} vs Signal {latest.get('MACD_Signal', 0):.2f}
- ATR: {latest.get('ATR', 0):.2f}
- HV20: {latest.get('HV_20', 0):.1f}%
- Trend: {latest.get('Trend_Signal', 'N/A')}
- BB Upper: {latest.get('BB_Upper', 0):,.2f} | Lower: {latest.get('BB_Lower', 0):,.2f}

## Options Summary
- PCR OI: {chain_summary.get('pcr_oi', 'N/A')}
- Max Pain: ₹{chain_summary.get('max_pain', 0):,.0f}
- GEX Regime: {chain_summary.get('gex_regime', 'N/A')}
- OI Bias: {chain_summary.get('oi_bias', 'N/A')}

Write a concise EOD report covering:
1. **Price Action** — what happened today
2. **Technical Outlook** — key indicator readings
3. **Options Activity** — what smart money did
4. **Tomorrow's Setup** — levels to watch, potential scenarios
5. **Trade Ideas** — 1-2 specific options plays for tomorrow

Format professionally. Be specific with levels. Max 300 words."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"_⚠️ Claude API error: {e}_"


def get_strategy_screener(
    symbol: str,
    spot: float,
    atm_iv: float,
    vix: float,
    pcr: float,
    gex_regime: str,
    skew_signal: str,
) -> list[dict]:
    """
    Get Claude to recommend top 3 options strategies for current conditions.
    Returns list of strategy dicts.
    """
    client = _get_client()
    if not client:
        return []

    prompt = f"""Given these market conditions for {symbol} (Spot: ₹{spot:,.0f}):
- ATM IV: {atm_iv:.1f}% | VIX: {v...

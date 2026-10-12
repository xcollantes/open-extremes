"""Alpaca SIP 1-minute bars for full regular sessions, cached as parquet."""

import os
from pathlib import Path

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetCalendarRequest
from dotenv import load_dotenv

ET = "America/New_York"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _keys() -> tuple[str, str]:
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    if not (key and secret):
        raise RuntimeError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY in the repo .env "
            "(see .env.example)."
        )
    return key, secret


def full_sessions(start: str, end: str) -> pd.DatetimeIndex:
    """
    Dates (ET midnight) of sessions that ran the full 09:30-16:00.

    Args:
        start: First date, YYYY-MM-DD.
        end: Last date, YYYY-MM-DD.

    Returns:
        Tz-aware ET midnights of each full session.
    """
    # ponytail: early closes (~3/yr) are dropped, not analysed; their
    # after-hours bars would otherwise pass a 09:30-16:00 clock filter.
    days = TradingClient(*_keys(), paper=True).get_calendar(
        GetCalendarRequest(start=start, end=end)
    )
    return pd.DatetimeIndex(
        [
            pd.Timestamp(d.date)
            for d in days
            if (d.open.hour, d.open.minute, d.close.hour) == (9, 30, 16)
        ]
    ).tz_localize(ET)


def load_minute_bars(
    symbol: str, start: str, end: str, cache_dir: Path
) -> pd.DataFrame:
    """
    Regular-hours 1-minute bars from the SIP feed, ET-indexed.

    Prices are raw (unadjusted); splits never happen intraday, so
    within-day comparisons are unaffected. The result is cached at
    ``{cache_dir}/{symbol}_1Min_{start}_{end}.parquet``; delete the file
    to refetch.

    Args:
        symbol: Ticker, e.g. "NVDA".
        start: First date, YYYY-MM-DD (inclusive).
        end: End date, YYYY-MM-DD (exclusive).
        cache_dir: Directory for the parquet cache.

    Returns:
        Bars with open, high, low, close, volume, trade_count, vwap.
    """
    path = Path(cache_dir) / f"{symbol}_1Min_{start}_{end}.parquet"
    if path.exists():
        return pd.read_parquet(path)

    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=pd.Timestamp(start, tz=ET),
        end=pd.Timestamp(end, tz=ET),
        feed=DataFeed.SIP,  # Consolidated tape; IEX alone misplaces highs/lows.
        adjustment=Adjustment.RAW,
    )
    client = StockHistoricalDataClient(*_keys())
    bars = client.get_stock_bars(req).df.xs(symbol)
    bars.index = bars.index.tz_convert(ET)

    minute = bars.index.hour * 60 + bars.index.minute
    in_hours = (minute >= 9 * 60 + 30) & (minute < 16 * 60)
    full_day = bars.index.normalize().isin(full_sessions(start, end))
    bars = bars[in_hours & full_day]

    path.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(path)
    return bars

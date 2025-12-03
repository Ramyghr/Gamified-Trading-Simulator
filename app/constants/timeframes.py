from enum import Enum

class Timeframe(str, Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

# Timeframe to seconds mapping
TIMEFRAME_SECONDS = {
    Timeframe.ONE_MINUTE: 60,
    Timeframe.FIVE_MINUTES: 300,
    Timeframe.FIFTEEN_MINUTES: 900,
    Timeframe.THIRTY_MINUTES: 1800,
    Timeframe.ONE_HOUR: 3600,
    Timeframe.FOUR_HOURS: 14400,
    Timeframe.ONE_DAY: 86400,
    Timeframe.ONE_WEEK: 604800,
    Timeframe.ONE_MONTH: 2592000,
}

# Provider-specific timeframe mappings
PROVIDER_TIMEFRAME_MAP = {
    "polygon": {
        "1m": "minute",
        "5m": "5minute",
        "15m": "15minute",
        "30m": "30minute",
        "1h": "hour",
        "1d": "day",
        "1w": "week",
        "1M": "month"
    },
    "alpha_vantage": {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "60min",
        "1d": "daily",
        "1w": "weekly",
        "1M": "monthly"
    },
    "binance": {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
        "1M": "1M"
    }
}
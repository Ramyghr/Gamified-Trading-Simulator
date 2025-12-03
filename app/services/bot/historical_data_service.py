"""
Historical Data Service - Fetch historical price data for backtesting
ENHANCED VERSION: Multiple API support with priority ranking
APIs: Alpha Vantage, Twelve Data, Polygon, Finnhub, Yahoo Finance
NO MOCK DATA - Real APIs only
"""
import asyncio
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging
import os
import time

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """
    Fetches historical price data from multiple sources with intelligent fallback
    Priority: Polygon -> Finnhub -> Alpha Vantage -> Twelve Data -> Yahoo Finance
    """
    
    def __init__(self):
        # API Keys - PLACEHOLDERS - YOU NEED TO FILL THESE
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "V6KUJ6EQB9OCJ1CT")
        self.twelve_data_key = os.getenv("TWELVE_DATA_API_KEY", "7dd48638c9f54ffd9029af89de3213d6")
        self.polygon_key = os.getenv("POLYGON_API_KEY", "dHrLdODMLQqYtmf2Na7iDYN2nnDyPdXn")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "d3lia21r01qq28enk8lgd3lia21r01qq28enk8m0")
        
        # API priority configuration
        self.data_sources = [
            {
                "name": "Polygon.io",
                "priority": 1,
                "enabled": True if self.polygon_key != "dHrLdODMLQqYtmf2Na7iDYN2nnDyPdXn" else False,
                "fetch_func": self._fetch_from_polygon,
                "asset_classes": ["stock", "crypto", "forex", "commodity"],
                "rate_limit": 5  # requests per minute
            },
            {
                "name": "Finnhub",
                "priority": 2,
                "enabled": True if self.finnhub_key != "d3lia21r01qq28enk8lgd3lia21r01qq28enk8m0" else False,
                "fetch_func": self._fetch_from_finnhub,
                "asset_classes": ["stock", "crypto", "forex"],
                "rate_limit": 60  # free tier limit
            },
            {
                "name": "Alpha Vantage",
                "priority": 3,
                "enabled": True if self.alpha_vantage_key != "V6KUJ6EQB9OCJ1CT" else False,
                "fetch_func": self._fetch_from_alpha_vantage,
                "asset_classes": ["stock", "forex", "commodity", "crypto"],
                "rate_limit": 5  # free tier limit
            },
            {
                "name": "Twelve Data",
                "priority": 4,
                "enabled": True if self.twelve_data_key != "7dd48638c9f54ffd9029af89de3213d6" else False,
                "fetch_func": self._fetch_from_twelve_data,
                "asset_classes": ["stock", "crypto", "forex", "commodity", "index"],
                "rate_limit": 800  # free tier per day
            },
            {
                "name": "Yahoo Finance",
                "priority": 5,
                "enabled": True,
                "fetch_func": self._fetch_from_yahoo,
                "asset_classes": ["stock", "crypto", "forex", "commodity", "etf"],
                "rate_limit": 0  # unlimited
            }
        ]
        
        # Sort by priority
        self.data_sources.sort(key=lambda x: x["priority"])
        
        # Cache and rate limiting
        self.cache = {}
        self.rate_limits = {}
        self.request_times = {}
        
        # Initialize rate limits
        for source in self.data_sources:
            self.request_times[source["name"]] = []
    
    def get_available_sources(self) -> List[Dict]:
        """Get list of available data sources with their status"""
        available = []
        for source in self.data_sources:
            if source["enabled"]:
                available.append({
                    "name": source["name"],
                    "priority": source["priority"],
                    "asset_classes": source["asset_classes"],
                    "rate_limit": source["rate_limit"]
                })
        return available
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1h",
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from multiple sources with intelligent fallback
        
        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTCUSDT", "XAUUSD")
            start_date: Start date
            end_date: End date
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            asset_class: Asset class to help choose appropriate API
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}_{interval}_{asset_class}"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"✓ Cache hit for {symbol}")
            return self.cache[cache_key]
        
        # Try enabled data sources in priority order
        for source in self.data_sources:
            if not source["enabled"]:
                continue
                
            # Check if source supports this asset class
            if asset_class not in source["asset_classes"]:
                logger.debug(f"Skipping {source['name']} - doesn't support {asset_class}")
                continue
            
            # Check rate limit
            if not self._check_rate_limit(source["name"], source["rate_limit"]):
                logger.debug(f"Rate limit reached for {source['name']}, trying next source")
                continue
            
            try:
                logger.info(f"Attempting {source['name']} for {symbol} ({asset_class})...")
                
                data = await source["fetch_func"](
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    asset_class=asset_class
                )
                
                # Record request time for rate limiting
                self._record_request_time(source["name"])
                
                if not data.empty and len(data) > 10:  # Require minimum data points
                    logger.info(f"✓ {source['name']} success: {len(data)} candles for {symbol}")
                    self.cache[cache_key] = data
                    return data
                elif not data.empty:
                    logger.warning(f"✗ {source['name']} returned insufficient data ({len(data)} candles)")
                else:
                    logger.warning(f"✗ {source['name']} returned empty data for {symbol}")
                    
            except Exception as e:
                logger.warning(f"✗ {source['name']} failed for {symbol}: {str(e)[:100]}")
                continue
        
        # All sources failed
        error_msg = f"All data sources failed for {symbol}. Check API keys, symbol format, and date range."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # ============ POLYGON.IO ============
    async def _fetch_from_polygon(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch from Polygon.io - High quality, real-time data
        Best for: US Stocks, Crypto, Forex
        """
        try:
            # Map interval to Polygon format
            interval_map = {
                "1m": "minute", "5m": "minute", "15m": "minute", "30m": "minute",
                "1h": "hour", "4h": "hour", "1d": "day"
            }
            polygon_interval = interval_map.get(interval, "minute")
            
            # Determine multiplier based on interval
            multiplier_map = {
                "1m": "1", "5m": "5", "15m": "15", "30m": "30",
                "1h": "1", "4h": "4", "1d": "1"
            }
            timespan_multiplier = multiplier_map.get(interval, "1")
            
            # Adjust symbol for different asset classes
            adjusted_symbol = symbol
            if asset_class == "forex":
                adjusted_symbol = f"C:{symbol}"
            elif asset_class == "crypto":
                adjusted_symbol = f"X:{symbol}"
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{adjusted_symbol}/range/{timespan_multiplier}/{polygon_interval}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            params = {
                "adjusted": "true",
                "sort": "asc",
                "limit": 50000,
                "apiKey": self.polygon_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 429:
                    logger.warning("Polygon rate limit exceeded")
                    return pd.DataFrame()
                
                data = response.json()
            
            if data.get("status") != "OK" or "results" not in data:
                logger.warning(f"Polygon error: {data.get('error', 'Unknown error')}")
                return pd.DataFrame()
            
            # Parse response
            results = data["results"]
            if not results:
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            
            # Convert timestamp (milliseconds to datetime)
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            
            # Rename columns
            df = df.rename(columns={
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume',
                'vw': 'vwap'
            })
            
            # Select and order columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume', 'vwap']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            logger.info(f"✓ Polygon.io: {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Polygon.io error for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    # ============ FINNHUB ============
    async def _fetch_from_finnhub(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch from Finnhub - Good for global markets
        Best for: Stocks, Forex, Crypto
        """
        try:
            # Map interval to Finnhub format (resolution)
            interval_map = {
                "1m": "1", "5m": "5", "15m": "15", "30m": "30",
                "1h": "60", "4h": "60", "1d": "D"
            }
            resolution = interval_map.get(interval, "60")
            
            # Convert dates to timestamps
            from_time = int(start_date.timestamp())
            to_time = int(end_date.timestamp())
            
            url = "https://finnhub.io/api/v1/stock/candle"
            
            params = {
                "symbol": symbol,
                "resolution": resolution,
                "from": from_time,
                "to": to_time,
                "token": self.finnhub_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data.get("s") != "ok":
                logger.warning(f"Finnhub error: {data.get('error', 'Unknown error')}")
                return pd.DataFrame()
            
            # Extract data
            timestamps = data.get("t", [])
            opens = data.get("o", [])
            highs = data.get("h", [])
            lows = data.get("l", [])
            closes = data.get("c", [])
            volumes = data.get("v", [])
            
            if not timestamps:
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(timestamps, unit='s'),
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            })
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            logger.info(f"✓ Finnhub: {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Finnhub error for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    # ============ ALPHA VANTAGE ============
    async def _fetch_from_alpha_vantage(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch from Alpha Vantage
        Best for: Forex, commodities, stocks
        """
        try:
            # Map interval to Alpha Vantage format
            interval_map = {
                "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
                "1h": "60min", "4h": "60min", "1d": "daily"
            }
            av_interval = interval_map.get(interval, "60min")
            
            # Determine function based on asset class
            if asset_class == "forex":
                function = "FX_INTRADAY" if av_interval != "daily" else "FX_DAILY"
                params = {
                    "function": function,
                    "from_symbol": symbol[:3],
                    "to_symbol": symbol[3:],
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "full",
                    "datatype": "json"
                }
                if function == "FX_INTRADAY":
                    params["interval"] = av_interval
            elif asset_class == "crypto":
                function = "DIGITAL_CURRENCY_INTRADAY" if av_interval != "daily" else "DIGITAL_CURRENCY_DAILY"
                params = {
                    "function": function,
                    "symbol": symbol.replace("USDT", ""),
                    "market": "USD",
                    "apikey": self.alpha_vantage_key
                }
            else:
                function = "TIME_SERIES_INTRADAY" if av_interval != "daily" else "TIME_SERIES_DAILY"
                params = {
                    "function": function,
                    "symbol": symbol,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "full",
                    "datatype": "json"
                }
                if function == "TIME_SERIES_INTRADAY":
                    params["interval"] = av_interval
            
            url = "https://www.alphavantage.co/query"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            # Check for errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return pd.DataFrame()
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return pd.DataFrame()
            
            # Parse response - find the time series key
            time_series_key = None
            for key in data.keys():
                if "Time Series" in key or "Time Series (Digital Currency" in key or "Time Series FX" in key:
                    time_series_key = key
                    break
            
            if not time_series_key or time_series_key not in data:
                logger.warning(f"No time series data in Alpha Vantage response")
                return pd.DataFrame()
            
            df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
            
            if df.empty:
                return pd.DataFrame()
            
            # Normalize column names
            column_map = {
                '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close',
                '5. volume': 'volume', '1a. open (USD)': 'open', '2a. high (USD)': 'high',
                '3a. low (USD)': 'low', '4a. close (USD)': 'close',
                '1. From_Currency Code': 'open', '2. From_Currency Name': 'high',  # Fallback
                '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close'
            }
            
            df = df.reset_index()
            df = df.rename(columns={'index': 'timestamp'})
            
            # Rename columns based on mapping
            for old_col, new_col in column_map.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Ensure we have required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close']
            available_cols = [col for col in required_cols if col in df.columns]
            
            if len(available_cols) >= 5:  # Need all OHLC + timestamp
                df = df[available_cols]
                
                # Convert to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.dropna()
                df = df.sort_values('timestamp')
                
                logger.info(f"✓ Alpha Vantage: {len(df)} candles for {symbol}")
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    # ============ TWELVE DATA ============
    async def _fetch_from_twelve_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch from Twelve Data
        Best for: All asset types, global coverage
        """
        try:
            url = "https://api.twelvedata.com/time_series"
            
            params = {
                "symbol": symbol,
                "interval": interval,
                "apikey": self.twelve_data_key,
                "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                "outputsize": 5000,
                "format": "JSON"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            # Check for errors
            if "status" in data and data["status"] == "error":
                logger.error(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
            
            if "values" not in data or not data["values"]:
                logger.warning("Twelve Data returned no values")
                return pd.DataFrame()
            
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={'datetime': 'timestamp'})
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            df = df.sort_values('timestamp')
            
            logger.info(f"✓ Twelve Data: {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Twelve Data error for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    # ============ YAHOO FINANCE ============
    async def _fetch_from_yahoo(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """
        Fetch from Yahoo Finance using yfinance
        Supports: stocks, ETFs, crypto, commodities, forex
        """
        try:
            import yfinance as yf
            
            # Map interval to Yahoo format
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "1h", "1d": "1d"
            }
            yf_interval = interval_map.get(interval, "1h")
            
            # Convert symbol to Yahoo format
            yahoo_symbol = self._convert_to_yahoo_symbol(symbol, asset_class)
            
            logger.info(f"Fetching {yahoo_symbol} from Yahoo Finance ({yf_interval})")
            
            # Fetch data
            ticker = yf.Ticker(yahoo_symbol)
            
            # Calculate period based on interval
            if yf_interval in ["1m", "5m", "15m", "30m"]:
                # Intraday - max 7 days for free Yahoo data
                period = "7d"
            elif yf_interval == "1h":
                period = "60d"
            else:
                period = "max"
            
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                period=period,
                auto_adjust=True,
                actions=False
            )
            
            if df.empty:
                logger.warning(f"Yahoo returned empty data for {yahoo_symbol}")
                return pd.DataFrame()
            
            # Normalize to standard format
            df = df.reset_index()
            
            # Handle different column names
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Ensure we have required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if all(col in df.columns for col in required_cols):
                df = df[required_cols]
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Convert to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove any rows with NaN
                df = df.dropna()
                df = df.sort_values('timestamp')
                
                logger.info(f"✓ Yahoo Finance: {len(df)} candles for {symbol}")
                return df
            
            return pd.DataFrame()
            
        except ImportError:
            logger.error("yfinance not installed! Install: pip install yfinance")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _convert_to_yahoo_symbol(self, symbol: str, asset_class: str) -> str:
        """Convert trading symbol to Yahoo Finance format"""
        # Crypto conversions
        if asset_class == "crypto":
            if "USDT" in symbol:
                return symbol.replace("USDT", "-USD")
            elif symbol == "BTC":
                return "BTC-USD"
            elif symbol == "ETH":
                return "ETH-USD"
            else:
                return f"{symbol}-USD"
        
        # Forex conversions
        if asset_class == "forex":
            forex_pairs = {
                "EURUSD": "EURUSD=X",
                "GBPUSD": "GBPUSD=X",
                "USDJPY": "USDJPY=X",
                "AUDUSD": "AUDUSD=X",
                "USDCAD": "USDCAD=X",
                "USDCHF": "USDCHF=X",
                "NZDUSD": "NZDUSD=X",
            }
            return forex_pairs.get(symbol, f"{symbol}=X")
        
        # Commodities
        if asset_class == "commodity":
            commodity_map = {
                "XAUUSD": "GC=F",  # Gold futures
                "XAGUSD": "SI=F",  # Silver futures
                "CL": "CL=F",      # Crude oil
                "NG": "NG=F",      # Natural gas
                "HG": "HG=F",      # Copper
            }
            return commodity_map.get(symbol, symbol)
        
        # Stocks/ETFs - return as-is
        return symbol
    
    # ============ RATE LIMITING ============
    def _check_rate_limit(self, source_name: str, rate_limit: int) -> bool:
        """Check if we can make another request based on rate limit"""
        if rate_limit == 0:  # Unlimited
            return True
        
        if source_name not in self.request_times:
            return True
        
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Count requests in the last minute
        recent_requests = [t for t in self.request_times[source_name] if t > window_start]
        
        return len(recent_requests) < rate_limit
    
    def _record_request_time(self, source_name: str):
        """Record a request time for rate limiting"""
        if source_name not in self.request_times:
            self.request_times[source_name] = []
        
        self.request_times[source_name].append(time.time())
        
        # Keep only last 100 timestamps
        if len(self.request_times[source_name]) > 100:
            self.request_times[source_name] = self.request_times[source_name][-50:]
    
    # ============ UTILITY METHODS ============
    def _filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Filter dataframe by date range"""
        if df.empty:
            return df
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        filtered = df[mask].reset_index(drop=True)
        
        logger.info(f"Filtered to {len(filtered)} candles in date range")
        return filtered
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Historical data cache cleared")
    
    def get_source_status(self) -> Dict:
        """Get status of all data sources"""
        status = {}
        for source in self.data_sources:
            status[source["name"]] = {
                "enabled": source["enabled"],
                "priority": source["priority"],
                "asset_classes": source["asset_classes"],
                "rate_limit": source["rate_limit"],
                "recent_requests": len(self.request_times.get(source["name"], []))
            }
        return status


# Singleton instance
historical_data_service = HistoricalDataService()
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
        # API Keys
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "V6KUJ6EQB9OCJ1CT")
        self.twelve_data_key = os.getenv("TWELVE_DATA_API_KEY", "7dd48638c9f54ffd9029af89de3213d6")
        self.polygon_key = os.getenv("POLYGON_API_KEY", "dHrLdODMLQqYtmf2Na7iDYN2nnDyPdXn")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "d3lia21r01qq28enk8lgd3lia21r01qq28enk8m0")
        
        # Data sources with CORRECTED priority for commodities
        self.data_sources = [
            {
                "name": "Yahoo Finance",
                "priority": 1,  # Best for commodities like XAUUSD
                "enabled": True,
                "fetch_func": self._fetch_from_yahoo,
                "asset_classes": ["stock", "forex", "commodity", "etf", "index"],
                "rate_limit": 0
            },
            {
                "name": "Twelve Data",
                "priority": 2,
                "enabled": bool(self.twelve_data_key and self.twelve_data_key != "7dd48638c9f54ffd9029af89de3213d6"),
                "fetch_func": self._fetch_from_twelve_data,
                "asset_classes": ["stock", "crypto", "forex", "commodity", "index"],
                "rate_limit": 800
            },
            {
                "name": "Polygon.io",
                "priority": 3,
                "enabled": bool(self.polygon_key and self.polygon_key != "dHrLdODMLQqYtmf2Na7iDYN2nnDyPdXn"),
                "fetch_func": self._fetch_from_polygon,
                "asset_classes": ["stock", "crypto", "forex"],  # Limited commodity support
                "rate_limit": 5
            },
            {
                "name": "Alpha Vantage",
                "priority": 4,
                "enabled": bool(self.alpha_vantage_key and self.alpha_vantage_key != "V6KUJ6EQB9OCJ1CT"),
                "fetch_func": self._fetch_from_alpha_vantage,
                "asset_classes": ["stock", "forex", "commodity", "crypto"],
                "rate_limit": 5
            },
            {
                "name": "Finnhub",
                "priority": 5,
                "enabled": bool(self.finnhub_key and self.finnhub_key != "d3lia21r01qq28enk8lgd3lia21r01qq28enk8m0"),
                "fetch_func": self._fetch_from_finnhub,
                "asset_classes": ["stock", "crypto", "forex"],
                "rate_limit": 60
            }
        ]
        
        self.data_sources.sort(key=lambda x: x["priority"])
        self.cache = {}
        self.request_times = {}
        
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
        Get historical OHLCV data with multiple fallback strategies
        """
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}_{interval}_{asset_class}"
        
        if cache_key in self.cache:
            logger.info(f"✓ Cache hit for {symbol}")
            return self.cache[cache_key]
        
        # Detect asset class
        detected_class = self._detect_asset_class(symbol, asset_class)
        logger.info(f"Processing {symbol} as {detected_class}")
        
        errors = []
        
        # Strategy 1: Try with original symbol
        for source in self.data_sources:
            if not self._can_use_source(source, detected_class):
                continue
            
            try:
                logger.info(f"→ Trying {source['name']} with original symbol {symbol}...")
                data = await self._try_fetch(source, symbol, start_date, end_date, interval, detected_class)
                
                if not data.empty and len(data) >= 10:
                    logger.info(f"✓ {source['name']} SUCCESS: {len(data)} candles")
                    self.cache[cache_key] = data
                    return data
                    
            except Exception as e:
                error_msg = f"{source['name']} (original): {str(e)[:150]}"
                logger.warning(f"✗ {error_msg}")
                errors.append(error_msg)
        
        # Strategy 2: Try with alternative symbols for commodities
        if detected_class == "commodity":
            alternative_symbols = self._get_alternative_symbols(symbol)
            logger.info(f"Trying alternative symbols: {alternative_symbols}")
            
            for alt_symbol in alternative_symbols:
                for source in self.data_sources:
                    if not self._can_use_source(source, detected_class):
                        continue
                    
                    try:
                        logger.info(f"→ Trying {source['name']} with {alt_symbol}...")
                        data = await self._try_fetch(source, alt_symbol, start_date, end_date, interval, detected_class)
                        
                        if not data.empty and len(data) >= 10:
                            logger.info(f"✓ {source['name']} SUCCESS with {alt_symbol}: {len(data)} candles")
                            self.cache[cache_key] = data
                            return data
                            
                    except Exception as e:
                        error_msg = f"{source['name']} ({alt_symbol}): {str(e)[:150]}"
                        errors.append(error_msg)
        
        # Strategy 3: Try with relaxed date range (last 30 days)
        logger.info("Trying with relaxed date range (last 30 days)...")
        relaxed_end = datetime.now()
        relaxed_start = relaxed_end - timedelta(days=30)
        
        for source in self.data_sources:
            if not self._can_use_source(source, detected_class):
                continue
            
            try:
                logger.info(f"→ Trying {source['name']} with recent data...")
                data = await self._try_fetch(source, symbol, relaxed_start, relaxed_end, interval, detected_class)
                
                if not data.empty and len(data) >= 10:
                    logger.info(f"✓ {source['name']} SUCCESS with recent data: {len(data)} candles")
                    # Filter to requested date range if possible
                    filtered = data[
                        (data['timestamp'] >= start_date) & 
                        (data['timestamp'] <= end_date)
                    ]
                    if not filtered.empty and len(filtered) >= 10:
                        self.cache[cache_key] = filtered
                        return filtered
                    else:
                        logger.warning("Recent data doesn't cover requested range, returning all data")
                        self.cache[cache_key] = data
                        return data
                        
            except Exception as e:
                error_msg = f"{source['name']} (recent): {str(e)[:150]}"
                errors.append(error_msg)
        
        # All strategies failed
        error_summary = "\n".join([f"  - {err}" for err in errors[:10]])  # Limit to 10 errors
        
        suggestions = self._get_suggestions(symbol, detected_class, interval)
        
        raise ValueError(
            f"All strategies failed for {symbol} ({detected_class}):\n{error_summary}\n\n"
            f"Suggestions:\n{suggestions}"
        )
    def _get_alternative_symbols(self, symbol: str) -> List[str]:
        """Get alternative symbol formats to try"""
        symbol_upper = symbol.upper()
        alternatives = []
        
        # Gold alternatives
        if symbol_upper in ['XAUUSD', 'XAU/USD', 'GOLD']:
            alternatives = ['GC=F', 'XAU/USD', 'XAUUSD', 'GOLD']
        
        # Silver alternatives
        elif symbol_upper in ['XAGUSD', 'XAG/USD', 'SILVER']:
            alternatives = ['SI=F', 'XAG/USD', 'XAGUSD', 'SILVER']
        
        # Oil alternatives
        elif symbol_upper in ['CL', 'OIL', 'CRUDEOIL']:
            alternatives = ['CL=F', 'CL', 'CRUDEOIL']
        
        # Remove the original symbol and return unique alternatives
        alternatives = [s for s in alternatives if s != symbol_upper]
        return alternatives

    def _get_suggestions(self, symbol: str, asset_class: str, interval: str) -> str:
        """Generate helpful suggestions"""
        suggestions = []
        
        suggestions.append("1. Try daily interval (1d) instead of hourly - more reliable")
        suggestions.append("2. Check if yfinance is installed: pip install yfinance")
        
        if asset_class == "commodity":
            suggestions.append("3. For gold, try symbols: GC=F, XAU/USD, or XAUUSD")
            suggestions.append("4. Yahoo Finance futures may not be available in all regions")
            suggestions.append("5. Consider using Twelve Data API (requires API key)")
        
        if not self.twelve_data_key or self.twelve_data_key == "7dd48638c9f54ffd9029af89de3213d6":
            suggestions.append("6. Enable Twelve Data API: export TWELVE_DATA_API_KEY=your_key")
        
        suggestions.append(f"7. Try a more recent date range (e.g., last 30 days)")
        suggestions.append(f"8. Run debug script: python -m app.scripts.debug_data_fetch")
        
        return "\n".join([f"  {s}" for s in suggestions])

    def _can_use_source(self, source: dict, asset_class: str) -> bool:
        """Check if source can be used"""
        if not source["enabled"]:
            return False
        if asset_class not in source["asset_classes"]:
            return False
        if not self._check_rate_limit(source["name"], source["rate_limit"]):
            return False
        return True

    async def _try_fetch(
        self,
        source: dict,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str
    ) -> pd.DataFrame:
        """Try to fetch data from a source"""
        data = await source["fetch_func"](
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            asset_class=asset_class
        )
        self._record_request_time(source["name"])
        return data

    def _detect_asset_class(self, symbol: str, provided_class: str) -> str:
        """Auto-detect asset class"""
        symbol_upper = symbol.upper()
        
        # Commodity patterns
        commodity_symbols = {
            'XAUUSD', 'XAU/USD', 'GOLD', 'GC=F', 'GC',
            'XAGUSD', 'XAG/USD', 'SILVER', 'SI=F', 'SI',
            'CL', 'CL=F', 'OIL', 'CRUDEOIL',
            'NG', 'NG=F', 'NATURALGAS',
            'HG', 'HG=F', 'COPPER'
        }
        
        if symbol_upper in commodity_symbols:
            return "commodity"
        
        # Forex patterns
        if '/' in symbol and len(symbol.replace('/', '')) == 6:
            return "forex"
        if len(symbol) == 6 and symbol.isalpha():
            return "forex"
        
        # Crypto patterns
        crypto_pairs = {'USDT', 'BUSD', 'USDC', 'BTC', 'ETH'}
        if any(pair in symbol_upper for pair in crypto_pairs):
            return "crypto"
        
        return provided_class

    
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
        """Twelve Data API"""
        try:
            td_symbol = self._convert_to_twelve_data_symbol(symbol, asset_class)
            logger.info(f"  Twelve Data: {symbol} → {td_symbol}")
            
            url = "https://api.twelvedata.com/time_series"
            params = {
                "symbol": td_symbol,
                "interval": interval,
                "apikey": self.twelve_data_key,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "outputsize": 5000,
                "format": "JSON"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if "status" in data and data["status"] == "error":
                logger.error(f"  Twelve Data error: {data.get('message')}")
                return pd.DataFrame()
            
            if "values" not in data or not data["values"]:
                logger.warning("  No values returned")
                return pd.DataFrame()
            
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={'datetime': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna().sort_values('timestamp')
            
            logger.info(f"  Twelve Data: {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"  Twelve Data error: {str(e)}")
            return pd.DataFrame()

    def _convert_to_twelve_data_symbol(self, symbol: str, asset_class: str) -> str:
        """Convert to Twelve Data format"""
        symbol_upper = symbol.upper()
        
        if asset_class == "commodity":
            commodity_map = {
                'XAUUSD': 'XAU/USD', 'GOLD': 'XAU/USD', 'GC=F': 'XAU/USD',
                'XAGUSD': 'XAG/USD', 'SILVER': 'XAG/USD', 'SI=F': 'XAG/USD'
            }
            return commodity_map.get(symbol_upper, symbol)
        
        return symbol
    # ============ YAHOO FINANCE ============
    async def _fetch_from_yahoo(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        asset_class: str = "stock"
    ) -> pd.DataFrame:
        """Yahoo Finance with enhanced error handling"""
        try:
            import yfinance as yf
            
            interval_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "1h", "1d": "1d"
            }
            yf_interval = interval_map.get(interval, "1h")
            
            # Convert symbol
            yahoo_symbol = self._convert_to_yahoo_symbol(symbol, asset_class)
            logger.info(f"  Yahoo: {symbol} → {yahoo_symbol} ({yf_interval})")
            
            # Create ticker
            ticker = yf.Ticker(yahoo_symbol)
            
            # Calculate appropriate period
            days_diff = (end_date - start_date).days
            
            if yf_interval in ["1m", "5m"]:
                period = "7d"
            elif yf_interval in ["15m", "30m"]:
                period = "60d"
            elif yf_interval == "1h":
                period = "730d"
            else:
                if days_diff <= 30:
                    period = "1mo"
                elif days_diff <= 90:
                    period = "3mo"
                elif days_diff <= 180:
                    period = "6mo"
                elif days_diff <= 365:
                    period = "1y"
                else:
                    period = "max"
            
            logger.info(f"  Requesting period={period}, interval={yf_interval}")
            
            # Try with date range first
            try:
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=yf_interval,
                    auto_adjust=True,
                    actions=False
                )
            except Exception as e:
                logger.warning(f"  Date range failed: {e}, trying period...")
                # Fallback to period
                df = ticker.history(
                    period=period,
                    interval=yf_interval,
                    auto_adjust=True,
                    actions=False
                )
            
            if df.empty:
                logger.warning(f"  Empty result for {yahoo_symbol}")
                return pd.DataFrame()
            
            logger.info(f"  Raw data: {len(df)} rows")
            
            # Normalize columns
            df = df.reset_index()
            
            # Handle timestamp column
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            
            # Rename OHLCV columns
            df = df.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            })
            
            # Check required columns
            required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                logger.error(f"  Missing columns: {missing}")
                logger.error(f"  Available columns: {list(df.columns)}")
                return pd.DataFrame()
            
            # Select and clean
            df = df[required]
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove NaN
            before_clean = len(df)
            df = df.dropna()
            after_clean = len(df)
            
            if before_clean != after_clean:
                logger.info(f"  Cleaned: {before_clean} → {after_clean} rows")
            
            df = df.sort_values('timestamp')
            
            logger.info(f"  Final: {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            return df
            
        except ImportError:
            logger.error("❌ yfinance not installed! Run: pip install yfinance")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"  Yahoo error: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return pd.DataFrame()

    def _convert_to_yahoo_symbol(self, symbol: str, asset_class: str) -> str:
        """Convert to Yahoo format"""
        symbol_upper = symbol.upper()
        
        if asset_class == "commodity":
            commodity_map = {
                'XAUUSD': 'GC=F', 'XAU/USD': 'GC=F', 'GOLD': 'GC=F',
                'XAGUSD': 'SI=F', 'XAG/USD': 'SI=F', 'SILVER': 'SI=F',
                'CL': 'CL=F', 'OIL': 'CL=F', 'CRUDEOIL': 'CL=F',
                'NG': 'NG=F', 'NATURALGAS': 'NG=F',
                'HG': 'HG=F', 'COPPER': 'HG=F'
            }
            if symbol_upper in commodity_map:
                return commodity_map[symbol_upper]
            if '=F' in symbol:
                return symbol
        
        if asset_class == "forex":
            if '/' in symbol:
                symbol_upper = symbol_upper.replace('/', '')
            return f"{symbol_upper}=X"
        
        if asset_class == "crypto":
            crypto_map = {
                'BTCUSDT': 'BTC-USD', 'ETHUSDT': 'ETH-USD',
                'BTC': 'BTC-USD', 'ETH': 'ETH-USD'
            }
            return crypto_map.get(symbol_upper, f"{symbol_upper}-USD")
        
        return symbol
    # ============ RATE LIMITING ============
    def _check_rate_limit(self, source_name: str, rate_limit: int) -> bool:
        """Check rate limiting"""
        if rate_limit == 0:
            return True
        
        current_time = time.time()
        window_start = current_time - 60
        
        recent = [t for t in self.request_times.get(source_name, []) if t > window_start]
        return len(recent) < rate_limit

    def _record_request_time(self, source_name: str):
        """Record request time"""
        if source_name not in self.request_times:
            self.request_times[source_name] = []
        
        self.request_times[source_name].append(time.time())
        
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
        """Clear cache"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_source_status(self) -> Dict:
        """Get status of all sources"""
        status = {}
        for source in self.data_sources:
            status[source["name"]] = {
                "enabled": source["enabled"],
                "priority": source["priority"],
                "asset_classes": source["asset_classes"],
                "rate_limit": source["rate_limit"]
            }
        return status


# Singleton instance
historical_data_service = HistoricalDataService()
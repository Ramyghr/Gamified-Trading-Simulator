"""
Historical Data Loader - FIXED VERSION
Loads and caches crisis-specific market data for simulations
Handles close-price-only data with proper date parsing
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class HistoricalDataLoader:
    """
    Manages loading and caching of historical crisis data
    Supports efficient lookups during simulation
    """
    
    # Define data structure for each crisis - FIXED
    CRISIS_DATA_CONFIGS = {
        "great_depression": {
            "directory": "Simulation_data/great_depression_29-39",
            "main_file": "Down_Jones_historical_daily.csv",
            "date_column": "Date",
            "date_format": "%m/%d/%Y",  # MM/DD/YYYY
            "assets": {
                "DJIA": {
                    "file": "Down_Jones_historical_daily.csv",
                    "price_col": "Value"
                }
            }
        },
        "black_monday": {
            "directory": "Simulation_data/Black_Monday-1987",
            "main_file": "final_black_monday_1987.csv",
            "date_column": "Date",
            "date_format": "%Y-%m-%d",  # YYYY-MM-DD
            "assets": {
                "^GSPC": {
                    "file": "sp500_1987.csv",
                    "symbol_col": "sp500"
                },
                "^N225": {
                    "file": "nikkei_1987.csv",
                    "symbol_col": "nikkei"
                },
                "^FTSE": {
                    "file": "ftse_1987.csv",
                    "symbol_col": "ftse"
                }
            }
        },
        "dotcom_bubble": {
            "directory": "Simulation_data/dot-com_bubble-98-02",
            "main_file": "dotcom_bubble_1998_2002.csv",
            "date_column": "Date",
            "date_format": "%Y-%m-%d",  # YYYY-MM-DD
            "assets": {
                "^IXIC": {
                    "file": "nasdaq_1998_2002.csv",
                    "symbol": "^IXIC"
                },
                "CSCO": {
                    "file": "cisco_1998_2002.csv",
                    "symbol": "CSCO"
                },
                "INTC": {
                    "file": "intel_1998_2002.csv",
                    "symbol": "INTC"
                },
                "AMZN": {
                    "file": "amazon_1998_2002.csv",
                    "symbol": "AMZN"
                },
                "GE": {
                    "file": "ge_1998_2002.csv",
                    "symbol": "GE"
                },
                "WMT": {
                    "file": "walmart_1998_2002.csv",
                    "symbol": "WMT"
                },
                "^GSPC": {
                    "file": "s&p_500_1998_2002.csv",
                    "symbol": "^GSPC"
                }
            }
        },
        "financial_crisis_2008": {
            "directory": "Simulation_data/global_financial_crisi",
            "main_file": "gfc_with_proxies_2007_2009.csv",
            "date_column": "Date",
            "date_format": "%Y-%m-%d",  # YYYY-MM-DD
            "assets": {
                "BAC": {"symbol": "BAC"},
                "GS": {"symbol": "GS"},
                "JPM": {"symbol": "JPM"},
                "WFC": {"symbol": "WFC"},
                "C": {"symbol": "C"},
                "^GSPC": {"symbol": "^GSPC"},
                "^VIX": {"symbol": "^VIX"},
                "XLF": {"symbol": "XLF"},
                "VNQ": {"symbol": "VNQ"},
                "GLD": {"symbol": "GLD"},
                "TLT": {"symbol": "TLT"}
            }
        },
        "covid_crash": {
            "directory": "Simulation_data/covid",
            "main_file": "covid_crash_2020.csv",
            "date_column": "Date",
            "date_format": "%Y-%m-%d",  # YYYY-MM-DD
            "assets": {
                "^GSPC": {"symbol": "^GSPC"},
                "^IXIC": {"symbol": "^IXIC"},
                "^DJI": {"symbol": "^DJI"},
                "^RUT": {"symbol": "^RUT"},
                "^VIX": {"symbol": "^VIX"},
                "AAPL": {"symbol": "AAPL"},
                "MSFT": {"symbol": "MSFT"},
                "AMZN": {"symbol": "AMZN"},
                "GOOGL": {"symbol": "GOOGL"},
                "TSLA": {"symbol": "TSLA"},
                "AAL": {"symbol": "AAL"},
                "UAL": {"symbol": "UAL"},
                "MAR": {"symbol": "MAR"},
                "XOM": {"symbol": "XOM"},
                "CVX": {"symbol": "CVX"},
                "JPM": {"symbol": "JPM"},
                "GS": {"symbol": "GS"},
                "GLD": {"symbol": "GLD"},
                "TLT": {"symbol": "TLT"}
            }
        }
    }
    
    def __init__(self, base_path: str = "."):
        """
        Initialize data loader
        
        Args:
            base_path: Base directory where Simulation_data folder is located
        """
        self.base_path = Path(base_path)
        self._cache: Dict[str, pd.DataFrame] = {}
        
    def load_crisis_data(self, crisis_type: str) -> pd.DataFrame:
        """
        Load complete dataset for a crisis - FIXED
        
        Args:
            crisis_type: Type of crisis (great_depression, black_monday, etc.)
            
        Returns:
            DataFrame with Date index and columns for each asset (close prices)
        """
        if crisis_type in self._cache:
            logger.info(f"Using cached data for {crisis_type}")
            return self._cache[crisis_type].copy()
        
        config = self.CRISIS_DATA_CONFIGS.get(crisis_type)
        if not config:
            raise ValueError(f"Unknown crisis type: {crisis_type}")
        
        data_dir = self.base_path / config["directory"]
        main_file = data_dir / config["main_file"]
        
        logger.info(f"Loading data for {crisis_type} from {main_file}")
        
        try:
            # Load main file with proper date parsing
            date_format = config.get("date_format", "%Y-%m-%d")
            
            # Read CSV
            df = pd.read_csv(main_file)
            
            # Parse dates with correct format
            date_col = config.get("date_column", "Date")
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], format=date_format, errors='coerce')
                df.set_index(date_col, inplace=True)
            
            # Remove any rows with invalid dates
            df = df[df.index.notna()]
            
            # Sort by date
            df.sort_index(inplace=True)
            
            # Select only numeric columns (close prices)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            df = df[numeric_cols]
            
            # Forward fill missing values
            df.ffill(inplace=True)
            
            # Backward fill any remaining NaN at the start
            df.bfill(inplace=True)
            
            # Cache the data
            self._cache[crisis_type] = df
            
            logger.info(f"Loaded {len(df)} days of data for {crisis_type}")
            logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
            logger.info(f"Assets: {list(df.columns)}")
            
            return df.copy()
            
        except Exception as e:
            logger.error(f"Error loading data for {crisis_type}: {e}")
            raise
    
    def get_price_at_time(
        self, 
        crisis_type: str, 
        symbol: str, 
        timestamp: datetime,
        interpolate: bool = True
    ) -> Optional[float]:
        """
        Get asset price at specific historical time - FIXED
        
        Args:
            crisis_type: Crisis identifier
            symbol: Asset symbol
            timestamp: Historical timestamp
            interpolate: Whether to interpolate between daily prices
            
        Returns:
            Close price at that time, or None if not available
        """
        df = self.load_crisis_data(crisis_type)
        
        # Check all possible column names for this symbol
        possible_cols = [symbol, symbol.lower(), symbol.upper(), symbol.replace('^', '')]
        
        actual_col = None
        for col in possible_cols:
            if col in df.columns:
                actual_col = col
                break
        
        if actual_col is None:
            logger.warning(f"Symbol {symbol} not found in {crisis_type} data. Available: {list(df.columns)}")
            return None
        
        # Normalize timestamp to date only (no time component)
        timestamp_date = pd.Timestamp(timestamp.date())
        
        try:
            # Exact match
            if timestamp_date in df.index:
                price = float(df.loc[timestamp_date, actual_col])
                return price if not np.isnan(price) else None
            
            if interpolate:
                # Find surrounding dates
                before_dates = df.index[df.index <= timestamp_date]
                after_dates = df.index[df.index > timestamp_date]
                
                if len(before_dates) == 0:
                    # Before data starts - use first available
                    price = float(df.iloc[0][actual_col])
                    return price if not np.isnan(price) else None
                    
                if len(after_dates) == 0:
                    # After data ends - use last available
                    price = float(df.iloc[-1][actual_col])
                    return price if not np.isnan(price) else None
                
                before_date = before_dates[-1]
                after_date = after_dates[0]
                
                before_price = float(df.loc[before_date, actual_col])
                after_price = float(df.loc[after_date, actual_col])
                
                # Check for NaN
                if np.isnan(before_price) or np.isnan(after_price):
                    # Use nearest non-NaN value
                    return before_price if not np.isnan(before_price) else after_price
                
                # Linear interpolation by days
                total_days = (after_date - before_date).days
                elapsed_days = (timestamp_date - before_date).days
                
                if total_days > 0:
                    weight = elapsed_days / total_days
                    interpolated_price = before_price + (after_price - before_price) * weight
                    return float(interpolated_price)
                
                return float(before_price)
            else:
                # Return nearest previous close
                before_dates = df.index[df.index <= timestamp_date]
                if len(before_dates) > 0:
                    price = float(df.loc[before_dates[-1], actual_col])
                    return price if not np.isnan(price) else None
                return None
                
        except Exception as e:
            logger.error(f"Error getting price for {symbol} at {timestamp}: {e}")
            return None
    
    def get_ohlcv_at_time(
        self,
        crisis_type: str,
        symbol: str,
        timestamp: datetime
    ) -> Optional[Dict[str, float]]:
        """
        Get OHLCV data - synthesized from close prices since we only have close
        
        Args:
            crisis_type: Crisis identifier
            symbol: Asset symbol
            timestamp: Historical timestamp
            
        Returns:
            Dictionary with open, high, low, close, volume (synthesized)
        """
        close_price = self.get_price_at_time(crisis_type, symbol, timestamp, interpolate=True)
        
        if close_price is None:
            return None
        
        # Get previous day's close for open price
        prev_day = timestamp - timedelta(days=1)
        prev_close = self.get_price_at_time(crisis_type, symbol, prev_day, interpolate=True)
        
        if prev_close is None:
            open_price = close_price
        else:
            open_price = prev_close
        
        # Synthesize realistic intraday range
        # Typical daily volatility ~1-2% for indices, more for stocks
        daily_volatility = 0.015  # 1.5% typical
        
        # High and low within reasonable range
        high = close_price * (1 + daily_volatility * np.random.uniform(0, 1))
        low = close_price * (1 - daily_volatility * np.random.uniform(0, 1))
        
        # Ensure open is between high and low
        open_price = np.clip(open_price, low, high)
        
        return {
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close_price, 2),
            "volume": int(np.random.uniform(1_000_000, 10_000_000))  # Synthetic volume
        }
    
    def get_available_assets(self, crisis_type: str) -> List[str]:
        """
        Get list of available assets for a crisis
        
        Args:
            crisis_type: Crisis identifier
            
        Returns:
            List of asset symbols
        """
        df = self.load_crisis_data(crisis_type)
        return list(df.columns)
    
    def get_date_range(self, crisis_type: str) -> Tuple[datetime, datetime]:
        """
        Get the date range covered by crisis data
        
        Args:
            crisis_type: Crisis identifier
            
        Returns:
            Tuple of (start_date, end_date)
        """
        df = self.load_crisis_data(crisis_type)
        return df.index.min().to_pydatetime(), df.index.max().to_pydatetime()
    
    def get_price_series(
        self,
        crisis_type: str,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.Series:
        """
        Get price series for a symbol within date range
        
        Args:
            crisis_type: Crisis identifier
            symbol: Asset symbol
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Series of prices
        """
        df = self.load_crisis_data(crisis_type)
        
        # Find actual column
        possible_cols = [symbol, symbol.lower(), symbol.upper(), symbol.replace('^', '')]
        actual_col = None
        for col in possible_cols:
            if col in df.columns:
                actual_col = col
                break
        
        if actual_col is None:
            raise ValueError(f"Symbol {symbol} not found")
        
        series = df[actual_col]
        
        if start_date:
            series = series[series.index >= start_date]
        if end_date:
            series = series[series.index <= end_date]
        
        return series
    
    def validate_data(self, crisis_type: str) -> Dict[str, any]:
        """
        Validate data completeness and quality
        
        Args:
            crisis_type: Crisis identifier
            
        Returns:
            Dictionary with validation results
        """
        df = self.load_crisis_data(crisis_type)
        
        return {
            "total_days": len(df),
            "date_range": (df.index.min(), df.index.max()),
            "assets": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "price_ranges": {
                col: {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean())
                }
                for col in df.columns
            }
        }
    
    def get_historical_volatility(
        self,
        crisis_type: str,
        symbol: str,
        lookback_days: int = 21
    ) -> pd.Series:
        """
        Calculate rolling historical volatility
        
        Args:
            crisis_type: Crisis identifier
            symbol: Asset symbol
            lookback_days: Rolling window size
            
        Returns:
            Series of annualized volatility percentages
        """
        series = self.get_price_series(crisis_type, symbol)
        returns = series.pct_change()
        volatility = returns.rolling(window=lookback_days).std() * np.sqrt(252) * 100
        
        return volatility
    
    def clear_cache(self):
        """Clear cached data"""
        self._cache.clear()
        logger.info("Data cache cleared")
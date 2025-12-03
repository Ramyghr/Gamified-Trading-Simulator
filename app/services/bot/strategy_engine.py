"""
Strategy Engine - Implements 10 Common Trading Strategies
Save as: app/services/bot/strategy_engine.py
"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StrategySignal:
    """Trading signal with strength and metadata"""
    def __init__(
        self, 
        action: str,  # BUY, SELL, HOLD
        strength: float,  # 0-1
        price: float,
        indicators: Dict[str, Any],
        reason: str
    ):
        self.action = action
        self.strength = strength
        self.price = price
        self.indicators = indicators
        self.reason = reason
        self.timestamp = datetime.utcnow()


class StrategyEngine:
    """
    Implements 10 common trading strategies
    """
    
    def __init__(self):
        self.strategies = {
            "MA_CROSSOVER": self.moving_average_crossover,
            "RSI_OVERSOLD_OVERBOUGHT": self.rsi_strategy,
            "BOLLINGER_BANDS": self.bollinger_bands_strategy,
            "MACD_CROSSOVER": self.macd_crossover,
            "VOLUME_BREAKOUT": self.volume_breakout,
            "MEAN_REVERSION": self.mean_reversion,
            "MOMENTUM": self.momentum_strategy,
            "SUPPORT_RESISTANCE": self.support_resistance,
            "GRID_TRADING": self.grid_trading,
            "DCA": self.dollar_cost_averaging,
            "RAPID_TEST": self.rapid_test_strategy
        }
    
    def execute_strategy(
        self,
        strategy_type: str,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Execute a strategy and return trading signal
        
        Args:
            strategy_type: Type of strategy
            params: Strategy parameters
            price_data: DataFrame with columns: timestamp, open, high, low, close, volume
            current_position: Current position info (optional)
        
        Returns:
            StrategySignal object
        """
        if strategy_type not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_type}")
        
        strategy_func = self.strategies[strategy_type]
        return strategy_func(params, price_data, current_position)
    
    # ==================== STRATEGY 1: Moving Average Crossover ====================
    
    def moving_average_crossover(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Classic MA crossover: Buy when short MA crosses above long MA, sell when crosses below
        
        Required params:
        - short_window: Short MA period (e.g., 5)
        - long_window: Long MA period (e.g., 20)
        """
        short_window = params.get('short_window', 5)
        long_window = params.get('long_window', 20)
        
        if len(price_data) < long_window:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Calculate MAs
        price_data['MA_short'] = price_data['close'].rolling(window=short_window).mean()
        price_data['MA_long'] = price_data['close'].rolling(window=long_window).mean()
        
        # Current values
        current_price = float(price_data['close'].iloc[-1])
        ma_short_current = float(price_data['MA_short'].iloc[-1])
        ma_long_current = float(price_data['MA_long'].iloc[-1])
        
        # Previous values
        ma_short_prev = float(price_data['MA_short'].iloc[-2])
        ma_long_prev = float(price_data['MA_long'].iloc[-2])
        
        # Detect crossover
        bullish_cross = ma_short_prev <= ma_long_prev and ma_short_current > ma_long_current
        bearish_cross = ma_short_prev >= ma_long_prev and ma_short_current < ma_long_current
        
        # Calculate signal strength based on MA separation
        separation_pct = abs((ma_short_current - ma_long_current) / ma_long_current) * 100
        strength = min(separation_pct / 2, 1.0)  # Cap at 1.0
        
        indicators = {
            "ma_short": ma_short_current,
            "ma_long": ma_long_current,
            "separation_pct": separation_pct
        }
        
        if bullish_cross:
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                f"Bullish MA crossover: {short_window} MA crossed above {long_window} MA"
            )
        elif bearish_cross:
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                f"Bearish MA crossover: {short_window} MA crossed below {long_window} MA"
            )
        elif ma_short_current > ma_long_current and current_position and current_position.get('is_open'):
            return StrategySignal("HOLD", 0.5, current_price, indicators, "In bullish trend, holding")
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "No crossover signal")
    
    # ==================== STRATEGY 2: RSI Oversold/Overbought ====================
    
    def rsi_strategy(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy when RSI crosses above oversold, sell when crosses below overbought
        
        Required params:
        - period: RSI period (e.g., 14)
        - oversold: Oversold level (e.g., 30)
        - overbought: Overbought level (e.g., 70)
        """
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        if len(price_data) < period + 1:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Calculate RSI
        delta = price_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        price_data['RSI'] = 100 - (100 / (1 + rs))
        
        current_price = float(price_data['close'].iloc[-1])
        rsi_current = float(price_data['RSI'].iloc[-1])
        rsi_prev = float(price_data['RSI'].iloc[-2])
        
        indicators = {"rsi": rsi_current, "oversold": oversold, "overbought": overbought}
        
        # Buy signal: RSI crosses above oversold
        if rsi_prev <= oversold and rsi_current > oversold:
            strength = (oversold - rsi_current) / oversold if rsi_current < 50 else 0.5
            return StrategySignal(
                "BUY", min(abs(strength), 1.0), current_price, indicators,
                f"RSI crossed above oversold ({rsi_current:.1f})"
            )
        
        # Sell signal: RSI crosses below overbought
        elif rsi_prev >= overbought and rsi_current < overbought:
            strength = (rsi_current - overbought) / (100 - overbought)
            return StrategySignal(
                "SELL", min(abs(strength), 1.0), current_price, indicators,
                f"RSI crossed below overbought ({rsi_current:.1f})"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, f"RSI neutral ({rsi_current:.1f})")
    
    # ==================== STRATEGY 3: Bollinger Bands ====================
    
    def bollinger_bands_strategy(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy when price touches lower band, sell when touches upper band
        
        Required params:
        - period: BB period (e.g., 20)
        - std_dev: Standard deviations (e.g., 2)
        """
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        
        if len(price_data) < period:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Calculate Bollinger Bands
        price_data['BB_middle'] = price_data['close'].rolling(window=period).mean()
        price_data['BB_std'] = price_data['close'].rolling(window=period).std()
        price_data['BB_upper'] = price_data['BB_middle'] + (price_data['BB_std'] * std_dev)
        price_data['BB_lower'] = price_data['BB_middle'] - (price_data['BB_std'] * std_dev)
        
        current_price = float(price_data['close'].iloc[-1])
        bb_upper = float(price_data['BB_upper'].iloc[-1])
        bb_middle = float(price_data['BB_middle'].iloc[-1])
        bb_lower = float(price_data['BB_lower'].iloc[-1])
        
        # Calculate position relative to bands
        bb_width = bb_upper - bb_lower
        price_position = (current_price - bb_lower) / bb_width
        
        indicators = {
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "price_position": price_position
        }
        
        # Buy signal: Price at or below lower band
        if current_price <= bb_lower * 1.01:  # 1% tolerance
            strength = max(0, (bb_lower - current_price) / bb_lower)
            return StrategySignal(
                "BUY", min(strength * 2, 1.0), current_price, indicators,
                "Price at lower Bollinger Band (oversold)"
            )
        
        # Sell signal: Price at or above upper band
        elif current_price >= bb_upper * 0.99:
            strength = max(0, (current_price - bb_upper) / bb_upper)
            return StrategySignal(
                "SELL", min(strength * 2, 1.0), current_price, indicators,
                "Price at upper Bollinger Band (overbought)"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Price within bands")
    
    # ==================== STRATEGY 4: MACD Crossover ====================
    
    def macd_crossover(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy when MACD crosses above signal line, sell when crosses below
        
        Required params:
        - fast_period: Fast EMA (e.g., 12)
        - slow_period: Slow EMA (e.g., 26)
        - signal_period: Signal line (e.g., 9)
        """
        fast = params.get('fast_period', 12)
        slow = params.get('slow_period', 26)
        signal = params.get('signal_period', 9)
        
        if len(price_data) < slow + signal:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Calculate MACD
        ema_fast = price_data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = price_data['close'].ewm(span=slow, adjust=False).mean()
        price_data['MACD'] = ema_fast - ema_slow
        price_data['MACD_signal'] = price_data['MACD'].ewm(span=signal, adjust=False).mean()
        price_data['MACD_hist'] = price_data['MACD'] - price_data['MACD_signal']
        
        current_price = float(price_data['close'].iloc[-1])
        macd_current = float(price_data['MACD'].iloc[-1])
        signal_current = float(price_data['MACD_signal'].iloc[-1])
        hist_current = float(price_data['MACD_hist'].iloc[-1])
        
        macd_prev = float(price_data['MACD'].iloc[-2])
        signal_prev = float(price_data['MACD_signal'].iloc[-2])
        
        indicators = {
            "macd": macd_current,
            "signal": signal_current,
            "histogram": hist_current
        }
        
        # Bullish crossover
        if macd_prev <= signal_prev and macd_current > signal_current:
            strength = min(abs(hist_current) / 2, 1.0)
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                "Bullish MACD crossover"
            )
        
        # Bearish crossover
        elif macd_prev >= signal_prev and macd_current < signal_current:
            strength = min(abs(hist_current) / 2, 1.0)
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                "Bearish MACD crossover"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "No MACD crossover")
    
    # ==================== STRATEGY 5: Volume Breakout ====================
    
    def volume_breakout(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy on high volume with price increase, sell on high volume with price decrease
        
        Required params:
        - volume_threshold: Volume multiplier (e.g., 2.0 = 2x average)
        - lookback_period: Period for average volume (e.g., 20)
        """
        threshold = params.get('volume_threshold', 2.0)
        lookback = params.get('lookback_period', 20)
        
        if len(price_data) < lookback:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Calculate average volume
        price_data['avg_volume'] = price_data['volume'].rolling(window=lookback).mean()
        
        current_price = float(price_data['close'].iloc[-1])
        prev_price = float(price_data['close'].iloc[-2])
        current_volume = float(price_data['volume'].iloc[-1])
        avg_volume = float(price_data['avg_volume'].iloc[-1])
        
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        volume_ratio = current_volume / avg_volume
        
        indicators = {
            "current_volume": current_volume,
            "avg_volume": avg_volume,
            "volume_ratio": volume_ratio,
            "price_change_pct": price_change_pct
        }
        
        # High volume + price increase = BUY
        if volume_ratio >= threshold and price_change_pct > 1:
            strength = min(volume_ratio / (threshold * 2), 1.0)
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                f"Volume breakout: {volume_ratio:.1f}x average with +{price_change_pct:.1f}% price"
            )
        
        # High volume + price decrease = SELL
        elif volume_ratio >= threshold and price_change_pct < -1:
            strength = min(volume_ratio / (threshold * 2), 1.0)
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                f"Volume breakout: {volume_ratio:.1f}x average with {price_change_pct:.1f}% price"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "No volume breakout")
    
    # ==================== STRATEGY 6: Mean Reversion ====================
    
    def mean_reversion(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy when price deviates below mean, sell when above mean
        
        Required params:
        - period: Period for mean (e.g., 20)
        - std_threshold: Std dev threshold (e.g., 2)
        """
        period = params.get('period', 20)
        std_threshold = params.get('std_threshold', 2)
        
        if len(price_data) < period:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        price_data['mean'] = price_data['close'].rolling(window=period).mean()
        price_data['std'] = price_data['close'].rolling(window=period).std()
        
        current_price = float(price_data['close'].iloc[-1])
        mean = float(price_data['mean'].iloc[-1])
        std = float(price_data['std'].iloc[-1])
        
        # Z-score
        z_score = (current_price - mean) / std if std > 0 else 0
        
        indicators = {"mean": mean, "std": std, "z_score": z_score}
        
        # Buy when significantly below mean
        if z_score < -std_threshold:
            strength = min(abs(z_score) / (std_threshold * 2), 1.0)
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                f"Price {abs(z_score):.1f} std devs below mean (oversold)"
            )
        
        # Sell when significantly above mean
        elif z_score > std_threshold:
            strength = min(z_score / (std_threshold * 2), 1.0)
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                f"Price {z_score:.1f} std devs above mean (overbought)"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Price near mean")
    
    # ==================== STRATEGY 7: Momentum ====================
    
    def momentum_strategy(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy on strong upward momentum, sell on strong downward momentum
        
        Required params:
        - period: Lookback period (e.g., 10)
        - threshold: Momentum threshold % (e.g., 5)
        """
        period = params.get('period', 10)
        threshold = params.get('threshold', 5)
        
        if len(price_data) < period:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        current_price = float(price_data['close'].iloc[-1])
        past_price = float(price_data['close'].iloc[-period])
        
        momentum_pct = ((current_price - past_price) / past_price) * 100
        
        indicators = {"momentum_pct": momentum_pct, "threshold": threshold}
        
        # Strong upward momentum
        if momentum_pct > threshold:
            strength = min(momentum_pct / (threshold * 2), 1.0)
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                f"Strong upward momentum: +{momentum_pct:.1f}%"
            )
        
        # Strong downward momentum
        elif momentum_pct < -threshold:
            strength = min(abs(momentum_pct) / (threshold * 2), 1.0)
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                f"Strong downward momentum: {momentum_pct:.1f}%"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Momentum neutral")
    
    # ==================== STRATEGY 8: Support/Resistance ====================
    
    def support_resistance(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy at support, sell at resistance
        
        Required params:
        - lookback_period: Period to find levels (e.g., 50)
        - tolerance: Price tolerance % (e.g., 2)
        """
        lookback = params.get('lookback_period', 50)
        tolerance_pct = params.get('tolerance', 2)
        
        if len(price_data) < lookback:
            return StrategySignal("HOLD", 0.0, price_data['close'].iloc[-1], {}, "Insufficient data")
        
        # Find support and resistance
        recent_data = price_data.iloc[-lookback:]
        support = float(recent_data['low'].min())
        resistance = float(recent_data['high'].max())
        
        current_price = float(price_data['close'].iloc[-1])
        
        tolerance = current_price * (tolerance_pct / 100)
        
        indicators = {"support": support, "resistance": resistance, "tolerance_pct": tolerance_pct}
        
        # At support
        if abs(current_price - support) <= tolerance:
            strength = 0.7
            return StrategySignal(
                "BUY", strength, current_price, indicators,
                f"Price at support level (${support:.2f})"
            )
        
        # At resistance
        elif abs(current_price - resistance) <= tolerance:
            strength = 0.7
            return StrategySignal(
                "SELL", strength, current_price, indicators,
                f"Price at resistance level (${resistance:.2f})"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Price between support/resistance")
    
    # ==================== STRATEGY 9: Grid Trading ====================
    
    def grid_trading(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Place buy/sell orders at predetermined price levels
        
        Required params:
        - grid_levels: Number of grid levels (e.g., 5)
        - grid_spacing_pct: Spacing between levels % (e.g., 2)
        """
        grid_levels = params.get('grid_levels', 5)
        spacing_pct = params.get('grid_spacing_pct', 2)
        
        current_price = float(price_data['close'].iloc[-1])
        
        # Calculate grid
        base_price = current_price
        grid = []
        for i in range(-grid_levels, grid_levels + 1):
            grid.append(base_price * (1 + (i * spacing_pct / 100)))
        
        # Find closest grid level
        closest_level = min(grid, key=lambda x: abs(x - current_price))
        distance_pct = abs((current_price - closest_level) / closest_level) * 100
        
        indicators = {
            "grid_levels": grid,
            "closest_level": closest_level,
            "distance_pct": distance_pct
        }
        
        # If price dropped to lower grid level, buy
        if current_price < closest_level * 0.99:
            return StrategySignal(
                "BUY", 0.6, current_price, indicators,
                f"Grid buy at ${closest_level:.2f}"
            )
        
        # If price rose to upper grid level, sell
        elif current_price > closest_level * 1.01:
            return StrategySignal(
                "SELL", 0.6, current_price, indicators,
                f"Grid sell at ${closest_level:.2f}"
            )
        
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Between grid levels")
    
    # ==================== STRATEGY 10: Dollar Cost Averaging (DCA) ====================
    
    def dollar_cost_averaging(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Buy fixed amount at regular intervals regardless of price
        
        Required params:
        - buy_interval: Interval in candles (e.g., 20 = every 20 periods)
        - buy_amount: Fixed $ amount to buy
        """
        buy_interval = params.get('buy_interval', 20)
        buy_amount = params.get('buy_amount', 100)
        
        current_price = float(price_data['close'].iloc[-1])
        
        # Check if it's time to buy (simplified - in real impl track last buy)
        candles_since_start = len(price_data)
        is_buy_time = (candles_since_start % buy_interval) == 0
        
        indicators = {
            "buy_interval": buy_interval,
            "buy_amount": buy_amount,
            "candles_count": candles_since_start
        }
        
        if is_buy_time:
            return StrategySignal(
                "BUY", 1.0, current_price, indicators,
                f"DCA: Time to buy ${buy_amount}"
            )
        else:
            return StrategySignal("HOLD", 0.0, current_price, indicators, "Waiting for next DCA interval")
    # ==================== STRATEGY 11: RAPID TEST ====================
    def rapid_test_strategy(
        self,
        params: Dict[str, Any],
        price_data: pd.DataFrame,
        current_position: Optional[Dict] = None
    ) -> StrategySignal:
        """
        Generates random signals for rapid testing of bot execution.
        More realistic with varied actions and strengths.
        """
        import random
        import numpy as np
        
        current_price = float(price_data['close'].iloc[-1])
        indicators = {
            "test_signal": "rapid_test",
            "volatility": float(price_data['close'].pct_change().std() * 100)
        }
        
        open_positions = current_position.get('open_positions', 0) if current_position else 0
        
        # Determine action based on probabilities
        if open_positions > 0:
            # When we have open positions, higher chance to SELL
            weights = [0.2, 0.6, 0.2]  # 20% BUY, 60% SELL, 20% HOLD
        else:
            # When no positions, balanced chance
            weights = [0.4, 0.3, 0.3]  # 40% BUY, 30% SELL, 30% HOLD
        
        actions = ["BUY", "SELL", "HOLD"]
        action = random.choices(actions, weights=weights, k=1)[0]
        
        # Generate appropriate strength
        if action == "HOLD":
            strength = random.uniform(0.0, 0.3)
            reason = f"Holding - {open_positions} open positions"
        else:
            # Stronger signals when fewer positions open
            if action == "BUY":
                max_positions = params.get('max_open_trades', 3)
                position_ratio = open_positions / max_positions if max_positions > 0 else 0
                # Less likely to buy when near max positions
                base_strength = 0.7 * (1 - position_ratio)
                strength = random.uniform(base_strength, 0.9)
                reason = f"Buy signal - {open_positions}/{max_positions} positions"
            else:  # SELL
                # Stronger sell signal when we have positions
                if open_positions > 0:
                    strength = random.uniform(0.6, 1.0)
                    reason = f"Sell signal - Closing 1 of {open_positions} positions"
                else:
                    strength = random.uniform(0.3, 0.6)
                    reason = "Sell signal (no positions to close)"
        
        return StrategySignal(
            action,
            strength,
            current_price,
            indicators,
            reason
        )


# Singleton instance
strategy_engine = StrategyEngine()
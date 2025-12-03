"""
Bot Configuration Examples
Save as: examples/bot_examples.py

These examples show how to create different types of trading bots
"""

# ==================== Example 1: Conservative MA Crossover Bot ====================

conservative_ma_bot = {
    "name": "Conservative Trend Follower",
    "description": "Low-risk MA crossover strategy for long-term trends",
    "strategy_type": "MA_CROSSOVER",
    "strategy_params": {
        "short_window": 10,
        "long_window": 50
    },
    "symbol": "AAPL",
    "asset_type": "STOCK",
    "max_position_size": 500.0,      # $500 per trade
    "stop_loss_pct": 3.0,             # 3% stop loss
    "take_profit_pct": 10.0,          # 10% take profit
    "max_daily_trades": 5,
    "max_daily_loss": 200.0,          # Max $200 loss per day
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "1h"                  # Check every hour
}

# ==================== Example 2: Aggressive RSI Scalper ====================

aggressive_rsi_bot = {
    "name": "RSI Scalper Pro",
    "description": "High-frequency RSI scalping for quick profits",
    "strategy_type": "RSI_OVERSOLD_OVERBOUGHT",
    "strategy_params": {
        "period": 14,
        "oversold": 25,               # More aggressive entry
        "overbought": 75              # More aggressive exit
    },
    "symbol": "TSLA",
    "asset_type": "STOCK",
    "max_position_size": 1000.0,
    "stop_loss_pct": 1.5,             # Tight stop loss
    "take_profit_pct": 3.0,           # Quick profit target
    "max_daily_trades": 20,           # Many trades allowed
    "max_daily_loss": 500.0,
    "use_leverage": True,             # Use 2x leverage
    "leverage": 2.0,
    "interval": "5m"                  # Very active - check every 5 minutes
}

# ==================== Example 3: Crypto Bollinger Bands Bot ====================

crypto_bb_bot = {
    "name": "BTC Bollinger Reverter",
    "description": "Mean reversion on Bitcoin using Bollinger Bands",
    "strategy_type": "BOLLINGER_BANDS",
    "strategy_params": {
        "period": 20,
        "std_dev": 2.5                # Wider bands for crypto volatility
    },
    "symbol": "BTCUSDT",
    "asset_type": "CRYPTO",
    "max_position_size": 2000.0,
    "stop_loss_pct": 5.0,             # Wider stops for crypto
    "take_profit_pct": 8.0,
    "max_daily_trades": 10,
    "max_daily_loss": 1000.0,
    "use_leverage": True,
    "leverage": 3.0,                  # 3x leverage for crypto
    "interval": "15m"
}

# ==================== Example 4: MACD Momentum Trader ====================

macd_momentum_bot = {
    "name": "MACD Momentum Master",
    "description": "Rides strong trends using MACD crossovers",
    "strategy_type": "MACD_CROSSOVER",
    "strategy_params": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    },
    "symbol": "GOOGL",
    "asset_type": "STOCK",
    "max_position_size": 1500.0,
    "stop_loss_pct": 2.5,
    "take_profit_pct": 7.0,
    "max_daily_trades": 8,
    "max_daily_loss": 400.0,
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "1h"
}

# ==================== Example 5: Volume Breakout Hunter ====================

volume_breakout_bot = {
    "name": "Breakout Hunter",
    "description": "Catches explosive moves with volume confirmation",
    "strategy_type": "VOLUME_BREAKOUT",
    "strategy_params": {
        "volume_threshold": 2.5,      # 2.5x average volume
        "lookback_period": 20
    },
    "symbol": "NVDA",
    "asset_type": "STOCK",
    "max_position_size": 800.0,
    "stop_loss_pct": 2.0,
    "take_profit_pct": 6.0,
    "max_daily_trades": 15,
    "max_daily_loss": 600.0,
    "use_leverage": True,
    "leverage": 2.0,
    "interval": "5m"                  # Quick reaction to breakouts
}

# ==================== Example 6: Grid Trading Bot ====================

grid_trading_bot = {
    "name": "Grid Profit Maker",
    "description": "Profits from sideways market with grid strategy",
    "strategy_type": "GRID_TRADING",
    "strategy_params": {
        "grid_levels": 10,            # 10 levels above and below
        "grid_spacing_pct": 1.5       # 1.5% spacing between levels
    },
    "symbol": "SPY",
    "asset_type": "STOCK",
    "max_position_size": 500.0,       # Small positions for many trades
    "stop_loss_pct": None,            # No stop loss for grid trading
    "take_profit_pct": None,          # No take profit - grid handles it
    "max_daily_trades": 50,           # Many small trades
    "max_daily_loss": 300.0,
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "15m"
}

# ==================== Example 7: Dollar Cost Averaging Bot ====================

dca_bot = {
    "name": "BTC DCA Accumulator",
    "description": "Systematically accumulates Bitcoin over time",
    "strategy_type": "DCA",
    "strategy_params": {
        "buy_interval": 24,           # Buy every 24 hours (if using 1h interval)
        "buy_amount": 100.0           # $100 per buy
    },
    "symbol": "BTCUSDT",
    "asset_type": "CRYPTO",
    "max_position_size": 100.0,
    "stop_loss_pct": None,            # Hold long-term
    "take_profit_pct": None,
    "max_daily_trades": 2,
    "max_daily_loss": 1000.0,         # High limit - we're buying dips
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "1h"
}

# ==================== Example 8: Mean Reversion Specialist ====================

mean_reversion_bot = {
    "name": "Mean Reversion Master",
    "description": "Profits from overextended price movements",
    "strategy_type": "MEAN_REVERSION",
    "strategy_params": {
        "period": 30,
        "std_threshold": 2.0          # Entry at 2 standard deviations
    },
    "symbol": "MSFT",
    "asset_type": "STOCK",
    "max_position_size": 1200.0,
    "stop_loss_pct": 3.0,
    "take_profit_pct": 5.0,
    "max_daily_trades": 6,
    "max_daily_loss": 500.0,
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "1h"
}

# ==================== Example 9: High-Frequency Momentum Bot ====================

hf_momentum_bot = {
    "name": "Momentum Surfer",
    "description": "Rides short-term momentum waves",
    "strategy_type": "MOMENTUM",
    "strategy_params": {
        "period": 5,                  # Very short lookback
        "threshold": 3.0              # 3% momentum threshold
    },
    "symbol": "AMD",
    "asset_type": "STOCK",
    "max_position_size": 600.0,
    "stop_loss_pct": 1.0,             # Very tight stops
    "take_profit_pct": 2.5,           # Quick profits
    "max_daily_trades": 30,
    "max_daily_loss": 400.0,
    "use_leverage": True,
    "leverage": 2.0,
    "interval": "5m"
}

# ==================== Example 10: Support/Resistance Trader ====================

support_resistance_bot = {
    "name": "Level Trader Pro",
    "description": "Trades key support and resistance levels",
    "strategy_type": "SUPPORT_RESISTANCE",
    "strategy_params": {
        "lookback_period": 100,       # Long lookback for solid levels
        "tolerance": 1.5              # 1.5% tolerance around levels
    },
    "symbol": "AMZN",
    "asset_type": "STOCK",
    "max_position_size": 1000.0,
    "stop_loss_pct": 2.0,
    "take_profit_pct": 5.0,
    "max_daily_trades": 10,
    "max_daily_loss": 500.0,
    "use_leverage": False,
    "leverage": 1.0,
    "interval": "1h"
}

# ==================== Example 11: Multi-Symbol Portfolio Bot ====================
# Note: Current implementation supports single symbol, but here's how you'd structure it

portfolio_bot_config = {
    "name": "Diversified Portfolio Bot",
    "description": "Manages a basket of stocks with MA crossover",
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],  # Multiple symbols
    "strategy_type": "MA_CROSSOVER",
    "strategy_params": {
        "short_window": 10,
        "long_window": 30
    },
    "max_position_size_per_symbol": 500.0,
    "total_portfolio_limit": 2000.0,
    "stop_loss_pct": 3.0,
    "take_profit_pct": 8.0,
    "rebalance_interval": "1d"
}

# ==================== Example Bot Creation Functions ====================

def create_bot_via_api(bot_config: dict, api_token: str, api_url: str = "http://localhost:8000"):
    """
    Helper function to create a bot via API
    
    Usage:
        token = "your_jwt_token"
        bot = create_bot_via_api(conservative_ma_bot, token)
    """
    import requests
    
    response = requests.post(
        f"{api_url}/api/v1/bots/",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        },
        json=bot_config
    )
    
    if response.status_code == 201:
        print(f"✅ Bot created successfully: {response.json()['name']}")
        return response.json()
    else:
        print(f"❌ Failed to create bot: {response.text}")
        return None


def create_multiple_bots(configs: list, api_token: str):
    """
    Create multiple bots at once
    
    Usage:
        bots = [conservative_ma_bot, aggressive_rsi_bot, crypto_bb_bot]
        create_multiple_bots(bots, token)
    """
    created_bots = []
    
    for config in configs:
        bot = create_bot_via_api(config, api_token)
        if bot:
            created_bots.append(bot)
    
    print(f"\n📊 Created {len(created_bots)} bots successfully")
    return created_bots


def backtest_bot(bot_id: int, api_token: str, days: int = 30):
    """
    Run backtest on a bot
    
    Usage:
        results = backtest_bot(bot_id=1, api_token=token, days=90)
    """
    import requests
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    response = requests.post(
        f"http://localhost:8000/api/v1/bots/{bot_id}/backtest",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        },
        json={
            "start_date": start_date.isoformat() + "Z",
            "end_date": end_date.isoformat() + "Z",
            "initial_capital": 10000.0
        }
    )
    
    if response.status_code == 202:
        results = response.json()
        print(f"\n📈 Backtest Results for Bot {bot_id}:")
        print(f"  Total Return: ${results['total_return']:.2f} ({results['total_return_pct']:.2f}%)")
        print(f"  Win Rate: {results['win_rate']:.1f}%")
        print(f"  Total Trades: {results['total_trades']}")
        print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        return results
    else:
        print(f"❌ Backtest failed: {response.text}")
        return None


# ==================== Bot Strategy Comparison ====================

def compare_strategies(symbol: str, api_token: str, strategies: list = None):
    """
    Create and backtest multiple strategies on the same symbol to compare
    
    Usage:
        compare_strategies("AAPL", token)
    """
    if strategies is None:
        strategies = [
            conservative_ma_bot,
            aggressive_rsi_bot,
            macd_momentum_bot,
            mean_reversion_bot
        ]
    
    results = []
    
    for config in strategies:
        # Update symbol
        config['symbol'] = symbol
        
        # Create bot
        bot = create_bot_via_api(config, api_token)
        if not bot:
            continue
        
        # Run backtest
        backtest = backtest_bot(bot['id'], api_token, days=90)
        if backtest:
            results.append({
                'strategy': config['strategy_type'],
                'name': config['name'],
                'return_pct': backtest['total_return_pct'],
                'win_rate': backtest['win_rate'],
                'sharpe': backtest['sharpe_ratio'],
                'max_drawdown': backtest['max_drawdown_pct']
            })
    
    # Print comparison
    print(f"\n🏆 Strategy Comparison for {symbol}:")
    print("-" * 80)
    print(f"{'Strategy':<30} {'Return %':<12} {'Win Rate':<12} {'Sharpe':<12} {'Max DD %'}")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['return_pct'], reverse=True):
        print(f"{r['name']:<30} {r['return_pct']:>10.2f}% {r['win_rate']:>10.1f}% {r['sharpe']:>10.2f} {r['max_drawdown']:>10.2f}%")
    
    return results


# ==================== Usage Examples ====================

if __name__ == "__main__":
    """
    Example usage - uncomment to test
    """
    
    # Set your API token
    API_TOKEN = "your_jwt_token_here"
    
    # Example 1: Create a single bot
    # bot = create_bot_via_api(conservative_ma_bot, API_TOKEN)
    
    # Example 2: Create multiple bots
    # bots = [conservative_ma_bot, crypto_bb_bot, dca_bot]
    # created = create_multiple_bots(bots, API_TOKEN)
    
    # Example 3: Backtest a bot
    # backtest_bot(bot_id=1, api_token=API_TOKEN, days=90)
    
    # Example 4: Compare strategies
    # compare_strategies("AAPL", API_TOKEN)
    
    print("✨ Bot examples loaded! Set your API_TOKEN and uncomment examples to use.")


# ==================== Advanced Bot Configurations ====================

# Combine multiple strategies in sequence
multi_strategy_approach = """
Strategy: Create multiple bots with different strategies on the same symbol

1. Conservative Entry Bot (MA Crossover) - Identifies trends
2. Scalping Bot (RSI) - Takes quick profits within trend
3. Breakout Bot (Volume) - Catches explosive moves
4. DCA Bot - Accumulates on dips

Each bot operates independently but can be monitored as a portfolio.
"""

# Risk management configurations
risk_profiles = {
    "conservative": {
        "max_position_size": 500,
        "leverage": 1.0,
        "stop_loss_pct": 3.0,
        "max_daily_trades": 5,
        "max_daily_loss": 200
    },
    "moderate": {
        "max_position_size": 1000,
        "leverage": 2.0,
        "stop_loss_pct": 2.0,
        "max_daily_trades": 10,
        "max_daily_loss": 500
    },
    "aggressive": {
        "max_position_size": 2000,
        "leverage": 5.0,
        "stop_loss_pct": 1.5,
        "max_daily_trades": 30,
        "max_daily_loss": 1000
    }
}

# Time-based strategy switching
time_based_config = """
Strategy: Switch strategies based on market conditions

Morning (9:30-11:00 AM): Volume Breakout (catch opening volatility)
Midday (11:00 AM-2:00 PM): Mean Reversion (range-bound trading)
Afternoon (2:00-4:00 PM): Momentum (trend following)

Implement by creating separate bots with different active hours.
"""
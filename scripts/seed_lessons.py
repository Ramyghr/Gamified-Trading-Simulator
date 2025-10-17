"""
Enhanced Seed Script for Trading Education Platform
Creates comprehensive lessons with real sources and detailed content
Run after migration to populate initial learning content
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.lesson import Lesson, LessonQuizQuestion
from app.config.database import SessionLocal, engine, Base
from app.models import User, Lesson, UserLessonProgress, UserXP, Watchlist
from app.models.user_xp import XPTransaction

def create_comprehensive_lessons():
    """Create comprehensive lessons with real sources and detailed content"""
    db: Session = SessionLocal()
    
    try:
        lessons_data = [
            # ========== CHAPTER 1: TRADING FUNDAMENTALS ==========
            {
                "title": "What is Trading? A Complete Introduction",
                "description": "Comprehensive introduction to trading, markets, and how they function in the modern economy",
                "chapter": 1,
                "order": 1,
                "type": "video",
                "difficulty": "beginner",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=p7HKvqRI_Bo",
                    "video_title": "Stock Market For Beginners 2024",
                    "channel": "ClearValue Tax",
                    "duration": "15:42",
                    "source": "YouTube - ClearValue Tax",
                    "source_url": "https://www.youtube.com/watch?v=p7HKvqRI_Bo",
                    "key_topics": [
                        "Definition of trading vs investing",
                        "How stock markets operate",
                        "Role of exchanges (NYSE, NASDAQ)",
                        "Market participants",
                        "Basic terminology"
                    ],
                    "learning_objectives": [
                        "Understand the difference between trading and investing",
                        "Learn how stock exchanges facilitate trading",
                        "Identify key market participants",
                        "Master basic trading terminology"
                    ]
                },
                "duration_minutes": 16,
                "xp_reward": 100,
                "coin_reward": 50,
                "required_level": 1,
                "is_published": True,
                "tags": ["basics", "introduction", "trading-101", "markets"]
            },
            
            {
                "title": "Understanding Stocks and Equity Markets",
                "description": "Deep dive into what stocks represent, how they're valued, and why people invest in them",
                "chapter": 1,
                "order": 2,
                "type": "reading",
                "difficulty": "beginner",
                "content": {
                    "markdown": """
# Understanding Stocks and Equity Markets

## What is a Stock?

A stock (also called equity or share) represents **fractional ownership** in a company. When you purchase stock, you become a shareholder and own a piece of that business.

### Key Characteristics:
- **Ownership Rights**: You have a claim on the company's assets and earnings
- **Voting Rights**: Most stocks allow you to vote on company decisions
- **Profit Sharing**: You may receive dividends (portions of company profits)
- **Capital Appreciation**: Stock value can increase as the company grows

## Types of Stocks

### Common Stock
- **Voting Rights**: Shareholders can vote on board members and corporate policies
- **Dividends**: Variable and not guaranteed; paid after preferred shareholders
- **Liquidation**: Last in line if company liquidates
- **Growth Potential**: Unlimited upside potential

### Preferred Stock
- **Fixed Dividends**: Regular, predetermined dividend payments
- **Priority**: Paid before common stockholders
- **Limited Voting**: Usually no voting rights
- **Convertible**: Sometimes can be converted to common stock

## Why Do Stock Prices Change?

Stock prices fluctuate based on **supply and demand**, influenced by:

### Company-Specific Factors
- Earnings reports and financial performance
- Product launches and innovations
- Management changes
- Mergers and acquisitions
- Legal issues or scandals

### Market-Wide Factors
- Economic indicators (GDP, unemployment, inflation)
- Interest rate changes by central banks
- Political events and policy changes
- Global events and geopolitical tensions
- Market sentiment and investor psychology

### Technical Factors
- Trading volume and liquidity
- Short interest and institutional holdings
- Market trends and momentum
- Support and resistance levels

## How Stocks Are Valued

### Fundamental Valuation Metrics
- **P/E Ratio** (Price-to-Earnings): Stock price ÷ Earnings per share
- **P/B Ratio** (Price-to-Book): Market value ÷ Book value
- **Dividend Yield**: Annual dividend ÷ Stock price
- **EPS** (Earnings Per Share): Net income ÷ Outstanding shares

### Market Capitalization Categories
- **Large Cap**: > $10 billion (More stable, lower growth)
- **Mid Cap**: $2-10 billion (Balanced risk/reward)
- **Small Cap**: $300M-2B (Higher risk, higher growth potential)
- **Micro Cap**: < $300M (Very high risk/reward)

## Stock Market Indices

Major indices track market performance:
- **S&P 500**: 500 largest US companies
- **Dow Jones Industrial Average**: 30 major US companies
- **NASDAQ Composite**: Technology-heavy index
- **Russell 2000**: Small-cap stocks

## Getting Started with Stocks

1. **Open a Brokerage Account**: Research platforms (Fidelity, Charles Schwab, Robinhood)
2. **Research Companies**: Read financial statements, analyst reports
3. **Start Small**: Begin with fractional shares or ETFs
4. **Diversify**: Don't put all eggs in one basket
5. **Think Long-Term**: Focus on quality companies and time horizon

---

**Sources:**
- Investopedia: "Stock Market Basics" - https://www.investopedia.com/terms/s/stock.asp
- SEC Investor Education: "Stocks" - https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks
- The Motley Fool: "How to Invest in Stocks" - https://www.fool.com/investing/how-to-invest/stocks/
                    """,
                    "external_links": [
                        {
                            "title": "SEC's Guide to Stock Investing",
                            "url": "https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks",
                            "description": "Official SEC investor education resource"
                        },
                        {
                            "title": "Investopedia Stock Basics",
                            "url": "https://www.investopedia.com/terms/s/stock.asp",
                            "description": "Comprehensive guide to understanding stocks"
                        }
                    ]
                },
                "duration_minutes": 15,
                "xp_reward": 150,
                "coin_reward": 75,
                "required_level": 1,
                "is_published": True,
                "tags": ["stocks", "basics", "equity", "valuation"]
            },
            
            {
                "title": "How the Stock Market Works",
                "description": "Learn about market mechanics, order types, and the trading process",
                "chapter": 1,
                "order": 3,
                "type": "video",
                "difficulty": "beginner",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=F3QpgXBtDeo",
                    "video_title": "How Does the Stock Market Work?",
                    "channel": "Kurzgesagt – In a Nutshell",
                    "source": "YouTube - Kurzgesagt",
                    "source_url": "https://www.youtube.com/watch?v=F3QpgXBtDeo",
                    "key_topics": [
                        "Primary vs secondary markets",
                        "Role of market makers",
                        "Bid-ask spread",
                        "Order execution process",
                        "Market vs limit orders"
                    ]
                },
                "duration_minutes": 6,
                "xp_reward": 120,
                "coin_reward": 60,
                "required_level": 1,
                "is_published": True,
                "tags": ["market-mechanics", "orders", "basics"]
            },
            
            {
                "title": "Order Types and Execution",
                "description": "Master different order types and when to use each one",
                "chapter": 1,
                "order": 4,
                "type": "reading",
                "difficulty": "beginner",
                "content": {
                    "markdown": """
# Order Types and Execution

## Basic Order Types

### Market Order
- **Definition**: Buy/sell immediately at current market price
- **Pros**: Guaranteed execution, fast
- **Cons**: Price uncertainty (slippage)
- **When to Use**: Liquid stocks, need immediate execution

### Limit Order
- **Definition**: Buy/sell at specified price or better
- **Pros**: Price control, no slippage
- **Cons**: May not execute
- **When to Use**: Specific price targets, less liquid stocks

### Stop-Loss Order
- **Definition**: Triggers market order when price hits stop level
- **Pros**: Limits losses automatically
- **Cons**: Slippage possible, false triggers
- **When to Use**: Risk management, position protection

### Stop-Limit Order
- **Definition**: Becomes limit order when stop price hit
- **Pros**: Price protection after stop triggered
- **Cons**: May not execute in fast markets
- **When to Use**: Volatile stocks, precise exit control

## Advanced Order Types

### Trailing Stop
- Automatically adjusts stop price as stock moves favorably
- Locks in profits while allowing upside
- Example: 5% trailing stop moves up but never down

### Good-Till-Cancelled (GTC)
- Order stays active until executed or cancelled
- Can remain open for weeks/months
- Check broker's specific GTC duration limits

### Fill-or-Kill (FOK)
- Execute entire order immediately or cancel
- Used for large orders requiring immediate full execution

### Immediate-or-Cancel (IOC)
- Execute whatever possible immediately, cancel rest
- Partial fills acceptable

## Order Timing

### Day Order
- Expires at market close if not filled
- Default for most orders

### Extended Hours Trading
- Pre-market: 4:00 AM - 9:30 AM EST
- After-hours: 4:00 PM - 8:00 PM EST
- Lower volume, wider spreads, more volatility

## Best Practices

1. **Use Limit Orders** for entries to control price
2. **Set Stop-Losses** before entering trades
3. **Understand Slippage** costs in fast markets
4. **Check Market Hours** before placing orders
5. **Review Order Status** after placement

---

**Sources:**
- FINRA: "Trading Basics" - https://www.finra.org/investors/learn-to-invest/types-investments/stocks/trading-basics
- Charles Schwab: "Order Types Guide" - https://www.schwab.com/learn/story/how-to-choose-order-type
                    """,
                    "external_links": [
                        {
                            "title": "FINRA Trading Basics",
                            "url": "https://www.finra.org/investors/learn-to-invest/types-investments/stocks/trading-basics",
                            "description": "Official guide to trading basics and order types"
                        }
                    ]
                },
                "duration_minutes": 12,
                "xp_reward": 150,
                "coin_reward": 75,
                "required_level": 1,
                "is_published": True,
                "tags": ["orders", "execution", "trading-basics"]
            },
            
            {
                "title": "Trading Fundamentals Quiz",
                "description": "Test your knowledge of basic trading concepts",
                "chapter": 1,
                "order": 5,
                "type": "quiz",
                "difficulty": "beginner",
                "content": {},
                "duration_minutes": 10,
                "xp_reward": 200,
                "coin_reward": 100,
                "badge_reward": "Trading Novice",
                "required_level": 1,
                "is_published": True,
                "tags": ["quiz", "basics", "assessment"]
            },
            
            # ========== CHAPTER 2: TECHNICAL ANALYSIS BASICS ==========
            {
                "title": "Introduction to Technical Analysis",
                "description": "Learn the foundations of technical analysis and chart reading",
                "chapter": 2,
                "order": 1,
                "type": "video",
                "difficulty": "beginner",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=08c8dKCk4XA",
                    "video_title": "Technical Analysis Secrets",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=08c8dKCk4XA",
                    "key_topics": [
                        "Dow Theory principles",
                        "Trend identification",
                        "Support and resistance",
                        "Chart patterns basics",
                        "Volume analysis"
                    ]
                },
                "duration_minutes": 25,
                "xp_reward": 200,
                "coin_reward": 100,
                "required_level": 2,
                "is_published": True,
                "tags": ["technical-analysis", "charts", "introduction"]
            },
            
            {
                "title": "Understanding Candlestick Patterns",
                "description": "Master Japanese candlesticks and key reversal patterns",
                "chapter": 2,
                "order": 2,
                "type": "reading",
                "difficulty": "beginner",
                "content": {
                    "markdown": """
# Understanding Candlestick Patterns

## Candlestick Anatomy

Each candlestick shows four price points:
- **Open**: First trade price of the period
- **High**: Highest price reached
- **Low**: Lowest price reached
- **Close**: Last trade price of the period

### Components:
- **Body**: Distance between open and close
- **Wicks/Shadows**: Lines above/below body showing high/low
- **Color**: Green/white (bullish), Red/black (bearish)

## Single Candlestick Patterns

### Doji
- Open equals close (or very close)
- Indicates indecision
- Potential reversal signal
- Types: Standard, Long-legged, Dragonfly, Gravestone

### Hammer
- Small body at top, long lower wick
- Appears after downtrend
- Bullish reversal signal
- Lower wick should be 2x body size

### Shooting Star
- Small body at bottom, long upper wick
- Appears after uptrend
- Bearish reversal signal
- Upper wick should be 2x body size

### Spinning Top
- Small body, long wicks both sides
- Shows indecision
- Potential trend change

## Two-Candlestick Patterns

### Bullish Engulfing
- Small red candle followed by larger green candle
- Second candle's body completely engulfs first
- Strong bullish reversal signal
- Best at support levels

### Bearish Engulfing
- Small green candle followed by larger red candle
- Second candle's body completely engulfs first
- Strong bearish reversal signal
- Best at resistance levels

### Tweezer Top/Bottom
- Two candles with same high (top) or low (bottom)
- Shows price rejection at level
- Reversal pattern
- Stronger with other confirmation

### Piercing Pattern (Bullish)
- Red candle followed by green candle
- Green opens below red's low, closes above midpoint
- Bullish reversal in downtrend

### Dark Cloud Cover (Bearish)
- Green candle followed by red candle
- Red opens above green's high, closes below midpoint
- Bearish reversal in uptrend

## Three-Candlestick Patterns

### Morning Star (Bullish)
1. Long red candle (downtrend)
2. Small-bodied candle (indecision)
3. Long green candle (reversal)
- Strong bullish reversal
- Best at support zones

### Evening Star (Bearish)
1. Long green candle (uptrend)
2. Small-bodied candle (indecision)
3. Long red candle (reversal)
- Strong bearish reversal
- Best at resistance zones

### Three White Soldiers (Bullish)
- Three consecutive long green candles
- Each opens within previous body
- Each closes near high
- Strong uptrend continuation

### Three Black Crows (Bearish)
- Three consecutive long red candles
- Each opens within previous body
- Each closes near low
- Strong downtrend continuation

## Continuation Patterns

### Rising Three Methods
- Long green, three small red candles, long green
- Uptrend continuation pattern

### Falling Three Methods
- Long red, three small green candles, long red
- Downtrend continuation pattern

## Best Practices

1. **Confirm with Volume**: Patterns stronger with volume confirmation
2. **Context Matters**: Consider overall trend and market structure
3. **Support/Resistance**: Patterns more reliable at key levels
4. **Multiple Timeframes**: Check pattern on different timeframes
5. **Never Trade in Isolation**: Use with other indicators

## Common Mistakes to Avoid

- Trading every pattern without confirmation
- Ignoring overall market trend
- Using patterns alone without risk management
- Forcing patterns where they don't exist
- Not waiting for pattern completion

---

**Sources:**
- "Japanese Candlestick Charting Techniques" by Steve Nison
- Investopedia: "Candlestick Patterns" - https://www.investopedia.com/trading/candlestick-charting-what-is-it/
- Bulkowski's Pattern Encyclopedia - http://thepatternsite.com/
                    """,
                    "external_links": [
                        {
                            "title": "Investopedia Candlestick Guide",
                            "url": "https://www.investopedia.com/trading/candlestick-charting-what-is-it/",
                            "description": "Comprehensive candlestick pattern reference"
                        }
                    ]
                },
                "duration_minutes": 20,
                "xp_reward": 250,
                "coin_reward": 125,
                "required_level": 2,
                "is_published": True,
                "tags": ["candlesticks", "patterns", "technical-analysis"]
            },
            
            {
                "title": "Support and Resistance Levels",
                "description": "Identify and trade key support and resistance zones",
                "chapter": 2,
                "order": 3,
                "type": "video",
                "difficulty": "beginner",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=1dMhwHHn59w",
                    "video_title": "Support and Resistance Explained",
                    "channel": "The Trading Channel",
                    "source": "YouTube - The Trading Channel",
                    "source_url": "https://www.youtube.com/watch?v=1dMhwHHn59w",
                    "key_topics": [
                        "Identifying support/resistance",
                        "Role reversals",
                        "Trading breakouts",
                        "False breakouts",
                        "Dynamic vs static levels"
                    ]
                },
                "duration_minutes": 18,
                "xp_reward": 200,
                "coin_reward": 100,
                "required_level": 2,
                "is_published": True,
                "tags": ["support-resistance", "levels", "technical-analysis"]
            },
            
            {
                "title": "Trend Lines and Channels",
                "description": "Master drawing and trading trend lines and price channels",
                "chapter": 2,
                "order": 4,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Trend Lines and Channels

## Understanding Trends

### Trend Definition
**Uptrend**: Series of higher highs and higher lows
**Downtrend**: Series of lower highs and lower lows
**Sideways**: Price oscillating between support and resistance

### Trend Timeframes
- **Primary Trend**: Months to years (long-term)
- **Secondary Trend**: Weeks to months (intermediate)
- **Minor Trend**: Days to weeks (short-term)

## Drawing Trend Lines

### Uptrend Line
- Connect at least 2-3 swing lows
- Line should not cut through price bars
- More touches = stronger trend line
- Extension predicts future support

### Downtrend Line
- Connect at least 2-3 swing highs
- Line should not cut through price bars
- More touches = stronger resistance
- Extension predicts future resistance

### Best Practices:
1. Use log scale for long-term trends
2. Draw from left to right
3. Don't force the line - find natural touches
4. Minor penetrations acceptable (3% rule)
5. Redraw as new swing points form

## Trading Trend Lines

### Entry Signals
- **Bounce Entry**: Enter when price touches and bounces off trend line
- **Breakout Entry**: Enter when price breaks through with volume
- **Pullback Entry**: Enter on retest of broken trend line

### Exit Signals
- Break below uptrend line (exit longs)
- Break above downtrend line (exit shorts)
- Price exhaustion at trend line

## Price Channels

### Parallel Channel
- Two parallel lines containing price action
- Connect highs for resistance, lows for support
- Price oscillates between boundaries
- Trade bounces off channel lines

### Ascending Channel (Bullish)
- Higher highs and higher lows
- Buy near lower line, sell near upper line
- Breakout above = continuation signal

### Descending Channel (Bearish)
- Lower highs and lower lows
- Sell near upper line, cover near lower line
- Breakdown below = continuation signal

### Horizontal Channel (Range)
- Flat support and resistance
- Buy support, sell resistance
- Breakout in either direction signals trend change

## Advanced Concepts

### Fibonacci Channels
- Use Fibonacci ratios to project channel widths
- 0.618, 1.0, 1.618 extensions
- Identifies potential reversal zones

### Linear Regression Channel
- Statistical best-fit line through price
- Shows mean and standard deviations
- Helps identify overextended moves

### Pitchfork (Andrews' Pitchfork)
- Three parallel trend lines
- Middle line is median
- Used for support/resistance projections

## Channel Trading Strategies

### Bounce Strategy
1. Identify established channel
2. Wait for price to approach channel line
3. Look for reversal pattern
4. Enter with stop beyond channel line
5. Target opposite channel line

### Breakout Strategy
1. Identify consolidating channel
2. Wait for decisive break with volume
3. Enter on breakout or pullback
4. Target measured move (channel width)
5. Use broken line as stop-loss

## Common Mistakes

- Forcing trend lines where they don't fit
- Using only 2 touches (need at least 3)
- Ignoring volume on breakouts
- Not adjusting lines as trends evolve
- Trading against major trend

## Tools and Resources

- **Charting Platforms**: TradingView, ThinkorSwim
- **Drawing Tools**: Fibonacci retracements, parallel lines
- **Indicators**: Moving averages (dynamic trend lines)

---

**Sources:**
- "Technical Analysis of the Financial Markets" by John Murphy
- StockCharts.com: "Trend Lines" - https://school.stockcharts.com/doku.php?id=chart_analysis:trend_lines
- Investopedia: "Channels" - https://www.investopedia.com/terms/c/channel.asp
                    """,
                    "external_links": [
                        {
                            "title": "StockCharts School - Trend Lines",
                            "url": "https://school.stockcharts.com/doku.php?id=chart_analysis:trend_lines",
                            "description": "Comprehensive guide to drawing and using trend lines"
                        }
                    ]
                },
                "duration_minutes": 15,
                "xp_reward": 250,
                "coin_reward": 125,
                "required_level": 2,
                "is_published": True,
                "tags": ["trend-lines", "channels", "technical-analysis"]
            },
            
            {
                "title": "Technical Analysis Foundations Quiz",
                "description": "Test your understanding of charts, patterns, and trend analysis",
                "chapter": 2,
                "order": 5,
                "type": "quiz",
                "difficulty": "beginner",
                "content": {},
                "duration_minutes": 12,
                "xp_reward": 250,
                "coin_reward": 125,
                "badge_reward": "Chart Reader",
                "required_level": 2,
                "is_published": True,
                "tags": ["quiz", "technical-analysis", "assessment"]
            },
            
            # ========== CHAPTER 3: TECHNICAL INDICATORS ==========
            {
                "title": "Moving Averages Explained",
                "description": "Learn how to use moving averages for trend following and support/resistance",
                "chapter": 3,
                "order": 1,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=S03L0_DOgfI",
                    "video_title": "Moving Averages Trading Strategy",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=S03L0_DOgfI",
                    "key_topics": [
                        "SMA vs EMA",
                        "Common periods (20, 50, 200)",
                        "Golden cross and death cross",
                        "Dynamic support/resistance",
                        "Moving average crossovers"
                    ]
                },
                "duration_minutes": 22,
                "xp_reward": 300,
                "coin_reward": 150,
                "required_level": 3,
                "is_published": True,
                "tags": ["moving-averages", "indicators", "trend-following"]
            },
            
            {
                "title": "RSI (Relative Strength Index)",
                "description": "Master the RSI indicator for identifying overbought/oversold conditions",
                "chapter": 3,
                "order": 2,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# RSI (Relative Strength Index)

## What is RSI?

The **Relative Strength Index** is a momentum oscillator that measures the speed and magnitude of price changes on a scale of 0 to 100.

**Developed by**: J. Welles Wilder Jr. (1978)
**Default Period**: 14 periods
**Range**: 0-100

## RSI Calculation

```
RSI = 100 - (100 / (1 + RS))
Where RS = Average Gain / Average Loss over 14 periods
```

## Traditional Interpretation

### Overbought/Oversold Levels
- **Above 70**: Overbought (potential sell signal)
- **Below 30**: Oversold (potential buy signal)
- **50 Level**: Midpoint indicating strength direction

### Important Notes:
- Overbought ≠ Immediate reversal
- Can stay overbought in strong uptrends
- Can stay oversold in strong downtrends
- Use in context with overall trend

## RSI Trading Strategies

### 1. Overbought/Oversold Strategy
**Setup**: 
- RSI above 70 + bearish reversal pattern = Sell
- RSI below 30 + bullish reversal pattern = Buy

**Best For**: Range-bound markets
**Risk**: False signals in trending markets

### 2. RSI Divergence

**Bullish Divergence**:
- Price makes lower low
- RSI makes higher low
- Signal: Upward reversal likely

**Bearish Divergence**:
- Price makes higher high
- RSI makes lower high
- Signal: Downward reversal likely

**Hidden Divergence** (Continuation):
- Bullish: Price higher low, RSI lower low
- Bearish: Price lower high, RSI higher high

### 3. RSI Trend Line Breaks
- Draw trend lines on RSI itself
- Break of RSI trend line often precedes price break
- Early warning system

### 4. 50-Level Strategy
- RSI above 50 = Bullish momentum
- RSI below 50 = Bearish momentum
- Cross of 50 level = Potential trend change

### 5. RSI Swing Rejections
**Bullish Swing Rejection**:
1. RSI falls below 30 (oversold)
2. RSI bounces above 30
3. RSI pulls back but holds above 30
4. RSI breaks above its prior high

**Bearish Swing Rejection**:
1. RSI rises above 70 (overbought)
2. RSI falls below 70
3. RSI bounces but stays below 70
4. RSI breaks below its prior low

## Advanced RSI Techniques

### RSI Period Adjustments
- **Shorter Period (9)**: More sensitive, more signals
- **Longer Period (21)**: Less sensitive, fewer signals
- **Multiple RSIs**: Use 5, 14, 21 for different timeframes

### RSI Bands
- Instead of 70/30, use 80/20 for stronger trends
- Or 60/40 for ranging markets
- Adjust based on market conditions

### RSI Price Action
Look for:
- Support/resistance zones on RSI
- RSI chart patterns (head and shoulders, etc.)
- RSI momentum shifts

## Combining RSI with Other Indicators

### RSI + Moving Averages
- Use MAs for trend direction
- Use RSI for entry timing
- Only take RSI signals in MA trend direction

### RSI + MACD
- MACD for trend and momentum
- RSI for overbought/oversold timing
- Both confirming = stronger signal

### RSI + Volume
- RSI extremes with high volume = stronger reversal
- RSI divergence with volume divergence = more reliable

### RSI + Candlestick Patterns
- RSI oversold + hammer = strong buy
- RSI overbought + shooting star = strong sell
- Combine multiple confirmations

## Common Mistakes

1. **Trading Every Signal**: Not all overbought/oversold readings are reversals
2. **Ignoring Trend**: RSI works differently in trends vs ranges
3. **Wrong Timeframe**: Match RSI period to your trading style
4. **No Confirmation**: Always wait for price confirmation
5. **Fixed Levels**: Adjust 70/30 levels based on market conditions

## RSI Settings by Trading Style

- **Day Trading**: 9 or 14 period, 5-min charts
- **Swing Trading**: 14 period, daily charts
- **Position Trading**: 21 period, weekly charts

## Real-World Application

**Example Setup**:
1. Identify uptrend (price above 50-day MA)
2. Wait for RSI to drop below 30 (oversold)
3. Look for bullish candlestick pattern
4. Enter long when RSI crosses back above 30
5. Set stop below recent low
6. Target RSI 70 or resistance level

---

**Sources:**
- "New Concepts in Technical Trading Systems" by J. Welles Wilder Jr.
- StockCharts.com: "RSI" - https://school.stockcharts.com/doku.php?id=technical_indicators:relative_strength_index_rsi
- Investopedia: "RSI Strategies" - https://www.investopedia.com/terms/r/rsi.asp
                    """,
                    "external_links": [
                        {
                            "title": "StockCharts RSI Guide",
                            "url": "https://school.stockcharts.com/doku.php?id=technical_indicators:relative_strength_index_rsi",
                            "description": "Complete RSI tutorial and strategies"
                        }
                    ]
                },
                "duration_minutes": 25,
                "xp_reward": 300,
                "coin_reward": 150,
                "required_level": 3,
                "is_published": True,
                "tags": ["rsi", "indicators", "momentum", "oscillators"]
            },
            
            {
                "title": "MACD Indicator Mastery",
                "description": "Understanding MACD histogram, crossovers, and divergences",
                "chapter": 3,
                "order": 3,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=JDVnPq-lZwg",
                    "video_title": "MACD Indicator Explained",
                    "channel": "UKspreadbetting",
                    "source": "YouTube - UKspreadbetting",
                    "source_url": "https://www.youtube.com/watch?v=JDVnPq-lZwg",
                    "key_topics": [
                        "MACD line and signal line",
                        "MACD histogram interpretation",
                        "Bullish and bearish crossovers",
                        "MACD divergences",
                        "Combining MACD with price action"
                    ]
                },
                "duration_minutes": 15,
                "xp_reward": 280,
                "coin_reward": 140,
                "required_level": 3,
                "is_published": True,
                "tags": ["macd", "indicators", "momentum"]
            },
            
            {
                "title": "Bollinger Bands Strategy",
                "description": "Learn to trade volatility squeezes and band bounces",
                "chapter": 3,
                "order": 4,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Bollinger Bands Strategy

## What are Bollinger Bands?

**Bollinger Bands** are volatility bands placed above and below a moving average, expanding and contracting based on market volatility.

**Developed by**: John Bollinger (1980s)
**Components**:
- Middle Band: 20-period Simple Moving Average
- Upper Band: Middle Band + (2 × Standard Deviation)
- Lower Band: Middle Band - (2 × Standard Deviation)

## How Bollinger Bands Work

### Band Width
- **Narrow Bands**: Low volatility, potential breakout coming
- **Wide Bands**: High volatility, potential consolidation ahead
- **Squeeze**: Bands at narrowest point in 6+ months

### Price Position
- **Above Middle Band**: Bullish momentum
- **Below Middle Band**: Bearish momentum
- **At Upper Band**: Strong uptrend or overbought
- **At Lower Band**: Strong downtrend or oversold

## Trading Strategies

### 1. Bollinger Bounce Strategy
**Setup**:
- Price touches lower band in uptrend
- Look for bullish reversal pattern
- Enter long targeting middle or upper band

**Rules**:
- Only trade bounces in direction of trend
- Wait for confirmation (candlestick pattern)
- Stop loss below recent low

**Best For**: Range-bound markets

### 2. Bollinger Squeeze Breakout
**The Squeeze**:
- Bands contract to narrow range
- Indicates low volatility before expansion
- Often precedes significant moves

**Trading the Breakout**:
1. Identify squeeze (narrowest in 6 months)
2. Wait for decisive close outside bands
3. Enter in breakout direction
4. Target previous band width as minimum move
5. Use opposite band as stop

**Confirmation**: Look for volume spike on breakout

### 3. Band Walk Strategy
**Uptrend Walk**:
- Price repeatedly touches or exceeds upper band
- Each pullback holds above middle band
- Sign of strong trend - don't fade

**Trading**: 
- Buy pullbacks to middle band
- Hold until price closes below middle band
- Very strong trend signal

### 4. Double Bottom/Top
**Double Bottom** (Bullish):
- First low touches/breaks lower band
- Second low holds above lower band
- Price rises above middle band = Buy signal

**Double Top** (Bearish):
- First high touches/breaks upper band
- Second high stays below upper band
- Price falls below middle band = Sell signal

### 5. Bollinger Band Divergence
**Bullish Divergence**:
- Price makes lower low
- Price doesn't touch lower band
- Shows weakening downtrend

**Bearish Divergence**:
- Price makes higher high
- Price doesn't touch upper band
- Shows weakening uptrend

## Advanced Techniques

### Bollinger Band %B
- Shows where price is relative to bands
- Formula: (Price - Lower Band) / (Upper Band - Lower Band)
- Above 1.0: Above upper band
- 0.5: At middle band
- Below 0.0: Below lower band

### Bandwidth Indicator
- Measures distance between bands
- Formula: (Upper Band - Lower Band) / Middle Band
- Low readings = squeeze
- High readings = volatility

### Multiple Timeframe Analysis
- Daily chart for trend
- 4-hour chart for entries
- 1-hour chart for precise timing
- All timeframes should align

## Settings Optimization

### Default Settings (20, 2)
- 20-period MA
- 2 standard deviations
- Works for most markets

### Aggressive (20, 1)
- Tighter bands
- More signals
- More false breakouts

### Conservative (20, 3)
- Wider bands
- Fewer signals
- More reliable

### Shorter Term (10, 2)
- More responsive
- Day trading
- More noise

## Combining with Other Indicators

### Bollinger Bands + RSI
- Bands for volatility
- RSI for momentum
- Both oversold = strong buy
- Both overbought = strong sell

### Bollinger Bands + Volume
- Squeeze + low volume = calm before storm
- Breakout + high volume = valid move
- Band touch + volume spike = reversal likely

### Bollinger Bands + Moving Averages
- Use 50/200 MA for major trend
- Trade BB signals in MA direction
- Ignore counter-trend BB signals

## Common Mistakes

1. **Fading Strong Trends**: Don't short upper band touches in uptrends
2. **No Confirmation**: Always wait for price confirmation
3. **Fixed Stops**: Adjust stops based on band width
4. **Ignoring Trend**: Squeeze can break either direction
5. **Overcrowded Trades**: Everyone sees squeezes - be patient

## Real Trading Example

**Setup**:
1. Stock in uptrend (above 50-day MA)
2. Bollinger Bands squeeze for 10+ days
3. Price breaks above upper band with volume
4. Enter long on close above upper band
5. Initial target: 2× band width
6. Stop: Below middle band or recent low
7. Trail stop using middle band

**Risk Management**:
- Risk 1-2% of account
- Position size based on stop distance
- Scale out at targets

---

**Sources:**
- "Bollinger on Bollinger Bands" by John Bollinger
- BollingerBands.com - https://www.bollingerbands.com/
- StockCharts: "Bollinger Bands" - https://school.stockcharts.com/doku.php?id=technical_indicators:bollinger_bands
- Investopedia: "Trading with Bollinger Bands" - https://www.investopedia.com/trading/using-bollinger-bands-to-gauge-trends/
                    """,
                    "external_links": [
                        {
                            "title": "Official Bollinger Bands Site",
                            "url": "https://www.bollingerbands.com/",
                            "description": "John Bollinger's official resource"
                        },
                        {
                            "title": "StockCharts Bollinger Guide",
                            "url": "https://school.stockcharts.com/doku.php?id=technical_indicators:bollinger_bands",
                            "description": "Complete Bollinger Bands tutorial"
                        }
                    ]
                },
                "duration_minutes": 20,
                "xp_reward": 300,
                "coin_reward": 150,
                "required_level": 3,
                "is_published": True,
                "tags": ["bollinger-bands", "volatility", "indicators"]
            },
            
            {
                "title": "Volume Analysis and Indicators",
                "description": "Understanding volume's role in confirming price movements",
                "chapter": 3,
                "order": 5,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=vPFRCJMuTTY",
                    "video_title": "How to Use Volume in Trading",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=vPFRCJMuTTY",
                    "key_topics": [
                        "Volume and price relationship",
                        "Volume at support/resistance",
                        "Accumulation/distribution",
                        "Volume-weighted average price (VWAP)",
                        "On-balance volume (OBV)"
                    ]
                },
                "duration_minutes": 18,
                "xp_reward": 280,
                "coin_reward": 140,
                "required_level": 3,
                "is_published": True,
                "tags": ["volume", "indicators", "confirmation"]
            },
            
            {
                "title": "Technical Indicators Mastery Quiz",
                "description": "Test your knowledge of moving averages, RSI, MACD, and Bollinger Bands",
                "chapter": 3,
                "order": 6,
                "type": "quiz",
                "difficulty": "intermediate",
                "content": {},
                "duration_minutes": 15,
                "xp_reward": 350,
                "coin_reward": 175,
                "badge_reward": "Indicator Expert",
                "required_level": 3,
                "is_published": True,
                "tags": ["quiz", "indicators", "assessment"]
            },
            
            # ========== CHAPTER 4: RISK MANAGEMENT ==========
            {
                "title": "Introduction to Risk Management",
                "description": "Learn why risk management is crucial for long-term trading success",
                "chapter": 4,
                "order": 1,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=1NMpEFfVwfM",
                    "video_title": "Risk Management for Traders",
                    "channel": "The Trading Channel",
                    "source": "YouTube - The Trading Channel",
                    "source_url": "https://www.youtube.com/watch?v=1NMpEFfVwfM",
                    "key_topics": [
                        "Why 90% of traders fail",
                        "Risk vs reward ratios",
                        "Position sizing fundamentals",
                        "Stop loss placement",
                        "Preserving capital"
                    ]
                },
                "duration_minutes": 20,
                "xp_reward": 300,
                "coin_reward": 150,
                "required_level": 3,
                "is_published": True,
                "tags": ["risk-management", "position-sizing", "stops"]
            },
            
            {
                "title": "Position Sizing and Risk Per Trade",
                "description": "Master the mathematics of position sizing and risk calculation",
                "chapter": 4,
                "order": 2,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Position Sizing and Risk Per Trade

## The Foundation of Risk Management

**Position sizing** is the process of determining how many shares/contracts to trade based on your risk tolerance and stop-loss distance.

### Why Position Sizing Matters
- Protects you from catastrophic losses
- Allows you to stay in the game long-term
- Removes emotional decision-making
- Enables consistent risk across all trades

## The 1-2% Rule

**Never risk more than 1-2% of your account on a single trade.**

### Why This Rule?
- **Series of Losses**: You can survive 10+ consecutive losses
- **Psychological**: Small losses don't trigger panic
- **Mathematical**: Easier to recover from drawdowns
- **Professional Standard**: Used by hedge funds and prop traders

### Drawdown Recovery Math
- Lose 10% → Need 11% to recover
- Lose 20% → Need 25% to recover
- Lose 50% → Need 100% to recover
- Lose 90% → Need 900% to recover!

## Position Sizing Formula

### Basic Formula
```
Position Size = (Account Risk $) / (Entry Price - Stop Loss Price)
```

### Step-by-Step Example

**Given**:
- Account Size: $10,000
- Risk Per Trade: 1% ($100)
- Entry Price: $50
- Stop Loss: $48
- Risk Per Share: $2

**Calculation**:
```
Position Size = $100 / $2 = 50 shares
Total Position Value = 50 × $50 = $2,500
```

### With Different Stop Distances

**Scenario 1**: Tight Stop
- Entry: $50, Stop: $49.50 (0.50 risk)
- Position: $100 / $0.50 = 200 shares
- Position Value: $10,000

**Scenario 2**: Wide Stop
- Entry: $50, Stop: $45 (5.00 risk)
- Position: $100 / $5.00 = 20 shares
- Position Value: $1,000

**Key Insight**: Wider stops = smaller positions

## Risk-Reward Ratios

### Minimum Acceptable Ratio: 1:2
- Risk $100 to make $200
- Even with 40% win rate, you profit

### Ratio Examples

**1:1 Ratio** (Bad)
- Win rate needed: 50%+
- Break-even strategy

**1:2 Ratio** (Good)
- Win rate needed: 34%
- Industry standard

**1:3 Ratio** (Better)
- Win rate needed: 25%
- Professional target

### Calculating R-Multiples

**R** = Risk amount per trade

- Win $200 on $100 risk = 2R gain
- Lose $100 on $100 risk = 1R loss
- 3 wins (2R) + 2 losses (1R) = +4R total

## Advanced Position Sizing Models

### Fixed Fractional Method
- Risk fixed percentage per trade (most common)
- Example: Always risk 1%

### Fixed Ratio Method
- Increase size after profit milestones
- Example: Add 1 contract per $5,000 profit

### Kelly Criterion
```
Kelly % = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
```
- Mathematically optimal
- Often too aggressive
- Use 1/4 or 1/2 Kelly for safety

### Volatility-Based Sizing (ATR Method)
```
Position Size = (Account × Risk%) / (ATR × Multiplier)
```
- ATR = Average True Range
- Adjusts for volatility
- Larger positions in stable stocks

## Account Size Considerations

### Small Accounts ($500 - $5,000)
- More challenging due to minimum shares
- Consider fractional shares
- Focus on higher-priced stocks for flexibility
- May need to risk slightly more (2-3%)

### Medium Accounts ($5,000 - $50,000)
- Standard 1-2% rule works well
- Good flexibility in position sizing
- Can diversify across 3-5 positions

### Large Accounts ($50,000+)
- Full flexibility
- Can hold 5-10 positions
- Consider 0.5-1% risk per trade
- Focus on liquidity

## Multiple Positions Management

### Correlated Positions
- Don't risk 2% on 5 tech stocks (effectively 10% risk)
- Consider sector correlation
- Limit correlated exposure to 5-6%

### Portfolio Heat
- Total risk across all open trades
- Maximum: 6-8% of account
- Example: 4 trades × 2% = 8% portfolio heat

### Scaling In
- Split position into 2-3 entries
- Risk 0.5% per entry
- Better average price
- Lower initial risk

## Stop Loss Placement Strategies

### Percentage-Based Stops
- Fixed % below entry (e.g., 2%)
- Simple but ignores market structure
- Better for beginners

### Technical Stops
- Below support/swing low
- Above resistance/swing high
- Respects market structure
- Professional approach

### ATR-Based Stops
- 1-2 × ATR below entry
- Adjusts for volatility
- Prevents tight stops in volatile markets

### Time-Based Stops
- Exit if thesis invalid after X days
- Frees up capital
- Prevents dead money

## Common Position Sizing Mistakes

1. **Risking Too Much**: "Just this once" becomes habit
2. **Revenge Trading**: Doubling size after losses
3. **Ignoring Correlation**: Multiple similar positions
4. **No Stop Loss**: "I'll just hold" leads to disaster
5. **Fixed Share Amount**: 100 shares regardless of setup
6. **Overleveraging**: Using maximum buying power
7. **Averaging Down**: Doubling up on losers

## Position Sizing for Different Strategies

### Day Trading
- Risk 0.5-1% per trade
- Take 5-10 trades per day
- Maximum daily loss: 3-5%

### Swing Trading
- Risk 1-2% per trade
- Hold 2-5 positions
- Maximum portfolio risk: 6-8%

### Position Trading
- Risk 0.5-1% per trade
- Hold 5-10 positions
- Wide stops, multi-week holds

## Practical Tools and Calculators

### Essential Spreadsheet Columns
- Account Size
- Risk %
- Risk $
- Entry Price
- Stop Loss Price
- Risk Per Share
- Position Size
- Position Value

### Position Sizing Apps
- TradingView (built-in calculator)
- Broker platforms (ToS, Interactive Brokers)
- Mobile apps (Trade Journal, Edgewonk)

## Real-World Example

**Trader Profile**:
- Account: $20,000
- Risk: 1% ($200 per trade)
- Max Open Positions: 4
- Max Portfolio Risk: 6% ($1,200)

**Trade Setup**:
- Stock: XYZ at $75
- Stop Loss: $72 (technical support)
- Risk: $3 per share
- Target: $84 (3:1 R:R)

**Position Sizing**:
```
Shares = $200 / $3 = 66 shares
Position Value = 66 × $75 = $4,950 (24.75% of account)
Potential Loss = $200 (1% of account)
Potential Profit = $600 (3% of account)
```

**If Stopped Out**:
- Account: $19,800
- Next Trade Risk: $198 (1% of new balance)

---

**Sources**:
- "Trade Your Way to Financial Freedom" by Van K. Tharp
- "The New Trading for a Living" by Dr. Alexander Elder
- Investopedia: "Position Sizing" - https://www.investopedia.com/terms/p/positionsizing.asp
- BabyPips: "Risk Management" - https://www.babypips.com/learn/forex/money-management
                    """,
                    "external_links": [
                        {
                            "title": "Investopedia Position Sizing",
                            "url": "https://www.investopedia.com/terms/p/positionsizing.asp",
                            "description": "Comprehensive guide to calculating position sizes"
                        },
                        {
                            "title": "BabyPips Risk Management",
                            "url": "https://www.babypips.com/learn/forex/money-management",
                            "description": "Money management fundamentals"
                        }
                    ]
                },
                "duration_minutes": 30,
                "xp_reward": 400,
                "coin_reward": 200,
                "required_level": 3,
                "is_published": True,
                "tags": ["position-sizing", "risk-management", "money-management"]
            },
            
            {
                "title": "Stop Loss Strategies",
                "description": "Learn different stop loss techniques and when to use each",
                "chapter": 4,
                "order": 3,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=YCZbngNs6EA",
                    "video_title": "Stop Loss Strategy",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=YCZbngNs6EA",
                    "key_topics": [
                        "Fixed vs trailing stops",
                        "ATR-based stops",
                        "Support/resistance stops",
                        "Time-based stops",
                        "Mental stops vs hard stops"
                    ]
                },
                "duration_minutes": 17,
                "xp_reward": 300,
                "coin_reward": 150,
                "required_level": 3,
                "is_published": True,
                "tags": ["stop-loss", "risk-management", "exits"]
            },
            
            {
                "title": "Trading Psychology and Discipline",
                "description": "Master the mental game of trading and emotional control",
                "chapter": 4,
                "order": 4,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Trading Psychology and Discipline

## The Mental Game

**"The market is a device for transferring money from the impatient to the patient."** - Warren Buffett

Trading success is 80% psychology, 20% strategy. You can have the best system, but without discipline and emotional control, you'll fail.

## Common Psychological Traps

### 1. Fear of Missing Out (FOMO)
**Symptoms**:
- Chasing trades after breakouts
- Entering without confirmation
- Abandoning your strategy

**Solution**:
- Remember: There's always another trade
- Stick to your entry criteria
- Keep a "missed trade" journal
- Focus on process, not individual trades

### 2. Revenge Trading
**Symptoms**:
- Trading immediately after a loss
- Increasing position size to "make it back"
- Taking low-probability setups

**Solution**:
- Take a break after 2 consecutive losses
- Have a maximum daily loss limit
- Review trades only after market closes
- Remember: The market doesn't owe you anything

### 3. Overconfidence After Wins
**Symptoms**:
- Increasing position sizes too quickly
- Ignoring stop losses
- Taking more setups than usual

**Solution**:
- Stick to your position sizing rules
- Document why you're winning
- Stay humble - markets change
- Increase size gradually over months

### 4. Fear of Taking Losses
**Symptoms**:
- Moving stop losses further away
- Holding losing trades too long
- Hoping for a reversal

**Solution**:
- Accept: Losses are part of trading
- View stops as insurance premiums
- Cut losses quickly, let winners run
- Focus on long-term statistics

### 5. Analysis Paralysis
**Symptoms**:
- Adding too many indicators
- Waiting for perfect setups
- Overthinking entries

**Solution**:
- Keep strategy simple (3-4 criteria max)
- Accept uncertainty is normal
- Trust your tested system
- Set time limits for analysis

## Developing Trading Discipline

### Create a Trading Plan

**Essential Components**:
1. **Markets**: What will you trade?
2. **Timeframe**: Day, swing, or position trading?
3. **Strategy**: Specific entry/exit rules
4. **Risk Management**: Position size, stop loss
5. **Schedule**: When will you trade?
6. **Goals**: Weekly, monthly, yearly targets
7. **Rules**: Personal trading commandments

**Example Trading Rules**:
- Never risk more than 1% per trade
- Maximum 3 trades per day
- Stop trading after 2 losses in a row
- No trading before major news
- Exit all positions before vacation

### The Pre-Market Routine

**Morning Checklist**:
1. Review overnight news
2. Check economic calendar
3. Identify key support/resistance
4. Mark potential trade setups
5. Set alerts
6. Review trading plan
7. Mental preparation (meditation, exercise)

### During Market Hours

**Stay Disciplined**:
- Trade only your setups
- Follow your checklist
- Take breaks between trades
- Don't watch P&L constantly
- Avoid social media/chat rooms
- Stay hydrated, take breaks

### Post-Market Review

**Essential Questions**:
1. Did I follow my plan?
2. What did I do well?
3. What mistakes did I make?
4. What can I improve?
5. Were my losses acceptable?
6. Did I manage emotions well?

## The Trading Journal

**What to Track**:

**Before Trade**:
- Date and time
- Stock/symbol
- Setup/pattern
- Entry price
- Stop loss
- Target
- Risk:reward ratio
- Position size
- Why entering (thesis)
- Screenshot of chart

**After Trade**:
- Exit price
- Actual gain/loss
- R-multiple (2R, 3R, -1R)
- Did I follow plan?
- Emotional state
- Lessons learned
- What to improve

**Weekly Review**:
- Win rate
- Average winner vs average loser
- Best/worst trades
- Pattern recognition
- Emotional patterns
- Strategy adjustments needed

## Managing Emotions

### Dealing with Losses

**Healthy Mindset**:
- Losses are tuition in market education
- Focus on making good decisions
- One trade doesn't define you
- Review what you can control

**Unhealthy Mindset**:
- "I'm a loser"
- "I need to make it back now"
- "This always happens to me"
- Blaming external factors

### Dealing with Wins

**Healthy Mindset**:
- Grateful but grounded
- Focus on what you did right
- Can it be replicated?
- Stay consistent

**Unhealthy Mindset**:
- "I'm a genius"
- "I can't lose"
- "Time to increase size 5x"
- Getting complacent

## Stress Management Techniques

### Physical Health
- **Sleep**: 7-9 hours crucial for decision making
- **Exercise**: Reduces cortisol, improves focus
- **Nutrition**: Stable blood sugar = stable emotions
- **Hydration**: Dehydration impairs cognition

### Mental Techniques
- **Meditation**: 10 minutes daily reduces anxiety
- **Deep Breathing**: 4-7-8 technique before trading
- **Visualization**: Mental rehearsal of trading day
- **Breaks**: Walk away every 90 minutes

### Lifestyle Balance
- **Relationships**: Don't neglect family/friends
- **Hobbies**: Identity beyond trading
- **Vacation**: Regular breaks from markets
- **Perspective**: Trading is a job, not your life

## The 10 Trading Commandments

1. **I shall risk only what I can afford to lose**
2. **I shall plan every trade and trade every plan**
3. **I shall use stops on every trade**
4. **I shall let my winners run and cut my losers short**
5. **I shall not overtrade or revenge trade**
6. **I shall keep detailed records of all trades**
7. **I shall continuously educate myself**
8. **I shall be patient and disciplined**
9. **I shall accept responsibility for my results**
10. **I shall treat trading as a business**

## Building Confidence

### Start Small
- Begin with minimum position sizes
- Focus on executing process correctly
- Build track record of disciplined trades
- Gradually increase size as consistency improves

### Simulate Before You Trade
- Paper trade for 1-3 months
- Test your strategy
- Learn the platform
- Build muscle memory

### Measure What Matters
- Focus on process, not profit
- Track rule adherence rate
- Celebrate disciplined losers
- System confidence comes from testing

## When to Take a Break

**Warning Signs**:
- 3+ consecutive losing days
- Breaking your trading rules
- Emotional trading decisions
- Fatigue or burnout
- Life stress affecting trading
- Consistent overtrading

**Break Activities**:
- Review past trades
- Backtest strategies
- Read trading books
- Exercise and rest
- Spend time with loved ones
- Return refreshed

## Recommended Reading

- **"Trading in the Zone"** by Mark Douglas
- **"The Psychology of Trading"** by Brett Steenbarger
- **"Reminiscences of a Stock Operator"** by Edwin Lefèvre
- **"The Daily Trading Coach"** by Brett Steenbarger

---

**Sources**:
- "Trading in the Zone" by Mark Douglas
- "The Psychology of Trading" by Brett Steenbarger
- TradingPsychology.com - https://www.tradingpsychology.com/
- Dr. Brett Steenbarger's Blog - https://www.forbes.com/sites/brettsteenbarger/
                    """,
                    "external_links": [
                        {
                            "title": "Dr. Brett Steenbarger Blog",
                            "url": "https://www.forbes.com/sites/brettsteenbarger/",
                            "description": "Trading psychology insights from leading expert"
                        }
                    ]
                },
                "duration_minutes": 25,
                "xp_reward": 350,
                "coin_reward": 175,
                "required_level": 3,
                "is_published": True,
                "tags": ["psychology", "discipline", "trading-mindset"]
            },
            
            {
                "title": "Risk Management Simulation",
                "description": "Practice proper risk management in a simulated trading environment",
                "chapter": 4,
                "order": 5,
                "type": "simulation",
                "difficulty": "intermediate",
                "content": {
                    "scenario": "You have $10,000. Make 10 trades with proper risk management. Maximum 2% risk per trade, minimum 1:2 risk-reward ratio.",
                    "success_criteria": {
                        "min_win_rate": 30,
                        "max_drawdown": 15,
                        "proper_position_sizing": True,
                        "min_trades": 10,
                        "risk_per_trade_max": 2,
                        "min_risk_reward": 2.0
                    },
                    "instructions": "This simulation tests your ability to manage risk across multiple trades. Focus on consistent position sizing and proper stop placement."
                },
                "duration_minutes": 45,
                "xp_reward": 500,
                "coin_reward": 250,
                "badge_reward": "Risk Manager",
                "required_level": 3,
                "is_published": True,
                "tags": ["simulation", "risk-management", "practice"]
            },
            
            {
                "title": "Risk Management Master Quiz",
                "description": "Comprehensive test of risk management concepts",
                "chapter": 4,
                "order": 6,
                "type": "quiz",
                "difficulty": "intermediate",
                "content": {},
                "duration_minutes": 15,
                "xp_reward": 400,
                "coin_reward": 200,
                "badge_reward": "Risk Master",
                "required_level": 3,
                "is_published": True,
                "tags": ["quiz", "risk-management", "assessment"]
            },
            
            # ========== CHAPTER 5: CHART PATTERNS & PRICE ACTION ==========
            {
                "title": "Classic Chart Patterns",
                "description": "Master continuation and reversal patterns for high-probability trading",
                "chapter": 5,
                "order": 1,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Classic Chart Patterns

## Continuation Patterns

### Bullish Flag
- **Formation**: Sharp rally followed by parallel consolidation downward
- **Volume**: High on pole, declining in flag, surges on breakout
- **Target**: Measure pole length, project from breakout
- **Timeframe**: 1-4 weeks consolidation
- **Success Rate**: 68% according to Bulkowski's research

### Bullish Pennant
- **Formation**: Sharp rally followed by converging consolidation
- **Difference from Flag**: Symmetrical triangle shape vs parallel
- **Duration**: Typically 1-3 weeks (shorter than flags)
- **Breakout**: Look for volume expansion
- **Target**: Equal to pole height

### Cup and Handle
- **Formation**: U-shaped consolidation followed by smaller pullback
- **Duration**: 1-6 months for cup, 1-4 weeks for handle
- **Depth**: Cup typically retraces 33-50% of prior advance
- **Handle**: Should be in upper half of cup, not more than 20% retracement
- **Volume**: Diminishing through pattern, spike on breakout
- **Target**: Cup depth added to breakout point
- **Success**: One of highest probability patterns (>80%)

### Ascending Triangle
- **Formation**: Flat resistance, rising support
- **Bias**: Bullish continuation (75% break upward)
- **Psychology**: Buyers increasingly aggressive, sellers at fixed level
- **Volume**: Should diminish into apex, spike on breakout
- **Target**: Height of triangle from breakout
- **Entry**: Breakout above resistance with volume

### Rectangle (Trading Range)
- **Formation**: Price oscillates between parallel support/resistance
- **Bias**: Neutral until breakout
- **Trading**: Buy support, sell resistance within range
- **Breakout**: 54% upward, 46% downward
- **Target**: Height of rectangle from breakout
- **False Breaks**: Common - wait for close confirmation

## Reversal Patterns

### Head and Shoulders (Bearish)
- **Formation**: Three peaks - middle highest (head), outer two similar (shoulders)
- **Neckline**: Support connecting lows between peaks
- **Volume**: Declining through pattern, surge on neckline break
- **Target**: Distance from head to neckline, projected down
- **Confirmation**: Close below neckline
- **Pullback**: 60% pull back to neckline before decline
- **Success Rate**: 83% reach target

### Inverse Head and Shoulders (Bullish)
- **Formation**: Three troughs - middle lowest, outer two similar
- **Neckline**: Resistance connecting highs between troughs
- **Volume**: Less important than regular H&S, but should expand on breakout
- **Target**: Distance from head to neckline, projected up
- **Confirmation**: Close above neckline
- **Success Rate**: 81% reach target

### Double Top (Bearish)
- **Formation**: Two peaks at approximately same price level
- **Time**: Peaks separated by weeks/months
- **Volume**: First peak higher volume, second peak lower
- **Confirmation**: Break below support (valley between peaks)
- **Target**: Distance from peaks to valley support
- **Variation**: Triple top (3 peaks)
- **Success Rate**: 65% reach target

### Double Bottom (Bullish)
- **Formation**: Two troughs at approximately same price level
- **Volume**: Second trough often lighter volume (bullish)
- **Confirmation**: Break above resistance (peak between troughs)
- **Target**: Distance from troughs to peak resistance
- **Success Rate**: 78% reach target (more reliable than double top)

### Rounding Bottom (Saucer)
- **Formation**: Gradual U-shaped decline and recovery
- **Duration**: Several months
- **Volume**: High at start, dries up at bottom, increases on right side
- **Strength**: Gentle pattern = less overhead resistance
- **Target**: Depth of pattern from breakout
- **Ideal**: Volume follows inverse saucer shape

### Rising Wedge (Bearish)
- **Formation**: Upward sloping converging trend lines
- **Contrarian**: Looks bullish but typically breaks down
- **Psychology**: Each rally weaker, momentum fading
- **Volume**: Should diminish throughout pattern
- **Breakout**: Usually to downside (68%)
- **Target**: Back to wedge origin

### Falling Wedge (Bullish)
- **Formation**: Downward sloping converging trend lines
- **Bias**: Bullish reversal
- **Volume**: Declining through pattern, expands on upside break
- **Breakout**: Usually upward (72%)
- **Target**: Height at widest point, projected from breakout

## Triangle Patterns

### Symmetrical Triangle
- **Formation**: Converging support and resistance lines
- **Bias**: Neutral - continuation pattern
- **Breakout Direction**: Same as trend entering pattern (70%)
- **Volume**: Must contract into apex, spike on breakout
- **Timing**: Typically breaks at 2/3 to 3/4 of pattern
- **Target**: Widest part of triangle from breakout

### Descending Triangle
- **Formation**: Flat support, descending resistance
- **Bias**: Bearish continuation (64% break downward)
- **Psychology**: Sellers increasingly aggressive, buyers at fixed level
- **Volume**: Less important than ascending, but should confirm break
- **Target**: Height of triangle from breakdown
- **Note**: Can appear as bullish reversal at bottoms

## Pattern Trading Guidelines

### Confirmation Checklist
1. **Volume**: Pattern volume matches expectations
2. **Completion**: Wait for full pattern formation
3. **Breakout**: Clear break with volume, ideally closing price
4. **Trend**: Consider larger trend context
5. **Support/Resistance**: Pattern at key level = higher probability

### Entry Techniques
- **Aggressive**: Enter on breakout
- **Conservative**: Enter on pullback after breakout
- **Scale**: Half position on break, half on retest

### Stop Loss Placement
- **Continuation Patterns**: Below pattern support
- **Reversal Patterns**: Below neckline or opposite peak/trough
- **Triangles**: Below triangle apex

### Target Setting
1. **Measured Move**: Pattern height from breakout (minimum)
2. **Fibonacci Extensions**: 1.272, 1.618 levels
3. **Previous Resistance/Support**: Major levels
4. **Take Profits**: Partial at minimum target, let rest run

## Common Mistakes

1. **Trading Incomplete Patterns**: Wait for full formation
2. **Ignoring Volume**: Essential for confirmation
3. **Wrong Timeframe**: Pattern should fit your trading style
4. **Forcing Patterns**: Not every consolidation is a pattern
5. **No Confirmation**: Don't anticipate - wait for breakout
6. **Fixed Targets**: Adjust for market conditions
7. **Ignoring False Breaks**: Use closing prices for confirmation

## Pattern Reliability Factors

### Higher Probability When:
- Pattern appears in direction of major trend
- Volume confirms the pattern
- Pattern is well-formed and clear
- Breakout is decisive with gap or large candle
- Pattern at significant support/resistance
- Multiple timeframes align

### Lower Probability When:
- Pattern against major trend
- Volume doesn't confirm
- Pattern is sloppy or ambiguous
- Small or tentative breakout
- No significant S/R level
- Conflicting timeframe signals

## Combining Patterns with Other Analysis

### With Indicators
- **RSI**: Bullish pattern + RSI oversold = stronger
- **MACD**: Pattern + MACD divergence = more reliable
- **Moving Averages**: Breakout aligned with MA cross

### With Fibonacci
- Pattern at 50% or 61.8% retracement level
- Targets at Fibonacci extension levels
- Confluence increases probability

### With Market Structure
- Pattern at weekly/monthly support
- Aligns with higher timeframe trend
- Respects major round numbers

---

**Sources:**
- "Encyclopedia of Chart Patterns" by Thomas Bulkowski - http://thepatternsite.com/
- "Technical Analysis of the Financial Markets" by John Murphy
- Investopedia: "Chart Patterns" - https://www.investopedia.com/articles/technical/112601.asp
- Bulkowski's Pattern Performance Statistics - http://thepatternsite.com/chartpatterns.html
                    """,
                    "external_links": [
                        {
                            "title": "Bulkowski's Pattern Encyclopedia",
                            "url": "http://thepatternsite.com/",
                            "description": "Most comprehensive chart pattern statistics and research"
                        },
                        {
                            "title": "StockCharts Pattern Reference",
                            "url": "https://school.stockcharts.com/doku.php?id=chart_analysis:chart_patterns",
                            "description": "Visual guide to all major chart patterns"
                        }
                    ]
                },
                "duration_minutes": 35,
                "xp_reward": 400,
                "coin_reward": 200,
                "required_level": 4,
                "is_published": True,
                "tags": ["chart-patterns", "price-action", "continuation", "reversal"]
            },
            
            {
                "title": "Price Action Trading Fundamentals",
                "description": "Learn to trade using pure price action without indicators",
                "chapter": 5,
                "order": 2,
                "type": "video",
                "difficulty": "intermediate",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=G4MHu7F5pVw",
                    "video_title": "Price Action Trading Secrets",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=G4MHu7F5pVw",
                    "key_topics": [
                        "Market structure (HH, HL, LH, LL)",
                        "Supply and demand zones",
                        "Price rejection and acceptance",
                        "Swing highs and lows",
                        "Trading breakouts and reversals"
                    ]
                },
                "duration_minutes": 28,
                "xp_reward": 350,
                "coin_reward": 175,
                "required_level": 4,
                "is_published": True,
                "tags": ["price-action", "market-structure", "trading"]
            },
            
            {
                "title": "Supply and Demand Zones",
                "description": "Identify and trade institutional supply and demand levels",
                "chapter": 5,
                "order": 3,
                "type": "reading",
                "difficulty": "advanced",
                "content": {
                    "markdown": """
# Supply and Demand Zones

## Understanding Supply and Demand

### The Core Concept
**Supply and Demand** zones are price areas where significant institutional buying or selling occurred, creating potential future support or resistance.

**Key Difference from S/R**:
- Support/Resistance: Lines where price bounced
- Supply/Demand: **Zones** where orders accumulated before major moves

### Why Zones Work
- Institutions can't fill large orders at single price
- They leave **unfilled orders** in these zones
- Price returns to fill remaining orders
- Creates high-probability reversal areas

## Identifying Demand Zones (Support)

### Characteristics
1. **Strong Rally**: Sharp, impulsive move away from zone
2. **Small Base**: Consolidation before rally (basing period)
3. **Fresh Zone**: Price hasn't returned (unfilled orders remain)
4. **Volume Spike**: High volume on the breakout from zone

### How to Draw
1. Find strong bullish move (pole)
2. Identify last consolidation before pole (base)
3. Draw rectangle around entire base
4. Zone = Support area with unfilled buy orders

### Quality Rating
**High Quality**:
- Very sharp move away (few candles)
- Small, tight base
- Fresh (untested)
- Significant volume
- Aligns with higher timeframe

**Low Quality**:
- Slow, choppy move away
- Large, loose base
- Already tested multiple times
- No volume confirmation

## Identifying Supply Zones (Resistance)

### Characteristics
1. **Strong Decline**: Sharp, impulsive move down from zone
2. **Small Distribution**: Consolidation before decline
3. **Fresh Zone**: Price hasn't returned
4. **Volume Spike**: High volume on breakdown

### Drawing Process
1. Find strong bearish move (drop)
2. Identify last consolidation before drop (distribution)
3. Draw rectangle around distribution area
4. Zone = Resistance with unfilled sell orders

## Zone Trading Strategies

### Strategy 1: Fresh Zone Bounce
**Setup**:
- Price approaches fresh demand zone
- Look for bullish reversal pattern
- Enter on confirmation

**Entry**:
- Conservative: Wait for close above zone
- Aggressive: Enter at zone with tight stop

**Stop Loss**: Below demand zone (10-20 pips)

**Target**: 
- First: Nearest supply zone
- Second: 2-3x risk

**Success Rate**: 60-70% when fresh

### Strategy 2: Zone Flip
**Concept**: Supply becomes demand, demand becomes supply

**Bullish Flip**:
1. Price breaks above supply zone with volume
2. Supply zone now becomes demand (role reversal)
3. Wait for pullback to flipped zone
4. Enter long on bounce

**Bearish Flip**:
1. Price breaks below demand zone
2. Demand becomes supply
3. Pullback to flipped zone = short entry

**Why It Works**: Previous sellers now buyers, vice versa

### Strategy 3: Zone Confluence
**High Probability Areas**:
- Demand zone + Fibonacci 61.8%
- Supply zone + Major resistance
- Zone + Round number (psychological)
- Zone + Moving average
- Multiple timeframe zones align

**Entry**: When 2+ factors align at zone

### Strategy 4: Zone Rejection
**Setup**:
- Price enters zone
- Creates wick/rejection candle
- Closes back outside zone

**Signal**: Zone still has unfilled orders

**Entry**: Next candle in direction of rejection

**Stop**: Inside the zone

## Zone vs. Traditional Support/Resistance

| Aspect | Zones | S/R Lines |
|--------|-------|-----------|
| Shape | Rectangle/Box | Horizontal Line |
| Concept | Order accumulation | Price memory |
| Width | 10-50 pips | Single price |
| Quality | Degrades with tests | Strengthens with tests |
| Entry | Anywhere in zone | At exact level |

## Fresh vs. Tested Zones

### Fresh Zones (Best)
- **Never tested** since creation
- All orders still unfilled
- Highest probability (60-70%)
- Maximum reaction expected

### Lightly Tested (Good)
- Tested once, still held
- Some orders filled
- Still reliable (50-60%)
- Watch for strong bounce

### Heavily Tested (Avoid)
- Multiple tests
- Most orders filled
- Low probability (<40%)
- Likely to break

## Multi-Timeframe Analysis

### The Power of Alignment
**Example Approach**:
1. **Weekly**: Identify major supply/demand zones
2. **Daily**: Find zones within weekly trend
3. **4H**: Pinpoint entry zones
4. **1H**: Time precise entry

**Best Setup**:
- Daily demand zone
- 4H demand zone inside it
- 1H entry signal
- = Triple confirmation

### Timeframe Rules
- Higher timeframe zones stronger
- Trade direction of higher TF
- Enter on lower TF signals
- Set stops based on higher TF

## Advanced Concepts

### Proximal vs. Distal Zones
**Proximal**: Closest zone to current price
- More likely to be tested
- Lower risk/reward
- Higher probability

**Distal**: Far zone from price
- Less likely to be reached
- Higher risk/reward
- Lower probability

### Zone Origin
**Rally-Base-Rally** (Demand):
- Accumulation before rise
- Buy orders

**Drop-Base-Drop** (Supply):
- Distribution before fall
- Sell orders

**Rally-Base-Drop** (Supply):
- Distribution disguised as strength
- Trap zone

**Drop-Base-Rally** (Demand):
- Accumulation disguised as weakness
- Trap zone

### Imbalance Zones
**Fair Value Gap (FVG)**:
- Large gap between candles
- Represents imbalance
- Price tends to fill gap
- Trade the fill

## Risk Management with Zones

### Position Sizing
```
Risk per trade: 1-2%
Entry: Top of demand zone
Stop: Below zone (15 pips)
Position size: Risk$ / 15 pips
```

### Stop Loss Placement
- **Demand Zones**: 5-10 pips below
- **Supply Zones**: 5-10 pips above
- **Wider Zones**: Stop outside zone
- **Tight Zones**: Stop middle of zone

### Take Profit Targets
1. **First Target**: Opposite zone (2R minimum)
2. **Second Target**: Major S/R level
3. **Final Target**: Trend exhaustion

## Common Mistakes

1. **Confusing Zones with S/R**: Zones are areas, not lines
2. **Trading Old Zones**: Fresh zones only
3. **Ignoring Move Quality**: Need sharp, decisive moves
4. **No Confirmation**: Don't blindly buy/sell at zones
5. **Wrong Timeframe**: Match zone TF to trading style
6. **Too Many Zones**: Mark only strongest, freshest zones
7. **Forgetting Role Reversal**: Broken zones flip

## Practical Workflow

### Daily Routine
1. **Mark Weekly Zones**: Major supply/demand
2. **Identify Daily Zones**: Within weekly trend
3. **Set Alerts**: Price approaching zones
4. **Wait for Setup**: Reversal pattern at zone
5. **Enter with Confirmation**: Don't anticipate
6. **Manage Trade**: Trail stops, scale out

### Zone Maintenance
- Remove zones after 2-3 strong tests
- Update zones weekly
- Focus on fresh zones
- Archive old zones for reference

## Tools and Resources

### Recommended Platforms
- **TradingView**: Rectangle tool for zones
- **NinjaTrader**: Zone drawing indicators
- **MT4/MT5**: Supply/demand indicators

### Study Resources
- Sam Seiden (Online Trading Academy)
- Adam Grimes' supply/demand course
- FX Price Action community

---

**Sources:**
- "Trading from Your Gut" by Curtis Faith
- Sam Seiden (Online Trading Academy) - Supply & Demand methodology
- "The Art and Science of Technical Analysis" by Adam Grimes
- No Nonsense Forex (YouTube channel) - https://www.youtube.com/c/NoNonsenseForex
                    """,
                    "external_links": [
                        {
                            "title": "Online Trading Academy - Supply & Demand",
                            "url": "https://www.tradingacademy.com/resources/professional-trading-strategies/understanding-supply-and-demand.aspx",
                            "description": "Original supply/demand methodology by Sam Seiden"
                        }
                    ]
                },
                "duration_minutes": 30,
                "xp_reward": 450,
                "coin_reward": 225,
                "required_level": 5,
                "is_published": True,
                "tags": ["supply-demand", "price-action", "institutional", "advanced"]
            },
            
            {
                "title": "Reading Market Structure",
                "description": "Identify trends, ranges, and market phases using price action",
                "chapter": 5,
                "order": 4,
                "type": "video",
                "difficulty": "advanced",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=2DVFb_5tLGE",
                    "video_title": "How To Read Market Structure",
                    "channel": "The Trading Channel",
                    "source": "YouTube - The Trading Channel",
                    "source_url": "https://www.youtube.com/watch?v=2DVFb_5tLGE",
                    "key_topics": [
                        "Higher highs and higher lows",
                        "Lower highs and lower lows",
                        "Break of structure (BOS)",
                        "Change of character (CHoCH)",
                        "Market phases"
                    ]
                },
                "duration_minutes": 24,
                "xp_reward": 400,
                "coin_reward": 200,
                "required_level": 5,
                "is_published": True,
                "tags": ["market-structure", "price-action", "trends"]
            },
            
            {
                "title": "Chart Patterns Mastery Quiz",
                "description": "Test your pattern recognition and price action skills",
                "chapter": 5,
                "order": 5,
                "type": "quiz",
                "difficulty": "advanced",
                "content": {},
                "duration_minutes": 20,
                "xp_reward": 500,
                "coin_reward": 250,
                "badge_reward": "Pattern Master",
                "required_level": 5,
                "is_published": True,
                "tags": ["quiz", "patterns", "price-action", "assessment"]
            },
            
            # ========== CHAPTER 6: TRADING STRATEGIES ==========
            {
                "title": "Trend Following Strategies",
                "description": "Master the art of riding trends for maximum profits",
                "chapter": 6,
                "order": 1,
                "type": "reading",
                "difficulty": "advanced",
                "content": {
                    "markdown": """
# Trend Following Strategies

## The Philosophy of Trend Following

**"The trend is your friend until the end when it bends."**

### Core Principles
1. **Trends persist longer than expected**
2. **Cut losses short, let winners run**
3. **Trade with the trend, not against it**
4. **Position sizing is critical**
5. **Accept many small losses for few big wins**

### Win Rate Reality
- Trend followers: 30-40% win rate
- But: Average win >> Average loss
- Example: 35% wins at 5R = profitable

## Strategy 1: Moving Average Crossover

### Classic Setup (50/200 EMA)
**Buy Signal**:
- 50 EMA crosses above 200 EMA (Golden Cross)
- Price above both MAs
- Increasing volume

**Sell Signal**:
- 50 EMA crosses below 200 EMA (Death Cross)
- Price below both MAs

**Position Management**:
- Entry: On close above/below both MAs after cross
- Stop: Below 200 EMA (or 2 ATR)
- Trail: Using 50 EMA as dynamic stop

**Pros**: Simple, effective in strong trends
**Cons**: Lagging, whipsaws in ranges

### Multiple MA System (8/21/55 EMA)
**Trend Identification**:
- Bullish: 8 > 21 > 55, all rising
- Bearish: 8 < 21 < 55, all falling
- Range: MAs flat and intertwined

**Entry Rules**:
- Wait for pullback to 21 EMA in uptrend
- Enter on bullish rejection candle
- Stop below 55 EMA

**Exit**: When 8 EMA crosses below 21 EMA

## Strategy 2: Breakout Trading

### Consolidation Breakout
**Setup**:
1. Identify 3+ weeks of consolidation
2. Tightening range (lower highs, higher lows)
3. Decreasing volume into apex
4. Strong trend before consolidation

**Entry Criteria**:
- Decisive break of range high/low
- Volume 50%+ above average
- Large bodied candle (not doji)
- Close in outer 25% of range

**Position Sizing**: 1-2% risk
**Stop Loss**: Opposite side of range
**Target**: Range height x 2

### 52-Week High Breakout
**Research**: Stocks breaking 52-week highs outperform (O'Neil, Minervini)

**Setup**:
- Stock hits new 52-week high
- Volume 40%+ above average
- Strong earnings/fundamentals
- Market in uptrend

**Entry**: On breakout day or pullback to breakout level

**Management**:
- Stop: 7-8% below entry (O'Neil rule)
- Trail: Raise stop as new highs made
- Hold: Until 50-day MA breaks

## Strategy 3: Donchian Channel System

### Turtle Trading Rules (Simplified)
**Entry**:
- Buy: 20-day high breakout
- Sell: 20-day low breakdown

**Position Sizing**:
- Risk 1% per trade
- Risk = 2 × ATR

**Stops**:
- Initial: 2 ATR from entry
- Trail: 10-day low (for longs)

**Pyramiding**:
- Add ½ position every 0.5 ATR profit
- Maximum 4 units total

**Exit**:
- 10-day channel breakout opposite direction
- Or hit stop loss

**Performance**: 30% win rate, highly profitable long-term

## Strategy 4: ADX Trend Strategy

### Using ADX for Trend Strength
**ADX Reading**:
- 0-20: Weak/no trend (avoid)
- 20-40: Moderate trend
- 40+: Strong trend (ideal)

**Strategy Rules**:
1. **Filter**: Only trade when ADX > 25
2. **Direction**: +DI above -DI = uptrend
3. **Entry**: Pullback to EMA in trend direction
4. **Exit**: ADX peaks and turns down

**Combination**:
- ADX > 25 (trending)
- Price > 50 EMA (bull trend)
- RSI oversold (< 40)
- Enter on RSI turn up

## Strategy 5: Higher High/Higher Low

### Pure Price Action Trend Following
**Uptrend Definition**:
- Series of higher highs (HH)
- Series of higher lows (HL)

**Entry Points**:
1. Wait for new HH
2. Enter on pullback to HL
3. Look for bullish reversal pattern at HL

**Stop Loss**: Below most recent HL

**Exit**: Break of HL (lower low made)

**Example**:
```
Entry Checklist:
☐ New HH confirmed
☐ Pullback at least 38.2% of last leg
☐ Bullish candle at support
☐ Volume declining on pullback
☐ Risk:reward minimum 1:2
```

## Strategy 6: Trend Channel Trading

### Drawing the Channel
1. Identify clear trend
2. Draw trend line (support in uptrend)
3. Draw parallel line through highs
4. Price should respect both lines

**Buy Strategy** (Uptrend):
- Entry: Bounce off lower channel line
- Confirmation: Bullish engulfing or hammer
- Stop: Below channel
- Target: Upper channel line

**Channel Break** Trading:
- Strong break above channel with volume
- Enter on pullback to channel (now support)
- Target: Channel width projected up

## Position Management Rules

### Scaling In (Pyramiding)
**Method 1**: Fixed Fractional
- Initial position: 50% of intended size
- Add 25% at +1R profit
- Add final 25% at +2R profit

**Method 2**: Fibonacci Levels
- Initial entry: 33% size
- Add at 38.2% retracement
- Add at 50% retracement

**Critical Rules**:
- Only add to winners, never losers
- Each add must have own stop loss
- Total risk should not exceed 2-3%

### Scaling Out (Taking Profits)
**Conservative Approach**:
- Take 1/3 at 1R (covers commission)
- Take 1/3 at 2R (locks profit)
- Let 1/3 run with trailing stop

**Aggressive Approach**:
- Take nothing until 3R
- Then trail stop aggressively
- Let trend run completely

## Trailing Stop Techniques

### 1. ATR Trailing Stop
- Set stop 2-3 ATR below highest close
- Move up only, never down
- Adjust daily

### 2. Moving Average Trail
- 20 EMA for short-term
- 50 EMA for intermediate
- 200 EMA for long-term
- Exit on close below MA

### 3. Chandelier Stop
Stop = Highest High - (ATR × Multiplier)
Typical multiplier: 3
- Hangs from ceiling like chandelier
- Rises with new highs
- Exit when price closes below

### 4. Percentage Trailing Stop
- Trail stop 5-10% below highest close
- Simple but effective
- Adjust % based on volatility

## Multi-Timeframe Trend Following

### The Top-Down Approach
1. **Monthly**: Identify major trend
2. **Weekly**: Confirm trend, find entry zones
3. **Daily**: Time specific entries
4. **4H/1H**: Precise entry trigger

**Example**:
- Monthly: Strong uptrend above 10 MA
- Weekly: Pullback to 20 EMA
- Daily: Bullish engulfing at support
- 4H: Entry on break of consolidation

**Rule**: All timeframes must align

## Trend Following Psychology

### Accepting Losses
- 60-70% of trades will lose
- Each loss gets you closer to winner
- Focus on process, not individual trades
- Track R-multiples, not dollar P&L

### Patience with Winners
**Common Mistake**: Taking profits too early

**Solution**:
- Predetermine profit target
- Use trailing stops
- Let stop get hit (don't exit manually)
- Review winners you cut short

### Dealing with Drawdowns
- Trend following has 20-30% drawdowns
- Don't abandon system during drawdown
- Reduce size if needed, but keep trading
- Drawdowns precede best performance

## Backtesting Your Strategy

### Essential Metrics
- **Win Rate**: % of winning trades
- **Average Win**: Mean profit on winners
- **Average Loss**: Mean loss on losers
- **Profit Factor**: Gross profit / Gross loss
- **Expectancy**: (Win% × Avg Win) - (Loss% × Avg Loss)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns

### Minimum Standards
- Win Rate: >30%
- Profit Factor: >1.5
- Expectancy: Positive
- Max Drawdown: <25%
- Sample Size: 100+ trades

## Famous Trend Followers

### Richard Dennis & the Turtles
- Taught trend following to novices
- Achieved 80%+ annual returns
- Proved trading is learnable

### Ed Seykota
- 250,000% returns over 16 years
- Pure trend follower
- "The elements of good trading are: 1) cutting losses, 2) cutting losses, and 3) cutting losses."

### David Harding
- Founder of Winton Capital
- Manages $30+ billion
- Systematic trend following

## Common Trend Following Mistakes

1. **Exiting Too Early**: Profits run further than expected
2. **Not Taking Stops**: Hope kills accounts
3. **Trading Against Trend**: Counter-trend = low probability
4. **Overtrading Ranges**: Wait for trending markets
5. **Poor Position Sizing**: Risking too much per trade
6. **No System**: Discretionary exits destroy edge
7. **Giving Up**: Most quit before biggest trends

## Trend Following in Different Markets

### Stocks
- Best: Strong trends in growth stocks
- Use: Relative strength to market
- Avoid: Low volume, penny stocks

### Forex
- Best: Major trends in EUR/USD, GBP/USD
- Use: Higher timeframes (4H+)
- Avoid: News trading

### Commodities
- Best: Seasonal trends, supply/demand shifts
- Use: Roll calendar spreads properly
- Avoid: Expired contracts

### Crypto
- Best: Strong bull markets
- Use: Wider stops (higher volatility)
- Avoid: Low-cap altcoins

---

**Sources:**
- "Trend Following" by Michael Covel
- "Way of the Turtle" by Curtis Faith
- "The New Market Wizards" by Jack Schwager
- CMT Association: "Trend Identification and Analysis"
                    """,
                    "external_links": [
                        {
                            "title": "TurtleTrader.com",
                            "url": "https://www.turtletrader.com/",
                            "description": "Complete Turtle Trading rules and trend following resources"
                        }
                    ]
                },
                "duration_minutes": 40,
                "xp_reward": 500,
                "coin_reward": 250,
                "required_level": 6,
                "is_published": True,
                "tags": ["trend-following", "strategies", "advanced"]
            },
            
            {
                "title": "Swing Trading Strategies",
                "description": "Multi-day trading strategies for capturing medium-term moves",
                "chapter": 6,
                "order": 2,
                "type": "video",
                "difficulty": "advanced",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=JnPnGzDbyj0",
                    "video_title": "Swing Trading Strategies That Work",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=JnPnGzDbyj0",
                    "key_topics": [
                        "Swing trading timeframes",
                        "Multiple timeframe analysis",
                        "Entry and exit strategies",
                        "Position management",
                        "Risk management for swing trades"
                    ]
                },
                "duration_minutes": 32,
                "xp_reward": 450,
                "coin_reward": 225,
                "required_level": 6,
                "is_published": True,
                "tags": ["swing-trading", "strategies", "multi-day"]
            },
            
            {
                "title": "Day Trading Fundamentals",
                "description": "Intraday strategies for active traders",
                "chapter": 6,
                "order": 3,
                "type": "reading",
                "difficulty": "advanced",
                "content": {
                    "markdown": """
# Day Trading Fundamentals

## What is Day Trading?

**Day Trading** = Opening and closing all positions within the same trading day. No overnight positions.

### Key Characteristics
- Multiple trades per day (2-10+)
- Small profit targets (0.5-2%)
- Tight stop losses (0.2-0.5%)
- High win rate needed (>50%)
- Requires significant time commitment

### Capital Requirements
- **Legal Minimum (US)**: $25,000 for Pattern Day Traders (PDT rule)
- **Recommended**: $30,000-50,000 for proper risk management
- **Buying Power**: 4:1 intraday leverage (margin)

## Day Trading Schedule

### Pre-Market (7:00 AM - 9:30 AM EST)
**Tasks**:
- Review overnight news
- Check futures and international markets
- Identify gapping stocks
- Mark key support/resistance levels
- Create watchlist (5-10 stocks)
- Set price alerts

**What to Look For**:
- Earnings reports
- FDA approvals
- Upgrades/downgrades
- Economic data releases
- Sector rotation

### Market Open (9:30 AM - 10:30 AM EST)
**The Most Volatile Hour**

**Characteristics**:
- Highest volume
- Widest spreads initially
- Most volatility
- Institutional orders hit market
- Retail traders most active

**Strategies**:
- Wait 15-30 minutes for dust to settle
- Trade momentum continuation
- Watch for opening range breakouts
- Respect the first hour high/low

### Mid-Day (10:30 AM - 2:00 PM EST)
**The Grind**

**Characteristics**:
- Lower volume
- Tighter ranges
- Institutional lunch (12-1 PM)
- False breakouts common

**Approach**:
- Reduce activity or stop trading
- Focus on strongest movers only
- Tighten profit targets
- Use limit orders
- Consider stepping away

### Power Hour (3:00 PM - 4:00 PM EST)
**The Second Wave**

**Characteristics**:
- Volume increases
- Day traders closing positions
- Institutional end-of-day orders
- Trend continuation or reversal

**Strategies**:
- Trade mean reversion
- Fade extremes
- Quick scalps
- Close all positions before 4:00 PM

## Day Trading Strategies

### 1. Opening Range Breakout (ORB)

**Setup**:
- Mark first 5-15 minutes high/low
- This is the "opening range"
- Wait for breakout with volume

**Entry Rules**:
- Buy: Break above opening range high
- Volume 25%+ above average
- Momentum candle (not doji)
- Enter on break or first pullback

**Management**:
- Stop: Below opening range low
- Target: Opening range height x 2
- Trail: Move stop to breakeven at 1R

**Best For**: Trending days, gapping stocks

### 2. VWAP Strategy

**VWAP** = Volume Weighted Average Price
- Shows average price weighted by volume
- Institutional benchmark
- Acts as dynamic support/resistance

**Bullish Setup**:
- Stock trending above VWAP
- Pullback touches VWAP
- Rejection candle (wick below, close above)
- Enter long on confirmation

**Bearish Setup**:
- Stock below VWAP
- Rally to VWAP
- Rejection (wick above, close below)
- Enter short

**Rules**:
- Trade in direction of VWAP slope
- Stop 5-10 cents beyond VWAP
- Target previous high/low

### 3. Momentum/Breakout Scalping

**Scanner Criteria**:
- % Change > 5%
- Volume > 1M shares
- Price > $5
- Relative volume > 2

**Entry**:
- Stock breaking to new high-of-day (HOD)
- Volume surging (2x+ average bar)
- Green candle closing strong
- Enter on break or first 1-min pullback

**Exit**:
- Quick targets (20-40 cents)
- Stop loss below recent low
- Scale out: 1/2 at target, let rest run
- Exit all on momentum stall

**Risk**: 1% per trade, tight stops

### 4. Reversal Fade Strategy

**Setup**:
- Stock makes parabolic move (vertical spike)
- RSI > 80 or < 20
- Volume exhaustion (declining bars)
- Price makes new high/low but fails

**Short Entry** (Fade Rally):
- Stock spikes >10% in <30 minutes
- First red candle after spike
- Volume declining
- Below VWAP

**Long Entry** (Fade Selloff):
- Stock drops >5% rapidly
- First green candle
- Volume declining
- Above VWAP

**Management**:
- Very tight stops (recent high/low)
- Quick profit targets (3-5%)
- Don't fight strong trends

### 5. Gap and Go

**Gap Types**:
- **Gap Up**: Opens higher than previous close
- **Gap Down**: Opens lower than previous close

**Full Gap Strategy**:
1. Stock gaps up 3-10% on news/volume
2. Opens strong, doesn't fill gap immediately
3. Consolidates first 15 minutes
4. Breaks above first 15-min high
5. Enter long, stop below consolidation

**Partial Fill Strategy**:
1. Gap up 2-5%
2. Fills 50% of gap (pulls back)
3. Bounces at VWAP or key support
4. Enter long for gap fill continuation

### 6. Support/Resistance Bounce

**Setup**:
- Identify key daily/weekly S/R levels
- Wait for price to approach level
- Watch for reversal pattern (hammer, engulfing)
- Enter on bounce confirmation

**Rules**:
- Must be clean level (multiple touches)
- Volume should increase on approach
- Enter after confirmation candle
- Stop 10-15 cents beyond level
- Target midpoint to opposite S/R

## Day Trading Indicators

### Essential Indicators
1. **VWAP**: Institutional reference point
2. **Level 2 / Time & Sales**: Order flow
3. **Volume**: Confirm moves
4. **9 EMA**: Quick trend reference
5. **Previous Day High/Low**: Key levels

### Optional Indicators
- RSI (14): Overbought/oversold
- MACD (12,26,9): Momentum
- ATR: Volatility for stops
- Bollinger Bands: Squeeze plays

**Keep It Simple**: Maximum 3-4 indicators

## Risk Management for Day Traders

### Position Sizing
```
Risk per trade: 0.5-1% (smaller than swing trading)
Daily loss limit: 2-3%
Weekly loss limit: 6%
Monthly loss limit: 10%
```

**Example** ($50,000 account):
- Risk per trade: $250 (0.5%)
- Daily stop: $1,000 (2%)
- If hit: STOP TRADING for the day

### Stop Loss Placement
- **Technical**: Below support/above resistance
- **Fixed**: 0.20-0.50 cents per share
- **ATR**: 0.5 × ATR for tight stops
- **Time**: Exit if no movement in 15-30 min

### Profit Targets
**Method 1**: Fixed R-Multiple
- Target 2:1 or 3:1 risk:reward
- If risk $0.30, target $0.60-$0.90

**Method 2**: Technical Levels
- Previous high/low
- VWAP
- Round numbers ($50, $100, etc.)
- Fibonacci extensions

**Method 3**: Trailing
- Move stop to breakeven at +1R
- Trail with 9 EMA or VWAP
- Let winners run to close

## Building a Watchlist

### Stock Selection Criteria
**Must Have**:
- Average volume > 500K shares/day
- Price > $5 (avoid penny stocks)
- Average daily range > 3-5%
- Liquid options market (if trading options)
- News catalyst or momentum

**Good Sectors** (High volatility):
- Technology
- Biotechnology
- Energy
- Cannabis
- Small-cap growth

**Avoid**:
- Stocks < $2
- Volume < 100K
- Large spreads (>$0.05)
- Low volatility utilities/staples

### Watchlist Size
- **Active Scanner**: Real-time momentum (10-20 stocks)
- **Core List**: 5-10 stocks you know well
- **Gap List**: Pre-market gappers (5-10 stocks)

## Day Trading Psychology

### The Mental Game

**Common Mistakes**:
1. **Revenge Trading**: Trying to "get back" at market
2. **Overtrading**: Taking low-quality setups
3. **FOMO**: Chasing breakouts without confirmation
4. **Scaling Up Too Fast**: Blowing up after hot streak
5. **Not Taking Breaks**: Mental fatigue = bad decisions

**Solutions**:
- Strict daily loss limit (hard stop)
- Trade only A-setups (quality > quantity)
- Wait for confirmation, miss some moves
- Increase size only 10% per month max
- Walk away after 2 losses or 3 hours

### Performance Tracking

**Daily Metrics**:
- # of trades
- Win rate %
- Profit factor
- Largest win/loss
- Average hold time
- Best/worst trade

**Weekly Review**:
- Total P&L
- Mistakes made
- Best setups
- Patterns to avoid
- Adjust strategy

## Tools and Platforms

### Recommended Brokers
- **TD Ameritrade / Thinkorswim**: Advanced charting
- **Interactive Brokers**: Low commissions
- **TradeStation**: Powerful platform
- **Webull**: Free Level 2 data
- **Lightspeed**: Direct market access

### Essential Tools
- **Level 2 Quotes**: See order book
- **Time & Sales**: Real-time trades
- **Hotkeys**: Fast execution critical
- **Multiple Monitors**: 2-3 screens minimum
- **Scanners**: Trade Ideas, Finviz, etc.

### Costs to Consider
- Commission: $0-1 per trade (most now $0)
- Data fees: $50-200/month
- Platform fees: $0-200/month
- Software: $50-300/month (scanners, etc.)
- **Total**: $100-500/month overhead

## Transitioning from Simulator

### Paper Trading First
- **Duration**: 1-3 months minimum
- **Goal**: Consistent profitability
- **Target**: 55%+ win rate, 2:1 R:R
- **Track**: Every trade, every mistake

### Starting Live Trading
1. **Start Small**: 25-50 shares only
2. **Focus**: Execution and emotions, not profit
3. **Increase Slowly**: 10% per month if profitable
4. **Expect Regression**: Performance will drop initially
5. **Be Patient**: Takes 1-2 years to become consistently profitable

## Day Trading Success Rates

**Reality Check**:
- **90% of day traders lose money** (academic studies)
- **5-10% break even**
- **1-5% consistently profitable**

**Success Factors**:
- Sufficient capital ($30K+)
- 6-12 months learning period
- Solid risk management
- Emotional discipline
- Continuous learning
- Realistic expectations

## Is Day Trading Right for You?

### Required Traits
✓ Discipline and patience
✓ Quick decision-making ability
✓ Handle stress well
✓ Accept losses gracefully
✓ Detail-oriented
✓ Self-motivated
✓ Available during market hours

### Red Flags
✗ Need immediate income
✗ Can't afford to lose capital
✗ Emotional decision maker
✗ Gambler mentality
✗ Impatient personality
✗ Full-time job conflicts

---

**Sources:**
- "How to Day Trade for a Living" by Andrew Aziz
- "Day Trading and Swing Trading the Currency Market" by Kathy Lien
- SMB Capital Training Resources - https://www.smbtraining.com/
- Ross Cameron (Warrior Trading) - Day Trading Strategies
- Investopedia: "Day Trading" - https://www.investopedia.com/terms/d/daytrading.asp
                    """,
                    "external_links": [
                        {
                            "title": "SMB Capital Training",
                            "url": "https://www.smbtraining.com/",
                            "description": "Professional day trading education and resources"
                        },
                        {
                            "title": "Investopedia Day Trading Guide",
                            "url": "https://www.investopedia.com/day-trading-4689679",
                            "description": "Comprehensive day trading tutorial"
                        }
                    ]
                },
                "duration_minutes": 45,
                "xp_reward": 550,
                "coin_reward": 275,
                "required_level": 7,
                "is_published": True,
                "tags": ["day-trading", "intraday", "strategies", "advanced"]
            },
            
            {
                "title": "Options Trading Basics",
                "description": "Introduction to calls, puts, and basic options strategies",
                "chapter": 6,
                "order": 4,
                "type": "video",
                "difficulty": "advanced",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=7PM4rNDr4oI",
                    "video_title": "Options Trading for Beginners",
                    "channel": "projectfinance",
                    "source": "YouTube - projectfinance",
                    "source_url": "https://www.youtube.com/watch?v=7PM4rNDr4oI",
                    "key_topics": [
                        "Call and put options explained",
                        "Options pricing and Greeks",
                        "Basic strategies (covered calls, protective puts)",
                        "When to use options vs stocks",
                        "Options risk management"
                    ]
                },
                "duration_minutes": 35,
                "xp_reward": 500,
                "coin_reward": 250,
                "required_level": 7,
                "is_published": True,
                "tags": ["options", "derivatives", "strategies", "advanced"]
            },
            
            {
                "title": "Building a Trading Plan",
                "description": "Create a comprehensive, personalized trading business plan",
                "chapter": 6,
                "order": 5,
                "type": "reading",
                "difficulty": "intermediate",
                "content": {
                    "markdown": """
# Building a Trading Plan

## Why You Need a Trading Plan

**"A goal without a plan is just a wish."** - Antoine de Saint-Exupéry

### Benefits of a Written Plan
- Removes emotional decision-making
- Provides accountability
- Enables performance tracking
- Identifies what works/doesn't
- Professionalizes your approach
- Reduces psychological stress

### Without a Plan
- Inconsistent decisions
- Emotional trading
- No measurable progress
- Hard to identify mistakes
- Reactive instead of proactive

## Components of a Trading Plan

### 1. Personal Information

**Trading Goals**:
- Income target: $_____ per month/year
- % Return target: ___% annually
- Timeframe: Achieve by _____ (date)
- Why am I trading? (Motivations)

**Available Resources**:
- Starting capital: $_____
- Time available: ___ hours per day/week
- Equipment: Platform, data, tools
- Education level: Beginner/Intermediate/Advanced

**Risk Tolerance**:
- Maximum loss per trade: ____%
- Maximum daily loss: ____%
- Maximum monthly drawdown: ____%
- Capital I can afford to lose: $_____

### 2. Market Selection

**What Will You Trade**?
- [ ] US Stocks
- [ ] Forex
- [ ] Futures
- [ ] Options
- [ ] Cryptocurrencies
- [ ] ETFs

**Specific Criteria**:
- Minimum volume: _____ shares/contracts
- Price range: $_____ to $_____
- Sectors: ________________
- Market cap: ________________

**Example**:
"I will trade US large-cap stocks ($5B+) in technology and healthcare sectors, with average daily volume >1M shares, priced between $20-$200."

### 3. Trading Style

**Choose Your Approach**:
- [ ] Scalping (seconds to minutes)
- [ ] Day Trading (minutes to hours, no overnight)
- [ ] Swing Trading (days to weeks)
- [ ] Position Trading (weeks to months)

**Time Commitment**:
- Trading hours: _____ to _____ (EST)
- Days per week: _____
- Pre-market prep: _____ hours
- Post-market review: _____ hours

**Why This Matters**:
Your trading style must match your lifestyle. Day trading requires full-time availability; swing trading can be part-time.

### 4. Trading Strategy

**Strategy Name**: ________________

**Setup Criteria** (Be Specific):

**Entry Rules**:
1. ________________________________
2. ________________________________
3. ________________________________
4. ________________________________
5. ________________________________

Example:
1. Stock above 50-day MA (uptrend)
2. RSI below 40 (pullback)
3. Price at demand zone or support
4. Bullish engulfing candle forms
5. Volume above average

**Entry Trigger**:
- Aggressive: ________________
- Conservative: ________________

**Position Sizing**:
```
Risk per trade: ____%
Formula: (Account × Risk%) / (Entry - Stop)
```

**Stop Loss Rules**:
- Type: Technical / ATR / Percentage
- Placement: ________________
- Never move stop _____ (toward loss)

**Profit Targets**:
- Target 1: ___R or $_____ (take ___%)
- Target 2: ___R or $_____ (take ___%)
- Final exit: Trailing stop / Signal

**Exit Rules** (Non-Target):
1. ________________________________
2. ________________________________
3. ________________________________

### 5. Risk Management Rules

**Position Limits**:
- Maximum risk per trade: ____%
- Maximum concurrent positions: _____
- Maximum correlated positions: _____
- Maximum portfolio heat: ____%

**Loss Limits**:
- Daily stop loss: -$_____ or ____%
- Weekly stop loss: -$_____ or ____%
- Monthly stop loss: -$_____ or ____%

**Action When Hit**:
"When I hit my daily stop loss, I will _____________________________"

**Position Sizing Examples**:
```
$10,000 Account, 1% Risk

Trade 1: Entry $50, Stop $48 (2 risk)
Position: $100 / $2 = 50 shares

Trade 2: Entry $100, Stop $95 (5 risk)
Position: $100 / $5 = 20 shares
```

### 6. Trading Schedule

**Daily Routine**:

**Pre-Market** (___:___ AM):
- [ ] Check news and economic calendar
- [ ] Review overnight market action
- [ ] Update watchlist
- [ ] Identify key levels
- [ ] Set alerts
- [ ] Review trading plan

**Market Hours**:
- [ ] Execute only planned setups
- [ ] Track all trades in journal
- [ ] Follow risk management rules
- [ ] Take breaks every ___ hours
- [ ] Stay hydrated

**Post-Market** (___:___ PM):
- [ ] Close all positions (if day trading)
- [ ] Journal all trades
- [ ] Review mistakes
- [ ] Plan next day
- [ ] Update statistics

**Weekly Review** (____day):
- [ ] Calculate win rate and metrics
- [ ] Review best/worst trades
- [ ] Identify patterns
- [ ] Adjust strategy if needed
- [ ] Set goals for next week

**Monthly Review**:
- [ ] Full performance analysis
- [ ] Update trading plan
- [ ] Reassess goals
- [ ] Education/skill development
- [ ] Psychological assessment

### 7. Trading Rules & Commandments

**My Personal Trading Rules**:

1. I will never risk more than ___% per trade
2. I will always use a stop loss
3. I will never move a stop loss toward a loss
4. I will follow my trading plan 100%
5. I will not revenge trade
6. I will not overtrade
7. I will keep detailed records
8. I will continuously educate myself
9. I will accept responsibility for results
10. I will take breaks after ___ consecutive losses

**Prohibited Actions**:
- [ ] Trading without a stop loss
- [ ] Averaging down on losing trades
- [ ] Trading on tips or rumors
- [ ] Over-leveraging
- [ ] Trading while emotional
- [ ] Checking P&L constantly
- [ ] Trading during _____  (personal red flag times)

### 8. Trade Journal Requirements

**For Every Trade, Record**:

**Before Entry**:
- Date & time
- Symbol & price
- Setup/pattern
- Why entering
- Risk amount
- Position size
- Stop loss level
- Target(s)
- Chart screenshot

**After Exit**:
- Exit price & time
- P&L ($and R)
- Did I follow plan? Y/N
- Mistakes made
- Lessons learned
- Emotional state (1-10)
- What to improve

**Weekly Stats**:
- Total trades: _____
- Win rate: _____%
- Profit factor: _____
- Average R: _____
- Best trade: _____
- Worst trade: _____

### 9. Continuous Improvement

**Education Plan**:
- Books to read: ________________
- Courses to take: ________________
- Skills to develop: ________________
- Time allocated: _____ hours/week

**Performance Milestones**:
- [ ] 30-day profitable
- [ ] 60-day profitable
- [ ] 90-day profitable
- [ ] 6-month profitable
- [ ] 1-year profitable
- [ ] Can increase position size

**Review Schedule**:
- Daily: After market close
- Weekly: ____day evenings
- Monthly: First ____day of month
- Quarterly: Deep dive analysis

### 10. Emergency Procedures

**If I Experience**:
- 3 consecutive losses → _____________________
- Daily loss limit hit → _____________________
- Weekly loss limit hit → _____________________
- 20% drawdown → _____________________
- Emotional distress → _____________________
- Life stress interfering → _____________________

**Support System**:
- Trading mentor: ________________
- Trading community: ________________
- Resources: ________________

## Sample Trading Plan Template
TRADING BUSINESS PLAN
Trader: [Your Name]
Date Created: [Date]
Review Date: [Quarterly]
=== SECTION 1: GOALS ===
Annual Return Target: 20%
Monthly Income Goal: $2,000
Timeframe: 12 months
=== SECTION 2: MARKETS ===
Primary: US Large-cap stocks
Sectors: Technology, Healthcare
Volume: >1M shares daily
Price: $20-$200
=== SECTION 3: STYLE ===
Type: Swing Trading
Timeframe: 3-10 day holds
Time Commitment: 2 hours/day
Market Hours: Part-time (evenings)
=== SECTION 4: STRATEGY ===
Name: Trend Pullback Strategy
Entry Criteria:

Daily chart uptrend (price > 50 MA)
RSI pullback < 40
Price at support or demand zone
Bullish reversal candle
Volume confirmation

Position Size: 1% risk per trade
Stop Loss: Below support or 2 ATR
Target: 1:3 risk-reward minimum
=== SECTION 5: RISK MANAGEMENT ===
Risk per trade: 1%
Daily stop loss: 2%
Weekly stop loss: 5%
Max positions: 5
Portfolio heat max: 5%
=== SECTION 6: ROUTINE ===
Pre-market: 30 min (scan, plan)
Trading: Evening review & orders
Post-market: 30 min (journal)
Weekly review: Sunday, 1 hour
=== SECTION 7: RULES ===

Always use stops
No revenge trading
Max 3 trades/day
Stop after 2 losses
Follow plan 100%

=== SECTION 8: JOURNAL ===
Log every trade in spreadsheet
Screenshot every setup
Weekly performance review
Monthly deep analysis
=== SECTION 9: GROWTH ===
Read 1 trading book/month
Review 10 trades/week
Backtest strategy quarterly
Increase size 10%/quarter if profitable
=== SECTION 10: EMERGENCIES ===
3 losses → Stop for day
Daily limit → Stop until tomorrow
20% drawdown → Reduce size 50%
Emotional → Take 1 week break
SIGNATURE: _______________ DATE: _______
## Making Your Plan Work

### Print and Display
- Print your trading rules
- Post near your monitor
- Read before every session
- Review weekly

### Track Compliance
- Did I follow my plan today? Y/N
- Track compliance rate
- Goal: 95%+ adherence
- Address violations immediately

### Update Regularly
- Review monthly
- Update quarterly
- Major changes: Test first
- Document all changes

### Accountability
- Share plan with mentor/partner
- Join trading group
- Regular check-ins
- Be honest about violations

## Common Mistakes

1. **No Written Plan**: "It's in my head" doesn't work
2. **Too Vague**: "Buy low, sell high" is not a plan
3. **Too Complex**: 47-step process nobody follows
4. **Never Following It**: Plan without execution = useless
5. **Not Updating**: Markets change, plan must adapt
6. **Abandoning After Losses**: Worst time to quit
7. **No Review Process**: Can't improve without feedback

## Final Thoughts

**Your trading plan is**:
- Your business blueprint
- Your decision-making filter
- Your accountability document
- Your path to consistency

**Start simple. Stay consistent. Improve continuously.**

---

**Sources:**
- "The Trading Plan" - Investopedia
- "Trade Your Way to Financial Freedom" by Van K. Tharp
- "The Daily Trading Coach" by Brett Steenbarger
- CMT Association: "Developing a Trading Business Plan"
                    """,
                    "external_links": [
                        {
                            "title": "Investopedia Trading Plan Template",
                            "url": "https://www.investopedia.com/articles/trading/11/trading-plan.asp",
                            "description": "Step-by-step guide to creating your trading plan"
                        }
                    ]
                },
                "duration_minutes": 30,
                "xp_reward": 400,
                "coin_reward": 200,
                "required_level": 5,
                "is_published": True,
                "tags": ["trading-plan", "business-plan", "strategy", "discipline"]
            },
            
            {
                "title": "Trading Strategies Mastery Quiz",
                "description": "Comprehensive test of trend following, swing trading, and day trading concepts",
                "chapter": 6,
                "order": 6,
                "type": "quiz",
                "difficulty": "advanced",
                "content": {},
                "duration_minutes": 20,
                "xp_reward": 600,
                "coin_reward": 300,
                "badge_reward": "Strategy Master",
                "required_level": 7,
                "is_published": True,
                "tags": ["quiz", "strategies", "assessment", "advanced"]
            },
            
            # ========== CHAPTER 7: ADVANCED CONCEPTS ==========
            {
                "title": "Market Psychology and Sentiment",
                "description": "Understanding crowd behavior and contrarian thinking",
                "chapter": 7,
                "order": 1,
                "type": "reading",
                "difficulty": "advanced",
                "content": {
                    "markdown": """
# Market Psychology and Sentiment

## The Psychology of Markets

**"The stock market is a device for transferring money from the impatient to the patient."** - Warren Buffett

### Market Participants' Emotional Cycle

**Phase 1: Optimism**
- Early uptrend
- Hope builds
- Buyers enter cautiously

**Phase 2: Excitement**
- Trend confirmed
- More buyers join
- Media attention begins

**Phase 3: Thrill**
- Rapid gains
- Everyone talking about it
- FOMO kicks in

**Phase 4: Euphoria** (Market Top)
- Maximum optimism
- "It's different this time"
- Retail goes all-in
- Professionals start selling

**Phase 5: Anxiety**
- First pullback
- "Just a healthy correction"
- Diamond hands mentality

**Phase 6: Denial**
- Downtrend begins
- "It will come back"
- Averaging down starts
**Phase 7: Fear**
- Losses mounting
- Panic sets in
- Some capitulation selling

**Phase 8: Desperation**
- Heavy losses
- "Should I sell?"
- Seeking advice everywhere

**Phase 9: Panic** (Market Bottom)
- Maximum pessimism
- Capitulation selling
- "I'll never invest again"
- Professionals start buying

**Phase 10: Despondency**
- Market bottoms
- Nobody wants to buy
- Best opportunities appear

**Phase 11: Depression**
- Avoiding markets completely
- Regret and blame

**Phase 12: Hope**
- Early recovery
- Cautious optimism returns
- Cycle repeats

## Sentiment Indicators

### 1. Fear & Greed Index (CNN)
**Range**: 0-100
- 0-25: Extreme Fear (Buying opportunity)
- 25-45: Fear
- 45-55: Neutral
- 55-75: Greed
- 75-100: Extreme Greed (Selling opportunity)

**Components**:
- Market momentum (S&P 500 vs 125-day MA)
- Stock price strength
- Stock price breadth
- Put/call ratio
- Junk bond demand
- Market volatility (VIX)
- Safe haven demand

**How to Use**:
- Contrarian indicator
- Extreme fear = Buy
- Extreme greed = Sell/caution

### 2. VIX (Volatility Index)
**"The Fear Gauge"**

**Levels**:
- <12: Complacency (Warning sign)
- 12-20: Normal market
- 20-30: Elevated fear
- >30: High fear/panic
- >40: Extreme panic (Buy signal)

**Trading VIX**:
- High VIX = Market bottoms near
- Low VIX = Complacency, risk building
- VIX spikes = Buying opportunities
- Rising VIX = Hedge long positions

### 3. Put/Call Ratio
**Formula**: Put Volume / Call Volume

**Interpretation**:
- >1.0: Bearish sentiment (contrarian bullish)
- 0.7-1.0: Normal
- <0.7: Bullish sentiment (contrarian bearish)
- >1.5: Extreme fear (strong buy signal)

**Example**:
- Put/Call = 1.3 → More puts than calls → Fear → Contrarian buy

### 4. AAII Sentiment Survey
**American Association of Individual Investors**

**Weekly Survey Results**:
- % Bullish
- % Neutral  
- % Bearish

**Historical Averages**:
- Bullish: 38%
- Neutral: 31%
- Bearish: 31%

**Contrarian Signals**:
- Bullish >50% → Caution (too optimistic)
- Bearish >50% → Buy signal (excessive pessimism)
- Bullish <20% → Strong buy signal

### 5. Market Breadth Indicators

**Advance/Decline Line**:
- Advancing stocks - Declining stocks
- Confirms trend health
- Divergence = Warning

**New Highs - New Lows**:
- Healthy bull: Many new highs, few new lows
- Divergence: Price up but fewer new highs = Weakness

**Percentage of Stocks Above 50-day MA**:
- >70%: Overbought
- <30%: Oversold
- Useful for timing

## Contrarian Investing

### The Contrarian Philosophy
**"Be fearful when others are greedy, greedy when others are fearful."** - Warren Buffett

**Core Principle**:
- Crowd is often wrong at extremes
- Maximum pessimism = Opportunity
- Maximum optimism = Danger

### Contrarian Signals

**Buy Signals** (Extreme Pessimism):
- VIX >40
- Put/Call ratio >1.5
- AAII Bearish >50%
- Magazine covers: "Death of stocks"
- Friends won't talk about investing
- Financial advisors turning bearish
- Heavy insider buying

**Sell Signals** (Extreme Optimism):
- VIX <12
- Put/Call ratio <0.5
- AAII Bullish >55%
- Magazine covers: "Dow 100,000!"
- Taxi drivers giving stock tips
- Your relatives asking about crypto
- Heavy insider selling
- IPO mania

### Famous Contrarian Indicators

**Magazine Cover Indicator**:
- Businessweek "The Death of Equities" (1979) → Bull market began
- Time "Is God Dead?" (1966) → Market peak
- Multiple housing covers (2005) → Real estate crash

**Shoe Shine Boy Indicator**:
- Joe Kennedy sold before 1929 crash when shoe shine boy gave stock tips
- When "everyone" is in, top is near

**Super Bowl Indicator**:
- AFC win = Bear market
- NFC win = Bull market
- (Fun correlation, not causation)

## Behavioral Finance Biases

### Cognitive Biases Affecting Traders

**1. Confirmation Bias**
- Seeking info that confirms beliefs
- Ignoring contradictory evidence
- Solution: Actively seek opposing views

**2. Anchoring Bias**
- Fixating on purchase price
- "I'll sell when it gets back to..."
- Solution: Focus on current facts, not history

**3. Recency Bias**
- Recent events seem more important
- "This trend will continue forever"
- Solution: Study long-term history

**4. Overconfidence Bias**
- Overestimating abilities after wins
- Taking excessive risk
- Solution: Track results objectively

**5. Loss Aversion**
- Pain of loss > Pleasure of gain
- Holding losers too long
- Solution: Pre-set stop losses

**6. Herd Mentality**
- Following the crowd
- FOMO trading
- Solution: Have independent system

**7. Gambler's Fallacy**
- "I'm due for a win"
- Revenge trading
- Solution: Each trade is independent

## Market Regime Recognition

### Bull Market Psychology
**Characteristics**:
- Dips bought quickly
- Bad news ignored
- Good news celebrated
- Optimism prevails
- "Buy the dip" works

**Trading Approach**:
- Long bias
- Buy pullbacks
- Trail stops loosely
- Stay invested

### Bear Market Psychology
**Characteristics**:
- Rallies sold quickly
- Good news ignored
- Bad news amplified
- Pessimism dominates
- "Sell the rip" works

**Trading Approach**:
- Short bias or cash
- Sell rallies
- Tight stops on longs
- Preserve capital

### Sideways Market Psychology
**Characteristics**:
- Range-bound
- Mixed sentiment
- Mean reversion works
- Trend following fails

**Trading Approach**:
- Buy support, sell resistance
- Shorter timeframes
- Tighter profit targets

## Crowd Behavior Patterns

### Stages of a Bubble

**1. Stealth Phase**
- Smart money accumulates
- Public unaware
- Fundamentals improving

**2. Awareness Phase**
- Early adopters enter
- Media coverage begins
- Institutional interest

**3. Mania Phase**
- Public rushes in
- "New paradigm" thinking
- Valuations irrelevant
- Parabolic price action

**4. Blow-Off Top**
- Maximum optimism
- Vertical price spike
- Everyone all-in
- Smart money exits

**5. Crash**
- Reality sets in
- Panic selling
- "Who could have known?"
- Losses mount

**Historical Examples**:
- Tulip Mania (1637)
- South Sea Bubble (1720)
- Roaring '20s (1929)
- Dot-com Bubble (2000)
- Housing Bubble (2008)
- Crypto Bubble (2017, 2021)

### Recognizing Bubble Warning Signs
- Parabolic price charts
- "This time is different"
- Excessive leverage
- Valuations at extremes
- Everyone talking about it
- "Get rich quick" schemes
- Retail mania
- Professional caution

## Using Sentiment in Trading

### Sentiment-Based Trading Rules

**Rule 1: Fade Extremes**
- Extreme fear → Buy
- Extreme greed → Sell
- Middle range → Follow trend

**Rule 2: Confirm with Price**
- Don't fight price action
- Wait for reversal confirmation
- Sentiment + Price = Entry

**Rule 3: Multiple Timeframes**
- Check daily and weekly sentiment
- Alignment = Stronger signal

**Rule 4: Context Matters**
- Sentiment in context of trend
- Bull market dips = Buying opportunities
- Bear market rallies = Selling opportunities

### Practical Sentiment Strategy

**Weekly Routine**:
1. Check VIX level
2. Review Put/Call ratio
3. Read AAII survey
4. Check Fear & Greed Index
5. Note unusual extremes
6. Wait for price confirmation
7. Enter with proper risk management

**Example Trade**:
```
Setup:
- VIX spikes to 35 (Fear)
- Put/Call ratio = 1.4 (Bearish)
- AAII Bearish = 52% (Extreme)
- S&P 500 at support

Action:
- Wait for bullish engulfing on daily
- Enter long SPY
- Stop below support
- Target: VIX return to 20
```

## Social Media Sentiment

### Modern Sentiment Indicators

**Twitter/X Sentiment**:
- Track $Cashtags mentions
- Sentiment analysis tools
- Extreme volume = Attention peak

**Reddit WallStreetBets**:
- Retail mania indicator
- Extreme activity = Top signal
- GME, AMC examples

**Google Trends**:
- Search volume for tickers
- Parabolic searches = Top
- Declining searches = Bottom

**Crypto Twitter**:
- "Number go up" tweets = Top
- "I quit crypto" tweets = Bottom
- Laser eyes avatars = Euphoria

### Contrarian Social Signals
- Everyone posting gains → Top near
- Nobody posting about markets → Bottom near
- Your friends asking to invest → Peak
- Silence on investing → Opportunity

## Market Wizards' Psychology Insights

### Jesse Livermore
*"The market is never wrong; opinions often are."*
- Don't fight the tape
- Let market tell you direction

### Paul Tudor Jones
*"Losers average losers."*
- Don't average down
- Cut losses quickly

### George Soros
*"It's not whether you're right or wrong, but how much money you make when you're right."*
- Focus on risk/reward
- Size winners, not frequency

### Stanley Druckenmiller
*"The way to build long-term returns is through preservation of capital and home runs."*
- Capital preservation first
- Let big winners run

## Emotional Intelligence in Trading

### Developing EQ as a Trader

**Self-Awareness**:
- Recognize your emotional state
- Know your triggers
- Journal feelings

**Self-Regulation**:
- Control impulses
- Stick to plan
- Take breaks when needed

**Motivation**:
- Focus on process, not money
- Delayed gratification
- Long-term thinking

**Empathy**:
- Understand other market participants
- See both sides of trade
- Read crowd emotions

**Social Skills**:
- Learn from other traders
- Join communities
- Seek mentorship

## Practical Exercises

### Exercise 1: Sentiment Journal
Track weekly:
- VIX level
- Fear & Greed Index
- Your emotional state
- Market action
- Review monthly for patterns

### Exercise 2: Contrarian Practice
When you feel strong urge to trade:
- Wait 24 hours
- Check sentiment indicators
- Is everyone else doing same?
- Consider opposite action

### Exercise 3: Bias Identification
After each trade:
- What biases influenced decision?
- Did I confirm my bias?
- What did I ignore?
- How to improve?

---

**Sources:**
- "The Psychology of Money" by Morgan Housel
- "Thinking, Fast and Slow" by Daniel Kahneman
- "Market Wizards" series by Jack Schwager
- "Reminiscences of a Stock Operator" by Edwin Lefèvre
- CNN Fear & Greed Index - https://money.cnn.com/data/fear-and-greed/
- AAII Sentiment Survey - https://www.aaii.com/sentimentsurvey
- CBOE VIX - https://www.cboe.com/tradable_products/vix/
                    """,
                    "external_links": [
                        {
                            "title": "CNN Fear & Greed Index",
                            "url": "https://money.cnn.com/data/fear-and-greed/",
                            "description": "Real-time market sentiment indicator"
                        },
                        {
                            "title": "AAII Sentiment Survey",
                            "url": "https://www.aaii.com/sentimentsurvey",
                            "description": "Weekly investor sentiment data"
                        }
                    ]
                },
                "duration_minutes": 35,
                "xp_reward": 500,
                "coin_reward": 250,
                "required_level": 8,
                "is_published": True,
                "tags": ["psychology", "sentiment", "contrarian", "advanced"]
            },
            
            {
                "title": "Multi-Timeframe Analysis",
                "description": "Master analyzing multiple timeframes for better trade timing",
                "chapter": 7,
                "order": 2,
                "type": "video",
                "difficulty": "advanced",
                "content": {
                    "video_url": "https://www.youtube.com/watch?v=5PwPJfNEZ9E",
                    "video_title": "Multi-Timeframe Analysis Complete Guide",
                    "channel": "Rayner Teo",
                    "source": "YouTube - Rayner Teo",
                    "source_url": "https://www.youtube.com/watch?v=5PwPJfNEZ9E",
                    "key_topics": [
                        "Top-down analysis approach",
                        "Timeframe alignment",
                        "Higher timeframe bias",
                        "Lower timeframe entries",
                        "Conflicting signals resolution"
                    ]
                },
                "duration_minutes": 26,
                "xp_reward": 450,
                "coin_reward": 225,
                "required_level": 8,
                "is_published": True,
                "tags": ["multi-timeframe", "analysis", "advanced"]
            },
            
            {
                "title": "Backtesting and System Development",
                "description": "Learn to test and optimize trading strategies systematically",
                "chapter": 7,
                "order": 3,
                "type": "reading",
                "difficulty": "advanced",
                "content": {
                    "markdown": """
# Backtesting and System Development

## What is Backtesting?

**Backtesting** = Testing a trading strategy on historical data to evaluate its performance before risking real money.

### Why Backtest?
- Validates strategy effectiveness
- Identifies optimal parameters
- Reveals weaknesses before live trading
- Builds confidence in system
- Quantifies expected returns and risks

### Reality Check
*"In theory, there is no difference between theory and practice. In practice, there is."* - Yogi Berra

- Backtesting is not perfect
- Past performance ≠ Future results
- But better than blind trading

## Types of Backtesting

### 1. Manual Backtesting
**Process**:
- Scroll back on charts
- Mark setups manually
- Record hypothetical results
- Calculate statistics

**Pros**:
- No coding required
- Learn pattern recognition
- Understand price action

**Cons**:
- Time-consuming
- Susceptible to bias
- Limited sample size

### 2. Automated Backtesting
**Process**:
- Code strategy rules
- Run on historical data
- System calculates results
- Statistical analysis automatic

**Pros**:
- Fast (years in minutes)
- Large sample sizes
- Removes human bias
- Repeatable

**Cons**:
- Requires coding skills
- Can be over-optimized
- Might miss discretionary elements

### 3. Walk-Forward Analysis
**Process**:
- Optimize on period 1
- Test on period 2 (unseen data)
- Move forward and repeat
- Simulates real-world adaptation

**Pros**:
- More realistic
- Tests adaptability
- Reduces curve-fitting

**Cons**:
- More complex
- Time-intensive
- Requires more data

## Backtesting Platforms and Tools

### Free/Low-Cost Options
**TradingView**:
- Pine Script language
- Built-in strategy tester
- Visual backtesting
- Community scripts

**Python Libraries**:
- Backtrader
- Zipline
- PyAlgoTrade
- Vectorbt

**Excel**:
- Manual but powerful
- Full control
- Good for learning

### Professional Platforms
**AmiBroker** ($279):
- Powerful backtesting
- AFL coding language
- Portfolio-level testing

**NinjaTrader**:
- Free for backtesting
- C# programming
- Detailed reports

**TradeStation**:
- EasyLanguage
- Professional-grade
- Subscription required

**QuantConnect** (Free tier):
- Cloud-based
- Python/C#
- Institutional-grade

## The Backtesting Process

### Step 1: Define Strategy Rules

**Entry Rules** (Must be 100% objective):
❌ Bad: "Buy when price looks strong"
✅ Good: "Buy when price closes above 20 EMA AND RSI < 40"

**Exit Rules**:
- Stop loss: Specific price or %
- Take profit: Target levels
- Time stop: Max holding period
- Trailing stop: Algorithm

**Position Sizing**:
- Fixed shares/contracts
- Fixed dollar amount
- % of equity
- Volatility-based (ATR)

### Step 2: Gather Quality Data

**Data Requirements**:
- Sufficient history (5-10 years minimum)
- Includes all symbols you'll trade
- Adjusted for splits/dividends
- Clean (no errors)

**Data Sources**:
- Yahoo Finance (free, good for stocks)
- Quandl (paid, high quality)
- Interactive Brokers (historical data)
- Alpaca (free API)
- FirstRate Data (forex)

**Pitfalls**:
- Survivorship bias (removed bankrupt companies)
- Look-ahead bias (using future data)
- Data-snooping bias (testing too many variations)

### Step 3: Run Initial Backtest

**Basic Metrics to Track**:
- Total Return
- # of Trades
- Win Rate %
- Average Win
- Average Loss
- Profit Factor
- Maximum Drawdown
- Sharpe Ratio

**Example Output**:
```
Period: 2015-2024 (10 years)
Starting Capital: $10,000
Ending Capital: $28,450
Total Return: 184.5%
Annual Return: 11.0%
Total Trades: 487
Wins: 198 (40.7%)
Losses: 289 (59.3%)
Avg Win: $215
Avg Loss: $87
Profit Factor: 1.95
Max Drawdown: -22.3%
Sharpe Ratio: 1.2
```

### Step 4: Analyze Results

**Key Questions**:
1. Is return acceptable for risk taken?
2. Is win rate realistic?
3. Is drawdown tolerable?
4. Are there enough trades?
5. Does it make logical sense?

**Red Flags**:
- Win rate >70% (suspicious)
- No losing periods (curve-fit)
- Profit Factor >4 (probably over-optimized)
- Too few trades (<30)
- Recent performance much worse

### Step 5: Optimize Parameters

**Parameters to Test**:
- Indicator periods (10 vs 20 vs 50)
- Entry thresholds (RSI 30 vs 40)
- Stop loss sizes (1% vs 2% vs 3%)
- Profit targets (2R vs 3R)

**Optimization Methods**:

**Grid Search**:
- Test all combinations
- RSI: 20, 30, 40, 50
- MA: 10, 20, 50, 100
- = 16 combinations

**Walk-Forward**:
- Optimize on in-sample
- Test on out-of-sample
- Roll forward
- More robust

**Monte Carlo**:
- Randomize trade order
- Run 1000+ simulations
- See range of outcomes
- Assess robustness

### Step 6: Out-of-Sample Testing

**Critical Step**:
- Reserve 20-30% of data
- NEVER look at it during optimization
- Final test on unseen data
- If still profitable → Good sign

**Example**:
- Optimize: 2015-2021 (7 years)
- Test: 2022-2024 (3 years)
- If out-of-sample passes → More confidence

### Step 7: Paper Trade

**Before Going Live**:
1. Paper trade for 1-3 months
2. Track every signal
3. Execute as if real
4. Compare to backtest expectations

**Reality Check**:
- Slippage worse than expected?
- Emotions affecting execution?
- Missing trades due to timing?
- Commission impact greater?

## Backtesting Pitfalls

### 1. Over-Optimization (Curve Fitting)
**Problem**: Strategy fits historical data perfectly but fails forward

**Example**:
```
Rule: Buy when 13-day MA crosses 47-day MA, 
sell when RSI hits 67.3
```
→ Too specific, unlikely to work live

**Solution**:
- Use round numbers (10, 20, 50)
- Robust across range of parameters
- Keep rules simple
- Out-of-sample testing

### 2. Look-Ahead Bias
**Problem**: Using information not available at trade time

**Examples**:
- Using closing price before close
- Indicators that repaint
- Using tomorrow's gap in today's signal

**Solution**:
- Trade on next bar open
- Use "series" or "shifted" data
- Check indicator repainting

### 3. Survivorship Bias
**Problem**: Data includes only surviving companies

**Impact**:
- Excludes bankruptcies
- Inflates returns artificially
- Example: Enron not in S&P 500 historical data

**Solution**:
- Use survivorship-bias-free data
- Costs more but worth it
- Or accept slight inflation of results

### 4. Cherry-Picking
**Problem**: Testing many strategies, showing only best one

**Reality**:
- Test 100 strategies
- 5 will be profitable by chance
- Showing only those 5 misleads

**Solution**:
- Document all tests
- Account for multiple testing
- Use out-of-sample validation

### 5. Ignoring Costs
**Problem**: Forgetting commissions, slippage, fees

**Reality**:
```
Backtest: +$500 per trade
Commission: -$10
Slippage: -$25
Actual: +$465 (7% less)

Over 100 trades: -$3,500 difference!
```

**Solution**:
- Include realistic commissions
- Add slippage (0.1-0.5% per trade)
- Account for spread (bid-ask)

## Evaluating Backtest Results

### Performance Metrics Explained

**1. Total Return**
- Simple: Ending / Starting capital
- Not enough alone
- 100% in 1 year vs 10 years = Big difference

**2. CAGR (Compound Annual Growth Rate)**
```
CAGR = (Ending / Starting) ^ (1 / Years) - 1
```
- Standardizes across different periods
- More useful than total return

**3. Maximum Drawdown**
- Largest peak-to-valley decline
- Shows worst-case scenario
- Must be tolerable psychologically

**Example**:
- 30% drawdown = $100K → $70K
- Need 43% gain to recover
- Can you handle it?

**4. Win Rate**
```
Win Rate = Winning Trades / Total Trades
```
- Not most important metric
- 30% win rate can be profitable
- Depends on risk:reward

**5. Profit Factor**
```
Profit Factor = Gross Profit / Gross Loss
```
- >1 = Profitable
- >1.5 = Good
- >2 = Excellent
- >3 = Suspicious (might be curve-fit)

**6. Expectancy**
```
Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
```
- Average $ per trade
- Must be positive
- Higher = Better

**Example**:
```
Win Rate: 40%
Avg Win: $300
Avg Loss: $100

Expectancy = (0.4 × $300) - (0.6 × $100)
           = $120 - $60
           = $60 per trade
```

**7. Sharpe Ratio**
```
Sharpe = (Return - Risk-Free Rate) / Std Deviation
```
- Risk-adjusted return
- >1 = Good
- >2 = Very good
- >3 = Excellent

**8. Sortino Ratio**
- Like Sharpe but only penalizes downside volatility
- Better metric for traders
- >2 = Good

**9. Recovery Factor**
```
Recovery Factor = Net Profit / Max Drawdown
```
- How fast strategy recovers
- >3 = Good
- >5 = Excellent

### Minimum Acceptable Standards

**For Profitable System**:
- CAGR: >10%
- Max DD: <25%
- Profit Factor: >1.5
- Sharpe Ratio: >0.5
- Expectancy: Positive
- Minimum Trades: 100+
- Out-of-sample: Profitable

## Building Robust Systems

### Principles of Robust Design

**1. Simplicity**
- Fewer rules = More robust
- 3-5 rules ideal
- Complex ≠ Better

**2. Logic al Foundation**
- Strategy should make sense
- Based on market inefficiency
- Explainable to others

**3. Parameter Stability**
- Works across range of values
- Not just at 17 but fails at 16/18
- Plateau vs spike in results

**4. Market Regime Awareness**
- Performs in different markets
- Or knows when to step aside
- Adapts to conditions

**5. Position Sizing**
- Incorporates risk management
- Volatility-based sizing
- Survives bad runs

### System Development Workflow

    Market Observation ↓
    Hypothesis Formation ↓
    Rules Definition ↓
    Initial Backtest ↓
    Analysis & Refinement ↓
    Optimization ↓
    Out-of-Sample Test ↓
    Walk-Forward Analysis ↓
    Monte Carlo Simulation ↓
    Paper Trading ↓
    Small Live Position ↓
    Full Implementation


## Advanced Backtesting Techniques

### Monte Carlo Simulation
**Purpose**: Test strategy robustness

**Process**:
1. Take backtest trades
2. Randomize order 1000+ times
3. Analyze distribution of outcomes
4. Identify worst-case scenarios

**Insights**:
- Range of possible returns
- Probability of achieving goals
- Confidence intervals
- Risk of ruin

### Position Sizing Optimization
**Test Different Models**:
- Fixed fractional
- Kelly Criterion
- Optimal f
- Volatility-based

**Find Balance**:
- Maximum growth
- Acceptable drawdown
- Psychological comfort

### Market Regime Filtering
**Concept**: Trade only in favorable conditions

**Filters to Test**:
- Market trend (S&P above/below 200 MA)
- Volatility (VIX levels)
- Breadth (% stocks above 50 MA)
- Seasonality (month of year)

**Result**: Often improves risk-adjusted returns

## Common Backtest Mistakes

1. **Not Accounting for Gaps**: Your stop might get blown through
2. **Using Closing Prices**: Can't trade there in real-time
3. **Perfect Entries**: Always buying at support exact low
4. **No Slippage**: Assuming filled at exact price
5. **Unlimited Liquidity**: Large orders move price
6. **Indicator Repainting**: Signal changes after bar closes
7. **Data Errors**: Bad ticks, missing data
8. **Not Including Dividends**: Affects long-term returns
9. **Ignoring Margin Calls**: Overleveraging
10. **Emotional Factors**: Can't backtest fear/greed

## From Backtest to Live Trading

### Expectation Setting
- Live results will be worse than backtest
- Accept 20-30% performance degradation
- If backtest: 20% annually
- Expect live: 14-16% annually

### Gradual Implementation
**Phase 1**: Paper trade (1-3 months)
**Phase 2**: Trade smallest size (1-3 months)
**Phase 3**: Scale to 50% size (3-6 months)
**Phase 4**: Full size (after consistent results)

### Ongoing Monitoring
- Track monthly performance
- Compare to backtest expectations
- If significantly worse → Investigate
- Markets change → Adapt or retire strategy

### When to Stop a Strategy
- 2+ years underperformance
- Market structure changed
- Drawdown exceeds historical maximum by 50%
- No longer makes logical sense
- Better opportunities elsewhere

---

**Sources:**
- "Evidence-Based Technical Analysis" by David Aronson
- "Quantitative Trading" by Ernest Chan
- "Building Winning Algorithmic Trading Systems" by Kevin Davey
- QuantStart - https://www.quantstart.com/
- QuantInsti Blog - https://blog.quantinsti.com/
                    """,
                    "external_links": [
                        {
                            "title": "QuantStart Backtesting Guide",
                            "url": "https://www.quantstart.com/articles/Backtesting-Systematic-Trading-Strategies-in-Python-Considerations-and-Open-Source-Frameworks",
                            "description": "Comprehensive guide to systematic backtesting"
                        }
                    ]
                },
                "duration_minutes": 45,
                "xp_reward": 600,
                "coin_reward": 300,
                "required_level": 8,
                "is_published": True,
                "tags": ["backtesting", "system-development", "advanced", "quantitative"]
            },
            
            {
                "title": "Advanced Concepts Final Quiz",
                "description": "Master-level assessment of psychology, multi-timeframe analysis, and backtesting",
                "chapter": 7,
                "order": 4,
                "type": "quiz",
                "difficulty": "advanced",
                "content": {},
                "duration_minutes": 25,
                "xp_reward": 700,
                "coin_reward": 350,
                "badge_reward": "Trading Master",
                "required_level": 8,
                "is_published": True,
                "tags": ["quiz", "advanced", "master-level", "assessment"]
            },
        ]
        
        # Create lessons
        created_lessons = []
        for lesson_data in lessons_data:
            lesson = Lesson(**lesson_data)
            db.add(lesson)
            created_lessons.append(lesson)
        
        db.commit()
        print(f"✅ Created {len(created_lessons)} lessons successfully!")
        
        return created_lessons
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating lessons: {str(e)}")
        raise
    finally:
        db.close()


def create_quiz_questions():
    """Create quiz questions for all quiz-type lessons"""
    db: Session = SessionLocal()
    
    try:
        # Get all quiz lessons
        quiz_lessons = db.query(Lesson).filter(Lesson.type == "quiz").all()
        
        quiz_questions_data = {
            # Chapter 1: Trading Fundamentals Quiz
            "Trading Fundamentals Quiz": [
                {
                    "question": "What is the primary difference between trading and investing?",
                    "options": [
                        "Trading is always more profitable",
                        "Trading focuses on short to medium-term price movements, investing focuses on long-term value",
                        "Investing requires more capital",
                        "Trading doesn't require research"
                    ],
                    "correct_answer": 1,
                    "explanation": "Trading typically involves shorter timeframes and focuses on price movements, while investing is a long-term approach focused on company fundamentals and value growth."
                },
                {
                    "question": "What does a limit order guarantee?",
                    "options": [
                        "Immediate execution",
                        "The price you'll pay or receive (or better)",
                        "Your order will be filled",
                        "No slippage"
                    ],
                    "correct_answer": 1,
                    "explanation": "A limit order guarantees the price (or better) but does NOT guarantee execution. The trade will only execute if the market reaches your specified price."
                },
                {
                    "question": "Which type of stock typically has voting rights?",
                    "options": [
                        "Preferred stock",
                        "Convertible bonds",
                        "Common stock",
                        "ETFs"
                    ],
                    "correct_answer": 2,
                    "explanation": "Common stockholders typically have voting rights in company decisions, while preferred stockholders usually do not but receive priority in dividends."
                },
                {
                    "question": "What is the bid-ask spread?",
                    "options": [
                        "The difference between yesterday's close and today's open",
                        "The difference between the highest buy price and lowest sell price",
                        "The commission charged by brokers",
                        "The daily price range"
                    ],
                    "correct_answer": 1,
                    "explanation": "The bid-ask spread is the difference between the highest price a buyer is willing to pay (bid) and the lowest price a seller is willing to accept (ask)."
                },
                {
                    "question": "What happens when you place a market order?",
                    "options": [
                        "You wait for your specified price",
                        "You buy/sell immediately at the current market price",
                        "Your order expires at end of day",
                        "You get the average price"
                    ],
                    "correct_answer": 1,
                    "explanation": "A market order executes immediately at the best available current price, guaranteeing execution but not price."
                }
            ],
            
            # Chapter 2: Technical Analysis Foundations Quiz
            "Technical Analysis Foundations Quiz": [
                {
                    "question": "What does a 'doji' candlestick indicate?",
                    "options": [
                        "Strong bullish momentum",
                        "Strong bearish momentum",
                        "Indecision and potential reversal",
                        "Guaranteed trend continuation"
                    ],
                    "correct_answer": 2,
                    "explanation": "A doji forms when open and close are nearly equal, indicating indecision between buyers and sellers and potentially signaling a reversal."
                },
                {
                    "question": "In an uptrend, how do you identify the trend line?",
                    "options": [
                        "Connect the highs",
                        "Connect at least 2-3 swing lows",
                        "Use the 50-day moving average",
                        "Draw a horizontal line"
                    ],
                    "correct_answer": 1,
                    "explanation": "In an uptrend, the trend line is drawn by connecting at least 2-3 swing lows (support points). The line should not cut through price bars."
                },
                {
                    "question": "What is a key characteristic of a valid support level?",
                    "options": [
                        "Price never touches it",
                        "Multiple tests where price bounced",
                        "It's always a round number",
                        "It only works once"
                    ],
                    "correct_answer": 1,
                    "explanation": "Valid support levels show multiple instances where price approached the level and bounced, confirming buying interest at that price."
                },
                {
                    "question": "What does a bullish engulfing pattern signal?",
                    "options": [
                        "Continuation of downtrend",
                        "Potential reversal to upside",
                        "Market uncertainty",
                        "Time to sell"
                    ],
                    "correct_answer": 1,
                    "explanation": "A bullish engulfing pattern (large green candle completely engulfing previous red candle) signals potential reversal from downtrend to uptrend."
                },
                {
                    "question": "What is the primary purpose of resistance levels?",
                    "options": [
                        "To determine stop loss placement",
                        "Areas where selling pressure may overcome buying",
                        "To calculate position size",
                        "To identify volume spikes"
                    ],
                    "correct_answer": 1,
                    "explanation": "Resistance levels identify price areas where selling pressure historically exceeded buying pressure, potentially halting upward movement."
                }
            ],
            
            # Chapter 3: Technical Indicators Mastery Quiz
            "Technical Indicators Mastery Quiz": [
                {
                    "question": "What does RSI above 70 traditionally indicate?",
                    "options": [
                        "Strong buy signal",
                        "Potential overbought condition",
                        "Guaranteed reversal",
                        "Market crash incoming"
                    ],
                    "correct_answer": 1,
                    "explanation": "RSI above 70 indicates potentially overbought conditions, but doesn't guarantee immediate reversal. Markets can remain overbought during strong trends."
                },
                {
                    "question": "What is a 'Golden Cross'?",
                    "options": [
                        "When price crosses above resistance",
                        "When 50-day MA crosses above 200-day MA",
                        "When RSI reaches 100",
                        "When volume doubles"
                    ],
                    "correct_answer": 1,
                    "explanation": "A Golden Cross occurs when the 50-day moving average crosses above the 200-day moving average, signaling potential long-term bullish momentum."
                },
                {
                    "question": "What does MACD histogram measure?",
                    "options": [
                        "Trading volume",
                        "Price volatility",
                        "Distance between MACD line and signal line",
                        "Market sentiment"
                    ],
                    "correct_answer": 2,
                    "explanation": "The MACD histogram represents the difference between the MACD line and signal line, showing momentum strength and potential divergences."
                },
                {
                    "question": "What does a Bollinger Band 'squeeze' suggest?",
                    "options": [
                        "Market crash",
                        "Low volatility with potential breakout coming",
                        "Time to close all positions",
                        "Strong trending market"
                    ],
                    "correct_answer": 1,
                    "explanation": "A Bollinger Band squeeze (bands narrowing) indicates low volatility and often precedes significant price moves as volatility expands."
                },
                {
                    "question": "What is bullish divergence in RSI?",
                    "options": [
                        "RSI and price both making higher highs",
                        "Price making lower lows while RSI makes higher lows",
                        "RSI above 70",
                        "RSI and MACD aligning"
                    ],
                    "correct_answer": 1,
                    "explanation": "Bullish divergence occurs when price makes lower lows but RSI makes higher lows, suggesting weakening downward momentum and potential reversal."
                },
                {
                    "question": "What is the primary advantage of EMA over SMA?",
                    "options": [
                        "It's easier to calculate",
                        "It gives more weight to recent prices",
                        "It never gives false signals",
                        "It works on all timeframes"
                    ],
                    "correct_answer": 1,
                    "explanation": "EMA (Exponential Moving Average) gives more weight to recent price data, making it more responsive to current price changes than SMA."
                }
            ],
            
            # Chapter 4: Risk Management Master Quiz
            "Risk Management Master Quiz": [
                {
                    "question": "What is the recommended maximum risk per trade for most traders?",
                    "options": [
                        "5-10%",
                        "1-2%",
                        "10-20%",
                        "Whatever feels right"
                    ],
                    "correct_answer": 1,
                    "explanation": "Professional traders typically risk only 1-2% of their account per trade to ensure survival through losing streaks and long-term sustainability."
                },
                {
                    "question": "If you lose 50% of your account, what % gain do you need to break even?",
                    "options": [
                        "50%",
                        "75%",
                        "100%",
                        "150%"
                    ],
                    "correct_answer": 2,
                    "explanation": "If you lose 50% (e.g., $10,000 to $5,000), you need a 100% gain ($5,000 profit) to return to $10,000. This demonstrates why capital preservation is critical."
                },
                {
                    "question": "What is the minimum acceptable risk-reward ratio?",
                    "options": [
                        "1:1",
                        "1:2",
                        "1:5",
                        "2:1"
                    ],
                    "correct_answer": 1,
                    "explanation": "Most successful traders aim for at least 1:2 risk-reward, meaning they risk $1 to make $2. This allows profitability even with win rates below 50%."
                },
                {
                    "question": "What should you do after hitting your daily loss limit?",
                    "options": [
                        "Trade larger to make it back",
                        "Stop trading for the day",
                        "Switch to different strategy",
                        "Lower your stop losses"
                    ],
                    "correct_answer": 1,
                    "explanation": "When you hit your daily loss limit, stop trading immediately. Revenge trading and attempting to 'make it back' typically leads to larger losses."
                },
                {
                    "question": "How should position size be calculated?",
                    "options": [
                        "Always use same number of shares",
                        "Based on account risk and distance to stop loss",
                        "Based on how confident you feel",
                        "Maximum buying power available"
                    ],
                    "correct_answer": 1,
                    "explanation": "Position size = (Account Risk $) / (Entry Price - Stop Loss Price). This ensures consistent risk across all trades regardless of stop distance."
                },
                {
                    "question": "What is 'portfolio heat'?",
                    "options": [
                        "Account temperature",
                        "Total risk across all open positions",
                        "Daily trading volume",
                        "Emotional state"
                    ],
                    "correct_answer": 1,
                    "explanation": "Portfolio heat refers to the total combined risk of all open positions. Most professionals limit this to 6-8% of total account value."
                }
            ],
            
            # Chapter 5: Chart Patterns Mastery Quiz
            "Chart Patterns Mastery Quiz": [
                {
                    "question": "What is the target for a cup and handle pattern?",
                    "options": [
                        "Previous high",
                        "Cup depth added to breakout point",
                        "200% of cup width",
                        "Next resistance level"
                    ],
                    "correct_answer": 1,
                    "explanation": "The price target for a cup and handle is calculated by measuring the depth of the cup and adding it to the breakout point above the handle."
                },
                {
                    "question": "Which pattern is considered most reliable according to Bulkowski's research?",
                    "options": [
                        "Head and shoulders",
                        "Double top",
                        "Cup and handle",
                        "Rising wedge"
                    ],
                    "correct_answer": 2,
                    "explanation": "The cup and handle pattern has one of the highest success rates (>80%) in reaching its target according to Thomas Bulkowski's extensive pattern research."
                },
                {
                    "question": "What indicates a valid head and shoulders pattern?",
                    "options": [
                        "Three peaks of exactly equal height",
                        "Middle peak (head) higher than shoulders",
                        "No volume requirements",
                        "Forms in one day"
                    ],
                    "correct_answer": 1,
                    "explanation": "A valid head and shoulders has a middle peak (head) that is distinctly higher than the two outer peaks (shoulders), with confirmation on break of neckline."
                },
                {
                    "question": "What does a bullish flag pattern indicate?",
                    "options": [
                        "Trend reversal",
                        "Market consolidation before continuation upward",
                        "Time to exit",
                        "Bearish signal"
                    ],
                    "correct_answer": 1,
                    "explanation": "A bullish flag is a continuation pattern showing brief consolidation (the flag) after a strong upward move (the pole) before continuing higher."
                },
                {
                    "question": "In supply and demand trading, what makes a zone 'fresh'?",
                    "options": [
                        "It was just created today",
                        "Price hasn't returned to test it since formation",
                        "It has high volume",
                        "It's near a round number"
                    ],
                    "correct_answer": 1,
                    "explanation": "A 'fresh' zone is one that price hasn't returned to since its creation, meaning institutional orders remain unfilled and it has higher probability of reaction."
                }
            ],
            
            # Chapter 6: Trading Strategies Mastery Quiz
            "Trading Strategies Mastery Quiz": [
                {
                    "question": "What is the typical win rate for trend following strategies?",
                    "options": [
                        "70-80%",
                        "60-70%",
                        "50-60%",
                        "30-40%"
                    ],
                    "correct_answer": 3,
                    "explanation": "Trend following strategies typically have win rates of 30-40% but remain profitable through large winners and small losers (high risk-reward ratios)."
                },
                {
                    "question": "What is the PDT (Pattern Day Trader) rule in the US?",
                    "options": [
                        "Must have $10,000 minimum",
                        "Must have $25,000 minimum for 4+ day trades per week",
                        "No day trading allowed",
                        "Only applies to options"
                    ],
                    "correct_answer": 1,
                    "explanation": "The PDT rule requires accounts to maintain $25,000 minimum equity if making 4 or more day trades within 5 business days."
                },
                {
                    "question": "What is VWAP primarily used for in day trading?",
                    "options": [
                        "Calculating profits",
                        "Dynamic support/resistance and institutional benchmark",
                        "Determining position size",
                        "Predicting closing price"
                    ],
                    "correct_answer": 1,
                    "explanation": "VWAP (Volume Weighted Average Price) serves as dynamic support/resistance and is used by institutions as a benchmark, making it valuable for entries and exits."
                },
                {
                    "question": "What time period is typically most volatile for day traders?",
                    "options": [
                        "12:00 PM - 1:00 PM (Lunch)",
                        "9:30 AM - 10:30 AM (Market open)",
                        "11:00 AM - 2:00 PM (Mid-day)",
                        "After 4:00 PM (After hours)"
                    ],
                    "correct_answer": 1,
                    "explanation": "The first hour after market open (9:30-10:30 AM EST) is typically the most volatile period with highest volume, offering the most opportunities and risks."
                },
                {
                    "question": "In swing trading, what is the typical holding period?",
                    "options": [
                        "Minutes to hours",
                        "Hours to one day",
                        "Days to weeks",
                        "Months to years"
                    ],
                    "correct_answer": 2,
                    "explanation": "Swing trading involves holding positions for days to weeks, aiming to capture larger price swings than day trading but shorter than position trading."
                },
                {
                    "question": "What should you do when a trend following system enters a drawdown?",
                    "options": [
                        "Immediately stop trading",
                        "Double position sizes",
                        "Continue following the system with discipline",
                        "Switch to counter-trend strategy"
                    ],
                    "correct_answer": 2,
                    "explanation": "Trend following systems naturally experience 20-30% drawdowns. The key is maintaining discipline and continuing to follow the system, as drawdowns often precede the best performance."
                }
            ],
            
            # Chapter 7: Advanced Concepts Final Quiz
            "Advanced Concepts Final Quiz": [
                {
                    "question": "What does a VIX level above 40 typically indicate?",
                    "options": [
                        "Market complacency",
                        "Normal conditions",
                        "Extreme fear - potential buying opportunity",
                        "Bull market peak"
                    ],
                    "correct_answer": 2,
                    "explanation": "VIX above 40 indicates extreme fear and volatility, which historically has been a contrarian buying signal as markets often bottom during panic."
                },
                {
                    "question": "What is the contrarian approach to market sentiment?",
                    "options": [
                        "Follow the crowd",
                        "Buy when others are greedy, sell when fearful",
                        "Be fearful when others are greedy, greedy when fearful",
                        "Ignore sentiment completely"
                    ],
                    "correct_answer": 2,
                    "explanation": "Contrarian investing, as advocated by Warren Buffett, means buying when the crowd is fearful (bottoms) and selling when the crowd is greedy (tops)."
                },
                {
                    "question": "In multi-timeframe analysis, which timeframe determines the overall bias?",
                    "options": [
                        "The lowest timeframe",
                        "The higher timeframe",
                        "They're all equal",
                        "Whichever is trending"
                    ],
                    "correct_answer": 1,
                    "explanation": "In top-down analysis, the higher timeframe determines the overall trend bias, while lower timeframes are used for precise entry timing."
                },
                {
                    "question": "What is the main purpose of backtesting?",
                    "options": [
                        "To guarantee future profits",
                        "To validate strategy effectiveness before risking real money",
                        "To find the perfect strategy",
                        "To eliminate all losing trades"
                    ],
                    "correct_answer": 1,
                    "explanation": "Backtesting helps validate whether a strategy has an edge and quantify expected performance, though past results don't guarantee future success."
                },
                {
                    "question": "What is 'curve fitting' in backtesting?",
                    "options": [
                        "Optimizing for maximum profit",
                        "Over-optimizing parameters to fit historical data perfectly",
                        "Using curved trend lines",
                        "Adjusting for inflation"
                    ],
                    "correct_answer": 1,
                    "explanation": "Curve fitting (over-optimization) means tailoring a strategy too specifically to historical data, causing it to fail in live trading when market conditions differ."
                },
                {
                    "question": "What is a healthy Sharpe Ratio for a trading strategy?",
                    "options": [
                        "< 0",
                        "0 - 0.5",
                        "> 1.0",
                        "Doesn't matter"
                    ],
                    "correct_answer": 2,
                    "explanation": "A Sharpe Ratio above 1.0 indicates good risk-adjusted returns, above 2.0 is very good, and above 3.0 is excellent (though rare and possibly over-optimized)."
                },
                {
                    "question": "When should you consider retiring a trading strategy?",
                    "options": [
                        "After first losing month",
                        "After 2+ years of underperformance vs backtest",
                        "Never - stick with it forever",
                        "When you feel like it"
                    ],
                    "correct_answer": 1,
                    "explanation": "If a strategy underperforms its backtest expectations for 2+ years or exceeds historical maximum drawdown by 50%, it may indicate market structure changes requiring strategy retirement."
                }
            ]
        }
        
        # Create questions for each quiz
        total_questions = 0
        for lesson in quiz_lessons:
            db.refresh(lesson)  # refresh from DB to make sure it's attached
            if lesson.title in quiz_questions_data:
                questions = quiz_questions_data[lesson.title]
                for idx, q_data in enumerate(questions, 1):
                    question = LessonQuizQuestion(
                        lesson_id=lesson.id,
                        question_text=q_data["question"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"],
                        order=idx
                    )
                    db.add(question)
                    total_questions += 1
        
        db.commit()
        print(f"✅ Created {total_questions} quiz questions successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating quiz questions: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 Starting Enhanced Seed Script")
    print("=" * 60)
    
    try:
        # Create database tables
        print("\n📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created!")
        
        # Create lessons
        print("\n📚 Creating comprehensive lessons...")
        lessons = create_comprehensive_lessons()
        print(f"✅ Created {len(lessons)} lessons across 7 chapters!")
        
        db: Session = SessionLocal()
        lessons = db.query(Lesson).all()
        db.close()
        
        # Create quiz questions
        print("\n❓ Creating quiz questions...")
        create_quiz_questions()
        print("✅ Quiz questions created!")
        
        # Summary
        print("\n" + "=" * 60)
        print("✨ SEED SCRIPT COMPLETED SUCCESSFULLY! ✨")
        print("=" * 60)
        print("\n📈 Summary:")
        print(f"   • Chapters: 7 (Fundamentals to Advanced)")
        print(f"   • Lessons: {len(lessons)}")
        print(f"   • Videos: {len([l for l in lessons if l.type == 'video'])}")
        print(f"   • Reading Materials: {len([l for l in lessons if l.type == 'reading'])}")
        print(f"   • Quizzes: {len([l for l in lessons if l.type == 'quiz'])}")
        print(f"   • Simulations: {len([l for l in lessons if l.type == 'simulation'])}")
        print("\n🎓 Learning Path:")
        print("   1. Trading Fundamentals (Beginner)")
        print("   2. Technical Analysis Basics (Beginner)")
        print("   3. Technical Indicators (Intermediate)")
        print("   4. Risk Management (Intermediate)")
        print("   5. Chart Patterns & Price Action (Intermediate/Advanced)")
        print("   6. Trading Strategies (Advanced)")
        print("   7. Advanced Concepts (Advanced)")
        print("\n🎮 Ready to start your trading education journey!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()


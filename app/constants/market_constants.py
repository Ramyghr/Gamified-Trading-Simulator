"""
Market constants with comprehensive symbol lists
"""
from enum import Enum


class AssetClass(str, Enum):
    STOCK = "stock"
    FOREX = "forex"
    CRYPTO = "crypto"
    INDEX = "index"
    COMMODITY = "commodity"
    BOND = "bond"


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class DataProvider(str, Enum):
    POLYGON = "polygon"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    TWELVE_DATA = "twelve_data"
    BINANCE = "binance"
    COINGECKO = "coingecko"


# ============================================================================
# Comprehensive Symbol Lists
# ============================================================================

# Popular US Stocks (100+ symbols)
POPULAR_STOCKS = [
    # Mega Cap Tech (FAANG+)
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    
    # Other Major Tech
    "AMD", "INTC", "NFLX", "ADBE", "CRM", "ORCL", "CSCO", "IBM",
    "AVGO", "TXN", "QCOM", "INTU", "NOW", "PANW", "SHOP", "SQ",
    "SNOW", "PLTR", "ABNB", "UBER", "LYFT", "DOCU", "ZM", "OKTA",
    "DDOG", "NET", "CRWD", "ZS", "MDB", "TEAM", "WDAY", "VEEV",
    
    # Financial Services
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP",
    "V", "MA", "PYPL", "FIS", "FISV", "SQ", "COIN",
    
    # Consumer Discretionary
    "WMT", "HD", "NKE", "MCD", "SBUX", "DIS", "COST", "TGT", "LOW",
    "BKNG", "CMG", "YUM", "LULU", "RCL", "MAR", "HLT",
    
    # Consumer Staples
    "PG", "KO", "PEP", "PM", "MO", "WBA", "CL", "KMB", "GIS", "K",
    
    # Healthcare & Biotech
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "ABT", "MRK", "LLY", "DHR",
    "AMGN", "BMY", "GILD", "REGN", "VRTX", "BIIB", "CVS", "CI",
    "ISRG", "SYK", "MDT", "BSX", "EW", "ZBH",
    
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "VLO", "MPC", "OXY",
    "HAL", "BKR", "DVN", "FANG", "MRO",
    
    # Industrials
    "BA", "HON", "UPS", "CAT", "GE", "MMM", "LMT", "RTX", "DE",
    "UNP", "CSX", "NSC", "FDX", "DAL", "UAL", "AAL", "LUV",
    
    # Communication Services
    "T", "VZ", "TMUS", "CMCSA", "CHTR", "DIS", "NFLX", "PARA",
    
    # Automotive & EV
    "F", "GM", "TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI",
    
    # Semiconductors
    "NVDA", "AMD", "INTC", "TSM", "ASML", "AMAT", "LRCX", "KLAC",
    "MU", "MRVL", "NXPI", "ADI", "MCHP", "ON",
    
    # Real Estate
    "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL",
    
    # Materials
    "LIN", "APD", "ECL", "SHW", "NEM", "FCX", "NUE", "VMC",
    
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"
]

# Cryptocurrencies (50+ major coins)
POPULAR_CRYPTO = [
    # Top 10 by Market Cap
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC",
    
    # DeFi Blue Chips
    "LINK", "UNI", "AAVE", "MKR", "COMP", "SNX", "CRV", "BAL", "YFI", "SUSHI",
    
    # Layer 1 Blockchains
    "ATOM", "NEAR", "ALGO", "FTM", "ONE", "HBAR", "EGLD", "FLOW", "ICP",
    "APT", "SUI", "SEI",
    
    # Layer 2 Solutions
    "ARB", "OP", "IMX", "LRC", "METIS", "BOBA",
    
    # Exchange Tokens
    "BNB", "FTT", "OKB", "HT", "KCS",
    
    # Meme Coins
    "SHIB", "PEPE", "FLOKI", "BONK",
    
    # Gaming & Metaverse
    "AXS", "SAND", "MANA", "ENJ", "GALA", "IMX", "APE",
    
    # Other Major Coins
    "LTC", "BCH", "XLM", "VET", "FIL", "GRT", "THETA", "XTZ",
    "EOS", "IOTA", "NEO", "DASH", "ZEC", "WAVES"
]

# Major Forex Pairs (40+ pairs)
POPULAR_FOREX = [
    # Major Pairs (USD based)
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD",
    
    # Minor Pairs (Cross pairs)
    "EUR/GBP", "EUR/JPY", "GBP/JPY", "EUR/CHF", "EUR/AUD", "EUR/CAD",
    "GBP/CHF", "GBP/AUD", "GBP/CAD", "AUD/JPY", "AUD/CAD", "AUD/NZD",
    "CAD/JPY", "CHF/JPY", "NZD/JPY", "NZD/CAD",
    
    # Exotic Pairs
    "USD/TRY", "USD/MXN", "USD/ZAR", "USD/SGD", "USD/HKD", "USD/THB",
    "USD/SEK", "USD/NOK", "USD/DKK", "USD/PLN", "USD/HUF", "USD/CZK",
    "USD/RUB", "USD/INR", "USD/BRL", "USD/CNY", "USD/KRW"
]

# Major Stock Indices (30+ indices)
MAJOR_INDICES = [
    # US Indices
    "SPX",      # S&P 500
    "DJI",      # Dow Jones Industrial Average
    "IXIC",     # NASDAQ Composite
    "NDX",      # NASDAQ 100
    "RUT",      # Russell 2000
    "VIX",      # Volatility Index
    "SPY",      # S&P 500 ETF
    "QQQ",      # NASDAQ 100 ETF
    "IWM",      # Russell 2000 ETF
    
    # European Indices
    "FTSE",     # FTSE 100 (UK)
    "DAX",      # DAX (Germany)
    "CAC",      # CAC 40 (France)
    "IBEX",     # IBEX 35 (Spain)
    "FTSEMIB",  # FTSE MIB (Italy)
    "STOXX50E", # Euro Stoxx 50
    "SMI",      # Swiss Market Index
    
    # Asian Indices
    "N225",     # Nikkei 225 (Japan)
    "HSI",      # Hang Seng (Hong Kong)
    "SSEC",     # Shanghai Composite (China)
    "SENSEX",   # BSE Sensex (India)
    "NIFTY",    # Nifty 50 (India)
    "KOSPI",    # KOSPI (South Korea)
    "STI",      # Straits Times Index (Singapore)
    "AXJO",     # ASX 200 (Australia)
    
    # Other Global Indices
    "TSX",      # S&P/TSX Composite (Canada)
    "BOVESPA",  # Bovespa (Brazil)
    "MOEX",     # MOEX (Russia)
    "TA125",    # TA-125 (Israel)
]

# Commodities (20+ symbols)
POPULAR_COMMODITIES = [
    # Precious Metals
    "GC",       # Gold
    "SI",       # Silver
    "PL",       # Platinum
    "PA",       # Palladium
    
    # Energy
    "CL",       # Crude Oil WTI
    "BZ",       # Brent Crude
    "NG",       # Natural Gas
    "HO",       # Heating Oil
    "RB",       # Gasoline
    
    # Agricultural
    "ZC",       # Corn
    "ZW",       # Wheat
    "ZS",       # Soybeans
    "CT",       # Cotton
    "SB",       # Sugar
    "KC",       # Coffee
    "CC",       # Cocoa
    
    # Industrial Metals
    "HG",       # Copper
    "ALI",      # Aluminum
]

# ETFs by Category (50+ popular ETFs)
POPULAR_ETFS = {
    "broad_market": [
        "SPY", "VOO", "IVV",    # S&P 500
        "QQQ", "QQQM",          # NASDAQ 100
        "VTI", "ITOT",          # Total US Market
        "IWM", "VB",            # Small Cap
    ],
    "sector": [
        "XLK", "VGT",           # Technology
        "XLF", "VFH",           # Financials
        "XLE", "VDE",           # Energy
        "XLV", "VHT",           # Healthcare
        "XLY", "VCR",           # Consumer Discretionary
        "XLP", "VDC",           # Consumer Staples
        "XLI", "VIS",           # Industrials
        "XLB", "VAW",           # Materials
        "XLRE", "VNQ",          # Real Estate
        "XLU", "VPU",           # Utilities
    ],
    "international": [
        "EFA", "VEA",           # Developed Markets
        "EEM", "VWO",           # Emerging Markets
        "FXI",                  # China
        "EWJ",                  # Japan
        "EWZ",                  # Brazil
        "INDA",                 # India
    ],
    "bonds": [
        "AGG", "BND",           # Total Bond Market
        "TLT", "IEF",           # Treasury Bonds
        "LQD",                  # Investment Grade Corp
        "HYG", "JNK",           # High Yield
    ],
    "thematic": [
        "ARKK", "ARKG", "ARKF", # ARK Innovation
        "ICLN", "TAN",          # Clean Energy
        "BOTZ", "ROBO",         # Robotics/AI
        "HACK",                 # Cybersecurity
        "SKYY",                 # Cloud Computing
        "FINX",                 # FinTech
        "GNOM",                 # Genomics
    ]
}

# Market Sectors
MARKET_SECTORS = [
    "Technology",
    "Healthcare",
    "Financials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Energy",
    "Industrials",
    "Materials",
    "Real Estate",
    "Utilities",
    "Communication Services"
]

# Crypto Categories
CRYPTO_CATEGORIES = [
    "Layer 1",
    "Layer 2",
    "DeFi",
    "NFT/Gaming",
    "Meme Coins",
    "Exchange Tokens",
    "Stablecoins",
    "Privacy Coins"
]
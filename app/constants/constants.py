# Paths
VERIFY_EMAIL_PATH = "/verify-email"
RESET_PASSWORD_PATH = "/reset-password"
RESET_PASSWORD_BACKEND_PATH = "/user/reset-password"
UPDATE_PASSWORD_PATH = "/user/update-password"

# Validation
PASSWORD_MIN_LENGTH = 8

# Tokens
EMAIL_TOKEN_EXPIRATION_MINUTES = 30
JWT_EXPIRATION_DAYS = 10

# Timers
REQUEST_DELAY_MILLISECONDS = 2000

# Portfolio
STARTING_CASH_BALANCE = 10000.00  # Your requested $10,000 "Quest Cash"

# Stock Exchanges
class StockExchange:
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"

# Order Actions
class OrderAction:
    BUY = "Buy"
    SELL = "Sell"

# Order Types
class OrderType:
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"

# Order Duration
class OrderDuration:
    IOC = "IOC"
    FOK = "FOK"
    DAY = "DAY"
    GTC = "GTC"
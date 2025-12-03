# 🎮 FastAPI Gamified Trading Simulator

A modern, feature-rich trading simulation platform that combines real market data with gamified learning experiences. Practice trading stocks, forex, and crypto with virtual currency while leveling up your skills through interactive lessons and challenges.
## 🚀 Features

### 📊 Trading & Portfolio
- **Real-time Market Data** - Live quotes for stocks, forex, and crypto
- **Advanced Order Types** - Market, limit, stop-loss, take-profit
- **Leverage Trading** - Margin positions with risk management
- **Portfolio Analytics** - Performance metrics, Sharpe ratio, drawdown analysis
- **Live WebSocket** - Real-time price updates and portfolio changes

### 🎓 Gamified Learning
- **Interactive Lessons** - Trading education with quizzes and simulations
- **XP System** - Earn experience points and level up
- **Leaderboards** - Compete with other traders
- **Progress Tracking** - Monitor your learning journey

### 🔐 Enterprise Security
- **JWT Authentication** - Secure token-based auth with device management
- **Rate Limiting** - API protection against abuse
- **Role-Based Access** - Admin and user permissions
- **Password Policies** - Argon2id and bcrypt hashing

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- API keys for market data providers

### Docker Deployment (Recommended)

1. **Clone and setup**
```bash
git clone https://github.com/Ramyghr/Gamified-Trading-Simulator.git
cd Gamified-Trading-Simulator
cp .env.example .env
```

2. **Configure environment variables**
```bash
# Edit .env with your API keys
nano .env
```

3. **Launch services**
```bash
docker-compose up -d
```

4. **Access the application**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Local Development

1. **Setup virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate    # Windows
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Database setup**
```bash
# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Environment Configuration

Create a `.env` file with the following variables:

### Database & Cache
```env
DATABASE_URL=postgresql+psycopg2://usr:password@db:5432/trading_simulator
REDIS_URL=redis://redis:6379/0
```

### Security
```env
SECRET_KEY=your-jwt-secret-key-here
```

### Market Data APIs
```env
POLYGON_API_KEY=your_polygon_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
TWELVE_DATA_API_KEY=your_twelve_data_key
```

### News & Email
```env
NEWS_API_KEY=your_news_api_key
MARKETAUX_API_KEY=your_marketaux_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 📡 API Overview

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Create new account |
| `POST` | `/login` | User login |
| `POST` | `/logout` | Logout current device |
| `POST` | `/logout-all-devices` | Logout all sessions |

### Market Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/quote/{symbol}` | Real-time quotes |
| `POST` | `/api/market/quotes` | Batch quotes |
| `GET` | `/api/v1/candles/{symbol}` | Historical OHLC data |
| `GET` | `/api/market/status/{market}` | Market hours |

### Trading
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orders/` | Place new order |
| `GET` | `/orders/pending` | Pending orders |
| `DELETE` | `/orders/{order_id}` | Cancel order |
| `POST` | `/leverage/positions/open` | Open leveraged position |

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/portfolio/overview` | Portfolio summary |
| `GET` | `/portfolio/stats` | Performance metrics |
| `GET` | `/portfolio/holdings` | Current positions |
| `GET` | `/portfolio/rank` | Global ranking |

### Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/lessons/` | List all lessons |
| `POST` | `/lessons/{id}/complete` | Mark lesson complete |
| `POST` | `/lessons/{id}/submit-quiz` | Submit quiz answers |
| `GET` | `/lessons/leaderboard` | User rankings |


### Key Components
- **RESTful API** - FastAPI with automatic OpenAPI documentation
- **Database** - PostgreSQL with SQLAlchemy ORM
- **Caching** - Redis for market data and session storage
- **Real-time** - WebSocket connections for live updates
- **Background Tasks** - APScheduler for market data refresh
- **Authentication** - JWT with device management

## 🔒 Security Features

- ✅ **HTTPS Ready** - Traefik with Let's Encrypt support
- ✅ **Password Hashing** - Argon2id with 12 rounds
- ✅ **JWT Tokens** - HS256 algorithm (RS256 roadmap)
- ✅ **CORS Protection** - Strict origin allow-list
- ✅ **Rate Limiting** - Token bucket (10 requests/second per IP)
- ✅ **SQL Injection Protection** - SQLAlchemy ORM
- ✅ **XSS Prevention** - Jinja2 auto-escaping
- ✅ **CSRF Protection** - Stateless JWT (no cookies)
- ✅ **Dependency Scanning** - Dependabot integration
- ✅ **Audit Logging** - Comprehensive admin audit table

## 🗄️ Database Schema

The application uses PostgreSQL with the following main models:

- **Users** - User accounts and profiles
- **Portfolios** - Virtual trading portfolios
- **Orders** - Trading orders and executions
- **Lessons** - Educational content and progress
- **Market Data** - Real-time and historical prices
- **Watchlists** - User symbol watchlists


## 🚢 Deployment

### Production with Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules


## 📊 Monitoring & Health

- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs`
- **Database Health**: Built-in connection monitoring
- **Redis Health**: Cache status and connectivity

## 🐛 Troubleshooting

Common issues and solutions:

**Database Connection Issues**
```bash
# Run migrations manually
docker-compose exec api alembic upgrade head
```

**Market Data Not Loading**
- Verify API keys in `.env`
- Check provider status endpoints
- Review rate limiting settings

**WebSocket Connection Issues**
- Verify JWT token is valid
- Check Redis connectivity
- Review CORS settings

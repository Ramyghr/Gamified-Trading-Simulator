# 📈 FastAPI Gamified Trading Simulator



## 🏁 Quick Start (local)

1. **Clone & env**

```bash
git clone https://github.com/Ramyghr/Gamified-Trading-Simulator.git
cd Gamified-Trading-simulator
cp .env
# fill keys (see table below)

```

1. **Docker (recommended)**

```bash

docker-compose up -d              # postgres + redis + api
# migrations run automatically
# <http://localhost:8000/docs>
docker-compose up --build

```

1. **Classic (needs Python 3.11)**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

---

## 🔑 Required Environment Variables

| Var | Purpose | Example |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL | `postgresql+asyncpg://user:pass@db:5432/trading` |
| `REDIS_URL` | Cache & pub/sub | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT signature | `openssl rand -hex 32` |
| `POLYGON_API_KEY` | Real-time stocks/forex | get [here](https://polygon.io/) |
| `BINANCE_KEY` *optional* | Crypto depth | leave blank for public streams |
| `ALPHA_VANTAGE_API_KEY` *optional* | Fallback quotes | get [here](https://alphavantage.co/) |
| `NEWS_API_KEY` | Headlines | get [here](https://newsapi.org/) |
| `SMTP_*` | Email verification | Gmail / SendGrid credentials |

> Tip: Use make check-env to validate keys on startup.
> 

---

## 📡 API Overview (OpenAPI 3.1)

| Tag | Endpoint | Description | Auth |
| --- | --- | --- | --- |
| **Auth** | `POST /register` | Create account & send verification | public |
|  | `POST /login` | Obtain JWT access + refresh | public |
|  | `POST /logout` | Black-list token | user |
|  | `POST /logout-all-devices` | Increment token version | user |
| **Market** | `GET /api/market/quote/{symbol}` | Real-time quote (cached 60 s) | user |
|  | `POST /api/market/quotes` | Batch quotes (≤ 100) | user |
|  | `GET /api/market/status/{market}` | Open / closed | public |
| **Candles** | `GET /api/v1/candles/{sym}` | Historical OHLCV any timeframe | user |
| **Orders** | `POST /orders` | Market / limit / stop / take-profit | user |
|  | `DELETE /orders/{id}` | Cancel pending | user |
|  | `GET /orders/history/transactions` | Executed trades | user |
| **Portfolio** | `GET /portfolio/overview` | Cash + holdings + P&L | user |
|  | `GET /portfolio/stats` | Sharpe, win-rate, max-drawdown | user |
|  | `GET /portfolio/rank` | Global percentile | user |
| **News** | `GET /news/?symbol=AAPL` | ML sentiment news | public |
|  | `POST /news/{id}/like` | Toggle like | user |
| **WebSocket** | `ws /ws/market` | Live trades & quotes | token param |
| **Admin** | `GET /admin/users` | List all (admin only) | admin |
|  | `PATCH /admin/users/{email}/role` | Promote / demote | admin |



---

## 📊 WebSocket Protocol

Connect

```
ws://localhost:8000/ws/market?token=<JWT>

```

Subscribe

```json
{"action":"subscribe","symbols":["AAPL","BTCUSDT"]}

```

Incoming

```json
{
  "type":"trade",
  "symbol":"AAPL",
  "price":192.34,
  "size":100,
  "timestamp":1712345678901,
  "source":"polygon"
}

```


---

## 🧠 Architecture Cheat-Sheet

```
┌-------------┐     ┌-------------┐     ┌-------------┐
│  Client     │────▶│  FastAPI    │────▶│  Service    │
│  React/Web  │◀----│  Routers    │◀----│  Layer      │
└-------------┘     └-------------┘     └-------------┘
                            │
                            ▼
                    ┌-------------┐
                    │  SQLAlchemy │
                    │  Models     │
                    └------┬------┘
                           │
                    ┌------▼------┐
                    │  PostgreSQL │
                    └-------------┘

```

---

---


## 🔐 Security Checklist

| Area | Status | Notes |
| --- | --- | --- |
| HTTPS only | ✅ | Traefik auto-LetsEncrypt |
| Passwords | ✅ | Argon2id, 12 rounds |
| JWT algo | ✅ | HS256 → RS256 roadmap |
| CORS | ✅ | Strict allow-list |
| Rate limit | ✅ | Token-bucket 10 rps /ip |
| SQL injection | ✅ | SQLAlchemy ORM |
| XSS | ✅ | Jinja2 auto-escape |
| CSRF | ✅ | Stateless JWT, no cookies |
| Dependency vulns | ✅ | Dependabot weekly |
| Audit logs | ✅ | `admin_audit` table |
| Pen-test | ⏳ | Q3 2024 |

# CryptoInvest — Enterprise Cryptocurrency Investment Platform

Modern, production-oriented investment platform built with **Django 5+**, **PostgreSQL**, **Bootstrap 5**, **HTMX**, **Celery**, **Redis**, and **Django REST Framework**.

Premium fintech UI inspired by Binance / Coinbase / Bybit: glassmorphism, gradients, dark/light mode, charts, and responsive layout.

---

## Features

### Users
- Register, email verification, login, password reset
- Optional TOTP 2FA (django-otp + QR)
- KYC document upload & admin review
- Profile picture & referral system

### Dashboard
- Available balance, active investments, pending deposits/withdrawals
- Total profit, referral earnings
- Transaction history, wallet addresses, notifications
- Earnings & portfolio charts (Chart.js)

### Investments
- Admin-configurable plans (name, min/max, duration, risk, featured)
- Profit methods: % of principal, fixed amount, compound
- Daily / weekly / monthly / end-of-term payouts
- Flexible maturity, auto & manual reinvest
- Earnings calculated from admin-defined rates (not hard-coded)

### Crypto deposits
- BTC, ETH, USDT TRC20/ERC20/BEP20, BNB, LTC
- Wallet address + QR, network, tx hash, screenshot
- Status: Pending → Waiting Confirmation → Approved / Rejected
- **Balance credits only after admin approval**

### Withdrawals
- Amount, wallet address, network
- Min/max validation & available-balance check
- Funds locked until admin approve/reject

### Platform
- Modular apps, audit logs, logging, caching
- Rate limiting, CSRF/XSS/SQL injection protections (Django defaults + axes)
- REST API with token auth + OpenAPI (drf-spectacular)
- Docker Compose (web, Postgres, Redis, Celery worker & beat)

---

## Vue SPA (native-feeling app)

Modern Vue 3 + PrimeVue shell that talks to the existing Django REST API (no business-logic rewrite).

```bash
# Terminal 1 — Django API
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2 — Vue app
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173** (proxies `/api` to Django).

Production build served by Django at **`/app/`**:

```bash
cd frontend
npm run build:django
# then open http://127.0.0.1:8000/app/
```

Classic Django templates remain at `/` and `/dashboard/`.

---

## Quick start (local / SQLite)

```bash
# Windows PowerShell
cd "investment app"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # already present as .env for dev

python manage.py migrate
python manage.py seed_platform
python manage.py runserver
```

Open http://127.0.0.1:8000

**Default admin** (from seed):
- Email: `admin@cryptoinvest.local`
- Password: `AdminPass123!`

Admin panel: http://127.0.0.1:8000/admin/  
API docs: http://127.0.0.1:8000/api/docs/

---

## Docker (PostgreSQL + Redis + Celery)

```bash
# Ensure .env has USE_SQLITE=False for full stack, or rely on compose overrides
docker compose up --build
```

Services:
| Service      | Port |
|-------------|------|
| Web         | 8000 |
| PostgreSQL  | 5432 |
| Redis       | 6379 |

---

## PythonAnywhere deployment

These commands assume your PythonAnywhere username is `investment256` and your web app domain is `investment256.pythonanywhere.com`.

```bash
cd ~
git clone https://github.com/Dannyparasite256/investment.git
cd investment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.pythonanywhere.example .env
```

Edit `.env` and replace `SECRET_KEY`, then run:

```bash
python manage.py migrate
python manage.py seed_platform
python manage.py collectstatic --noinput
```

In the PythonAnywhere **Web** tab:

- Set **Source code** to `/home/investment256/investment`
- Set **Working directory** to `/home/investment256/investment`
- Set **Virtualenv** to `/home/investment256/investment/venv`
- Set the WSGI file to load `/home/investment256/investment/pythonanywhere_wsgi.py`
- Add static mapping `/static/` to `/home/investment256/investment/staticfiles`
- Add media mapping `/media/` to `/home/investment256/investment/media`

Reload the web app after changing settings.

---

## Environment variables

See `.env.example`. Important keys:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret |
| `DEBUG` | `True` / `False` |
| `USE_SQLITE` | `True` for local dev without Postgres |
| `DATABASE_URL` | Postgres URL |
| `REDIS_URL` / `CELERY_BROKER_URL` | Redis |
| `EMAIL_*` | SMTP (console backend in dev) |
| `MIN_WITHDRAWAL` / `MAX_WITHDRAWAL` | Global limits |

---

## Architecture

```
config/           # Settings, URLs, Celery, ASGI/WSGI
accounts/         # User, KYC, auth, 2FA
wallets/          # Balance, cryptocurrencies, ledger, addresses
investments/      # Plans, investments, earnings engine, Celery tasks
transactions/     # Deposits, withdrawals, history
notifications/    # In-app notifications
api/              # DRF viewsets & serializers
core/             # Audit log, middleware, dashboard, seed command
templates/        # Bootstrap 5 + glassmorphism UI
static/           # CSS / JS
```

### Earnings engine

`investments.services.process_earning` applies each plan’s **admin-configured** `profit_rate_percent`, `profit_method`, and `payout_frequency`. Celery beat runs `process_scheduled_earnings` hourly (configurable).

### Deposit workflow

1. User submits amount + currency + tx hash (+ screenshot)
2. Status `pending` / `waiting_confirmation`
3. Admin approves → wallet credited + ledger + notification
4. Admin rejects → no balance change

---

## API (v1)

- `POST /api/v1/auth/token/` — obtain token
- `GET  /api/v1/me/` — user + wallet
- `GET  /api/v1/plans/` — investment plans
- `POST /api/v1/investments/create_investment/` — invest
- `GET/POST /api/v1/deposits/` · `withdrawals/`
- `GET /api/v1/transactions/` · `earnings/` · `notifications/`

Auth: session or `Authorization: Token <key>`.

---

## Security notes

- CSRF middleware + HTMX CSRF header injection
- Django ORM (parameterized queries)
- XSS-safe templates (auto-escape)
- `django-axes` brute-force lockout
- `django-ratelimit` on auth / deposit / withdraw
- Optional HTTPS flags via env in production
- Audit log model + rotating security/audit log files

**Change `SECRET_KEY` and admin password before production.**

---

## Celery (local without Docker)

```bash
# Terminal 1
redis-server

# Terminal 2
celery -A config worker -l info

# Terminal 3
celery -A config beat -l info
```

Without Redis, web app still runs (earnings can be triggered via admin actions or by calling the task after Redis is up).

---

## Staff panel (custom admin)

Professional operations console at **`/staff/`** (requires `is_staff` or platform role).

| Area | Features |
|------|----------|
| Dashboard | Pending deposits/withdrawals, KYC queue, charts, quick actions |
| Deposits | Approve / reject (credits balance on approve) |
| Withdrawals | **Pending → Approved → Paid** / Reject (unlock funds) |
| Users | Search, detail, suspend / activate |
| KYC | Document review |
| Plans | Create/edit profit rules (admin-configured rates) |
| Crypto | Deposit addresses & limits |
| Transactions | Full log (UUID, amount, fee, currency, network, hash, admin, notes) |
| Reports | Revenue charts + **CSV / Excel / PDF** export |
| Referrals | Program config, commissions, leaderboard |
| Notifications | Broadcast to all users (WebSocket + in-app) |
| Audit / Login history | Security & admin activity trails |
| Settings | Maintenance mode, session timeout, limits |
| Support / CMS | Tickets, FAQ, Terms, Privacy |

Django admin remains at `/admin/` for low-level model edits.

### Withdrawal statuses

1. **Pending** — user submitted, funds locked  
2. **Approved** — admin approved, awaiting on-chain payout  
3. **Paid** — balance debited, optional tx hash  
4. **Rejected** — funds unlocked  

### Real-time notifications

WebSocket endpoint: `ws://host/ws/notifications/` (Django Channels).  
Events: deposit/withdrawal approve/reject, investments, referrals, system broadcasts.

### Referral system

- Shareable links: `/accounts/register/?ref=CODE`  
- User dashboard: `/referrals/`  
- Leaderboard: `/referrals/leaderboard/`  
- Commission on deposit (configurable in staff panel)

---

## License

Proprietary / use as you wish for your product. Not financial advice.

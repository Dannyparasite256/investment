# CryptoInvest SPA (Vue 3)

Native-feeling investment UI built with **Vue 3 + Vite + TypeScript + Pinia + Vue Router + PrimeVue + ApexCharts**.

Django remains the API/backend. This app consumes `/api/v1/*` with Token auth.

## Develop

```bash
# Terminal 1 — Django
cd ".."
.\venv\Scripts\python.exe manage.py runserver

# Terminal 2 — Vue
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173  
API is proxied to http://127.0.0.1:8000

## Build for production

```bash
cd frontend
npm run build
```

Outputs to `frontend/dist/`. Django can serve the SPA via the included `spa` route.

## Login

Use an existing user from the Django database (same credentials as the classic site).

Token is stored in `localStorage` as `ci_token`.

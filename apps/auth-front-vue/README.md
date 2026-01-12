# SIBU Auth Front (Vue 3 + Vite)

Front mínimo para **un solo microservicio** (Auth). Incluye:
- Register (`POST /auth/register`)
- Login (`POST /auth/login`) -> guarda el JWT en `localStorage`
- Me (`GET /auth/me`) para validar token
- Change password (`POST /auth/change-password`) por si el backend devuelve `must_change_password=true`

## 1) Requisitos
- Node.js 18+ (ideal 20+)
- El microservicio **auth** levantado en `http://localhost:8000`

## 2) Config
Copia `.env.example` a `.env` y ajusta:
```
VITE_AUTH_BASE_URL=http://localhost:8000
```

## 3) Ejecutar
```
npm install
npm run dev
```
Abre: http://localhost:5174

## 4) MUY IMPORTANTE: CORS en el backend
Tu `auth/app/main.py` no tiene CORS, entonces el navegador va a bloquear las peticiones.

Agrega esto (mínimo) en `auth/app/main.py`:

```py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SIBU Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> Si vas a usar un gateway (ej. `/api/auth`), solo cambia `VITE_AUTH_BASE_URL` y/o el `baseURL` del axios.

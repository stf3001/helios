from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.ratelimit import limiter
from app.routers import audits, auth, chat, energy, faq, houses, leads, partners, solar

app = FastAPI(title="HELIOS API", version="0.1.0")


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Trop de requêtes, réessayez dans un instant."})


# Rate limiting (doc 10 sécurité) — limites par IP appliquées sur les routes décorées (auth, chat)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # front dev — restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(houses.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(solar.router, prefix="/api")
app.include_router(audits.router, prefix="/api")
app.include_router(energy.router, prefix="/api")
app.include_router(partners.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(faq.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "helios-api"}


# Jalons à venir :
# J8: partners, leads        J9: prod        J10: agents

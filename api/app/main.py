from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, houses

app = FastAPI(title="HELIOS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # front dev — restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(houses.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "helios-api"}


# Jalons à venir :
# J3: chat (RAG)   J5: solar   J6: audits
# J7: energy (SOBRY)         J8: partners, leads

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ratings, stats, works

app = FastAPI(title="CyberDex API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(works.router)
app.include_router(ratings.router)
app.include_router(stats.router)

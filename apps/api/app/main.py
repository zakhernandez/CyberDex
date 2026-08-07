
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cyberdex API")

# Allow frontend to call API

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

DbSession = Annotated[Session, Depends(get_db)]

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from fastapi import FastAPI, Depends
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ping
from app.schemas import PingCreate, PingRead


app = FastAPI(title="CyberDex API")
DbSession = Annotated[Session, Depends(get_db)]

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cyberdex-api"}


@app.post("/api/pings", response_model=PingRead, status_code=201)
def create_ping(payload: PingCreate, db: DbSession) -> Ping:
    ping = Ping(message=payload.message)
    db.add(ping)
    db.commit()
    db.refresh(ping)
    return ping



@app.get("/api/pings", response_model=list[PingRead])
def list_pings(db: DbSession) -> list[Ping]:
    stmt = select(Ping).order_by(Ping.created_at.desc()).limit(50)
    return list(db.scalars(stmt))
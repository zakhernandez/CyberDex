from fastapi import FastAPI

app = FastAPI(title="CyberDex API")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cyberdex-api"}
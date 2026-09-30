from fastapi import FastAPI

from app.routers.audit import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.milestones import router as milestones_router
from app.routers.projects import router as projects_router

app = FastAPI(title="ARS Project Finance API", version="5.1.0")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(expenses_router)
app.include_router(milestones_router)
app.include_router(audit_router)

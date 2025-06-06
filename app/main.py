from fastapi import FastAPI
from app.routes.explorer import router as explorer_router

app = FastAPI(title="Heritage Lens")

app.include_router(explorer_router, prefix="/api/explorer")
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.config import settings
from app.database import Base, engine


from app.routers import admin, auth, users, cars, rentals

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title=settings.app_name, version = "1.0.0", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name = "uploads")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(cars.router)
app.include_router(rentals.router)


@app.get("/health", tags = ["system"])
def health():
    return {"status": "ok"}

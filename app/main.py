from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db import Base, engine
import app.models  # noqa: F401
from app.routes import auth, dashboard, subjects

app = FastAPI(title="StudyFlow")

app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-this")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(subjects.router)

@app.get("/")
def root():
    return {"message": "StudyFlow is running"}
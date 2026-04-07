from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
import app.models  # noqa: F401

app = FastAPI(title="StudyFlow")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return {"message": "StudyFlow is running"}
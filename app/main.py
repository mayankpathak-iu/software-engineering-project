from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.db import Base, engine
import app.models  # noqa: F401
from app.routes import auth, dashboard, subjects, assignments, calendar, recommendations, planner, study_sessions

app = FastAPI(title="StudyFlow")

app.add_middleware(SessionMiddleware, secret_key="studyflow-dev-secret-key")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(subjects.router)
app.include_router(assignments.router)
app.include_router(calendar.router)
app.include_router(recommendations.router)
app.include_router(planner.router)
app.include_router(study_sessions.router)


@app.get("/")
def root(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)
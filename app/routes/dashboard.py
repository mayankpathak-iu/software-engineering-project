from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Assignment, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    assignments = (
        db.query(Assignment)
        .filter(Assignment.user_id == user_id)
        .all()
    )

    today = date.today()
    week_later = today + timedelta(days=7)

    overdue = []
    due_soon = []
    completed = []

    for assignment in assignments:
        try:
            assignment_date = date.fromisoformat(assignment.due_date)
        except ValueError:
            continue

        if assignment.status == "completed":
            completed.append(assignment)
        elif assignment_date < today:
            overdue.append(assignment)
        elif today <= assignment_date <= week_later:
            due_soon.append(assignment)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "overdue": overdue,
            "due_soon": due_soon,
            "completed": completed,
        },
    )
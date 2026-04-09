from collections import defaultdict
from datetime import datetime, date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Assignment, ClassEvent, Subject, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_day_name(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%A")
    except ValueError:
        return "Unknown"


def get_assignment_date(date_str: str):
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


@router.get("/recommendations")
def recommendations_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    assignments = (
        db.query(Assignment)
        .filter(Assignment.user_id == user_id, Assignment.status != "completed")
        .all()
    )

    class_events = (
        db.query(ClassEvent)
        .filter(ClassEvent.user_id == user_id)
        .all()
    )

    busy_by_day = defaultdict(int)
    for event in class_events:
        day_name = get_day_name(event.start_time)
        if day_name != "Unknown":
            busy_by_day[day_name] += 1

    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    light_days = sorted(weekdays, key=lambda d: busy_by_day.get(d, 0))

    today = date.today()

    pending_assignments = []
    for assignment in assignments:
        due = get_assignment_date(assignment.due_date)
        if due:
            days_left = (due - today).days
        else:
            days_left = None

        pending_assignments.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "subject": assignment.subject.name if assignment.subject else "Unknown",
                "priority": assignment.priority,
                "estimated_hours": assignment.estimated_hours or 0,
                "due_date": assignment.due_date,
                "days_left": days_left,
                "status": assignment.status,
            }
        )

    pending_assignments.sort(
        key=lambda a: (
            a["days_left"] if a["days_left"] is not None else 9999,
            {"high": 0, "medium": 1, "low": 2}.get(a["priority"], 3),
        )
    )

    recommendations = []

    if pending_assignments:
        top = pending_assignments[0]
        if top["days_left"] is not None:
            recommendations.append(
                f"Start with '{top['title']}' for {top['subject']}. It is due in {top['days_left']} day(s)."
            )
        else:
            recommendations.append(
                f"Start with '{top['title']}' for {top['subject']}. It appears to be your highest priority pending task."
            )

    total_pending_hours = sum(a["estimated_hours"] for a in pending_assignments)
    if total_pending_hours > 0:
        recommendations.append(
            f"You currently have about {total_pending_hours} estimated study hour(s) of pending work."
        )

    if light_days:
        recommendations.append(
            f"Your lighter class day(s) appear to be: {', '.join(light_days[:2])}. These may be good for focused study sessions."
        )

    urgent_items = [a for a in pending_assignments if a["days_left"] is not None and a["days_left"] <= 3]
    if urgent_items:
        urgent_titles = ", ".join(a["title"] for a in urgent_items[:3])
        recommendations.append(
            f"Urgent assignment(s) due within 3 days: {urgent_titles}."
        )

    if not recommendations:
        recommendations.append("No recommendations available yet. Add assignments and upload your class schedule first.")

    return templates.TemplateResponse(
        request,
        "recommendations.html",
        {
            "request": request,
            "user": user,
            "recommendations": recommendations,
            "pending_assignments": pending_assignments,
            "busy_by_day": dict(busy_by_day),
        },
    )
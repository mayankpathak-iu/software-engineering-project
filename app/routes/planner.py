from collections import defaultdict
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Assignment, ClassEvent, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_day_name_from_datetime_string(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%A")
    except ValueError:
        return "Unknown"


def parse_due_date(date_str: str):
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None


def get_daily_capacity(class_load: int) -> int:
    if class_load <= 1:
        return 4
    if class_load <= 3:
        return 2
    return 1


def get_deadline_score(days_left: int) -> int:
    if days_left <= 0:
        return 100
    if days_left == 1:
        return 90
    if days_left == 2:
        return 75
    if days_left == 3:
        return 60
    if days_left <= 5:
        return 40
    return 20


def get_priority_score(priority: str) -> int:
    return {"high": 30, "medium": 15, "low": 5}.get(priority, 0)


def get_pressure_score(hours_per_day_needed: float) -> int:
    if hours_per_day_needed > 6:
        return 40
    if hours_per_day_needed > 3:
        return 25
    if hours_per_day_needed > 1:
        return 10
    return 5


@router.get("/planner")
def planner_page(request: Request, db: Session = Depends(get_db)):
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
        day_name = get_day_name_from_datetime_string(event.start_time)
        if day_name != "Unknown":
            busy_by_day[day_name] += 1

    today = date.today()
    planning_days = [today + timedelta(days=i) for i in range(7)]

    day_plan = []
    for day in planning_days:
        day_name = day.strftime("%A")
        class_load = busy_by_day.get(day_name, 0)
        capacity = get_daily_capacity(class_load)

        day_plan.append(
            {
                "date": day.isoformat(),
                "day_name": day_name,
                "busy_score": class_load,
                "capacity": capacity,
                "used_hours": 0,
                "items": [],
            }
        )

    assignment_data = []
    warnings = []

    for assignment in assignments:
        due = parse_due_date(assignment.due_date)
        if not due:
            continue

        days_left = (due - today).days
        available_days = max(days_left + 1, 1)
        estimated_hours = assignment.estimated_hours or 1
        hours_per_day_needed = estimated_hours / available_days

        score = (
            get_deadline_score(days_left)
            + get_priority_score(assignment.priority)
            + get_pressure_score(hours_per_day_needed)
        )

        assignment_data.append(
            {
                "title": assignment.title,
                "subject": assignment.subject.name if assignment.subject else "Unknown",
                "priority": assignment.priority,
                "estimated_hours": estimated_hours,
                "remaining_hours": estimated_hours,
                "due_date": assignment.due_date,
                "due": due,
                "days_left": days_left,
                "hours_per_day_needed": round(hours_per_day_needed, 2),
                "priority_score": score,
            }
        )

    assignment_data.sort(
        key=lambda a: (-a["priority_score"], a["days_left"], -a["estimated_hours"])
    )

    for assignment in assignment_data:
        candidate_days = [
            day for day in day_plan
            if date.fromisoformat(day["date"]) <= assignment["due"]
        ]

        candidate_days.sort(
            key=lambda d: (
                d["busy_score"],
                d["used_hours"],
                d["date"],
            )
        )

        for day in candidate_days:
            if assignment["remaining_hours"] <= 0:
                break

            available_capacity = day["capacity"] - day["used_hours"]
            if available_capacity <= 0:
                continue

            allocated = min(assignment["remaining_hours"], available_capacity)

            day["items"].append(
                {
                    "title": assignment["title"],
                    "subject": assignment["subject"],
                    "hours": allocated,
                    "priority": assignment["priority"],
                    "due_date": assignment["due_date"],
                }
            )

            day["used_hours"] += allocated
            assignment["remaining_hours"] -= allocated

        if assignment["remaining_hours"] > 0:
            warnings.append(
                f"Risk: '{assignment['title']}' still has {assignment['remaining_hours']} unscheduled hour(s) before its due date ({assignment['due_date']})."
            )

    return templates.TemplateResponse(
        request,
        "planner.html",
        {
            "request": request,
            "user": user,
            "day_plan": day_plan,
            "assignment_data": assignment_data,
            "warnings": warnings,
        },
    )
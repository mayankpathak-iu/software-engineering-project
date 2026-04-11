from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from icalendar import Calendar

from app.db import get_db
from app.models import ClassEvent, Subject , StudySession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def guess_code_and_name(title: str) -> tuple[str, str]:
    title = title.strip()

    if " - " in title:
        left, right = title.split(" - ", 1)
        return left.strip(), right.strip()

    return "", title


@router.get("/calendar")
def calendar_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    events = (
        db.query(ClassEvent)
        .filter(ClassEvent.user_id == user_id)
        .order_by(ClassEvent.start_time.asc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "calendar.html",
        {
            "request": request,
            "events": events,
            "error": None,
        },
    )


@router.post("/calendar/upload")
async def upload_calendar(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    if not file.filename.endswith(".ics"):
        events = (
            db.query(ClassEvent)
            .filter(ClassEvent.user_id == user_id)
            .order_by(ClassEvent.start_time.asc())
            .all()
        )
        return templates.TemplateResponse(
            request,
            "calendar.html",
            {
                "request": request,
                "events": events,
                "error": "Please upload a valid .ics file.",
            },
        )

    content = await file.read()

    try:
        calendar = Calendar.from_ical(content)

        db.query(ClassEvent).filter(ClassEvent.user_id == user_id).delete()

        for component in calendar.walk():
            if component.name == "VEVENT":
                summary = str(component.get("summary", "Untitled Event"))

                dtstart = component.get("dtstart")
                dtend = component.get("dtend")

                start_value = dtstart.dt if dtstart else None
                end_value = dtend.dt if dtend else None

                if isinstance(start_value, datetime):
                    start_str = start_value.strftime("%Y-%m-%d %H:%M")
                else:
                    start_str = str(start_value) if start_value else ""

                if isinstance(end_value, datetime):
                    end_str = end_value.strftime("%Y-%m-%d %H:%M")
                else:
                    end_str = str(end_value) if end_value else ""

                event = ClassEvent(
                    user_id=user_id,
                    title=summary,
                    start_time=start_str,
                    end_time=end_str,
                )
                db.add(event)

        db.commit()

        return RedirectResponse(url="/calendar", status_code=303)

    except Exception:
        events = (
            db.query(ClassEvent)
            .filter(ClassEvent.user_id == user_id)
            .order_by(ClassEvent.start_time.asc())
            .all()
        )
        return templates.TemplateResponse(
            request,
            "calendar.html",
            {
                "request": request,
                "events": events,
                "error": "Could not parse the uploaded calendar file.",
            },
        )


@router.post("/calendar/clear")
def clear_calendar(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    db.query(ClassEvent).filter(ClassEvent.user_id == user_id).delete()
    db.commit()

    return RedirectResponse(url="/calendar", status_code=303)


@router.get("/calendar/import-subjects")
def import_subjects_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    events = db.query(ClassEvent).filter(ClassEvent.user_id == user_id).all()

    seen_titles = set()
    candidates = []

    for event in events:
        raw_title = event.title.strip()
        if not raw_title or raw_title.lower() in seen_titles:
            continue

        seen_titles.add(raw_title.lower())

        code, name = guess_code_and_name(raw_title)

        candidates.append(
            {
                "raw_title": raw_title,
                "suggested_code": code,
                "suggested_name": name,
            }
        )

    return templates.TemplateResponse(
        request,
        "import_subjects.html",
        {
            "request": request,
            "candidates": candidates,
        },
    )


@router.post("/calendar/import-subjects")
async def import_subjects_submit(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    form = await request.form()

    selected_titles = form.getlist("selected_titles")

    existing_subjects = db.query(Subject).filter(Subject.user_id == user_id).all()
    existing_pairs = {
        ((s.code or "").strip().lower(), (s.name or "").strip().lower())
        for s in existing_subjects
    }

    for raw_title in selected_titles:
        code = str(form.get(f"code::{raw_title}", "")).strip()
        name = str(form.get(f"name::{raw_title}", "")).strip()

        if not name:
            continue

        pair = (code.lower(), name.lower())

        if pair not in existing_pairs:
            db.add(
                Subject(
                    user_id=user_id,
                    code=code,
                    name=name,
                    color="#3b82f6",
                )
            )
            existing_pairs.add(pair)

    db.commit()
    return RedirectResponse(url="/subjects", status_code=303)

@router.get("/calendar-view")
def calendar_view_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "calendar_view.html",
        {
            "request": request,
        },
    )

@router.get("/calendar-events")
def calendar_events(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    events = (
        db.query(ClassEvent)
        .filter(ClassEvent.user_id == user_id)
        .all()
    )

    study_sessions = (
        db.query(StudySession)
        .filter(StudySession.user_id == user_id)
        .all()
    )

    calendar_items = []

    for event in events:
        start_value = event.start_time.replace(" ", "T")
        end_value = event.end_time.replace(" ", "T")

        calendar_items.append(
            {
                "title": event.title,
                "start": start_value,
                "end": end_value,
                "color": "#2563eb",
                "extendedProps": {
                    "type": "class_event",
                },
            }
        )

    for session in study_sessions:
        start_value = f"{session.session_date}T{session.start_time}:00"
        end_value = f"{session.session_date}T{session.end_time}:00"

        calendar_items.append(
            {
                "title": session.title,
                "start": start_value,
                "end": end_value,
                "color": "#16a34a",
                "extendedProps": {
                    "type": "study_session",
                    "session_id": session.id,
                },
            }
        )

    return JSONResponse(calendar_items)
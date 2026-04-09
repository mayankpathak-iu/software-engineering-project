from datetime import datetime

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from icalendar import Calendar

from app.db import get_db
from app.models import ClassEvent

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
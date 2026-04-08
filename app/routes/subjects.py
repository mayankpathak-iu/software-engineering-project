from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Subject

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/subjects")
def list_subjects(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    subjects = (
        db.query(Subject)
        .filter(Subject.user_id == user_id)
        .order_by(Subject.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "subjects.html",
        {"request": request, "subjects": subjects},
    )


@router.post("/subjects")
def create_subject(
    request: Request,
    name: str = Form(...),
    code: str = Form(""),
    color: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    subject = Subject(
        user_id=user_id,
        name=name,
        code=code,
        color=color,
    )
    db.add(subject)
    db.commit()

    return RedirectResponse(url="/subjects", status_code=303)


@router.post("/subjects/{subject_id}/delete")
def delete_subject(subject_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.user_id == user_id)
        .first()
    )

    if subject:
        db.delete(subject)
        db.commit()

    return RedirectResponse(url="/subjects", status_code=303)
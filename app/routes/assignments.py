from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Assignment, Subject

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/assignments")
def list_assignments(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    assignments = (
        db.query(Assignment)
        .filter(Assignment.user_id == user_id)
        .order_by(Assignment.created_at.desc())
        .all()
    )

    subjects = (
        db.query(Subject)
        .filter(Subject.user_id == user_id)
        .order_by(Subject.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "assignments.html",
        {
            "request": request,
            "assignments": assignments,
            "subjects": subjects,
        },
    )


@router.post("/assignments")
def create_assignment(
    request: Request,
    subject_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    due_date: str = Form(...),
    priority: str = Form(...),
    status: str = Form(...),
    estimated_hours: int = Form(...),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.user_id == user_id)
        .first()
    )

    if not subject:
        return RedirectResponse(url="/assignments", status_code=303)

    assignment = Assignment(
        user_id=user_id,
        subject_id=subject_id,
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        status=status,
        estimated_hours=estimated_hours,
    )
    db.add(assignment)
    db.commit()

    return RedirectResponse(url="/assignments", status_code=303)


@router.get("/assignments/{assignment_id}/edit")
def edit_assignment_page(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.user_id == user_id)
        .first()
    )

    if not assignment:
        return RedirectResponse(url="/assignments", status_code=303)

    subjects = (
        db.query(Subject)
        .filter(Subject.user_id == user_id)
        .order_by(Subject.name.asc())
        .all()
    )

    return templates.TemplateResponse(
        request,
        "edit_assignment.html",
        {
            "request": request,
            "assignment": assignment,
            "subjects": subjects,
        },
    )


@router.post("/assignments/{assignment_id}/edit")
def update_assignment(
    assignment_id: int,
    request: Request,
    subject_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    due_date: str = Form(...),
    priority: str = Form(...),
    status: str = Form(...),
    estimated_hours: int = Form(...),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.user_id == user_id)
        .first()
    )

    if not assignment:
        return RedirectResponse(url="/assignments", status_code=303)

    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.user_id == user_id)
        .first()
    )

    if not subject:
        return RedirectResponse(url="/assignments", status_code=303)

    assignment.subject_id = subject_id
    assignment.title = title
    assignment.description = description
    assignment.due_date = due_date
    assignment.priority = priority
    assignment.status = status
    assignment.estimated_hours = estimated_hours

    db.commit()

    return RedirectResponse(url="/assignments", status_code=303)


@router.post("/assignments/{assignment_id}/delete")
def delete_assignment(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.user_id == user_id)
        .first()
    )

    if assignment:
        db.delete(assignment)
        db.commit()

    return RedirectResponse(url="/assignments", status_code=303)
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    print("DASHBOARD SESSION:", dict(request.session))
    print("DASHBOARD USER ID:", user_id)

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    print("DASHBOARD USER:", user)

    if not user:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, "user": user},
    )
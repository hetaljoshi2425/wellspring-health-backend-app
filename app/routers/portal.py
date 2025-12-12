from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def portal_login(request: Request):
    return templates.TemplateResponse("portal_login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def portal_dashboard(request: Request):
    return templates.TemplateResponse("portal_dashboard.html", {"request": request})

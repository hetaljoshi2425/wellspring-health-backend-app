import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import (
    clients,
    appointments,
    notes,
    billing,
    telehealth,
    prescribing,
    icd10,
    insurance,
    family_contacts,
    staff_assignments,
    documents,
    reminders,
    assessments,
    admin,
    ai_tools,
    portal,
    reports,
    ui_spec,
    users,
    dashabord
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wellspring AI EHR Prototype")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,
    allow_methods=["*"],            
    allow_headers=["*"],            
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Routers
app.include_router(users.router, prefix="/user", tags=["user"])
app.include_router(dashabord.router, prefix="/dashabord", tags=["dashabord"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(telehealth.router, prefix="/telehealth", tags=["telehealth"])
app.include_router(prescribing.router, prefix="/prescribing", tags=["prescribing"])
app.include_router(icd10.router, prefix="/icd10", tags=["icd10"])
app.include_router(insurance.router, prefix="/insurance", tags=["insurance"])
app.include_router(family_contacts.router, prefix="/family-contacts", tags=["family_contacts"])
app.include_router(staff_assignments.router, prefix="/staff-assignments", tags=["staff_assignments"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
app.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(ai_tools.router, prefix="/ai", tags=["ai"])
app.include_router(portal.router, prefix="/portal", tags=["portal"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(ui_spec.router, prefix="/config", tags=["config"])

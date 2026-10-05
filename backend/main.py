from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.db import (
    init_db,
    get_applications,
    get_application,
    get_policies
)

from backend.agent import analyze_application


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="CortexOps",
    description=(
        "Autonomous Credit Operations Network"
    ),
    version="0.1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_PATH = (
    BASE_DIR /
    "frontend" /
    "index.html"
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    init_db()


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "system": "CortexOps",
        "version": "0.1.0"
    }


# ============================================================
# APPLICATIONS
# ============================================================

@app.get("/api/applications")
def applications():

    return {
        "count": len(get_applications()),
        "applications": get_applications()
    }


# ============================================================
# SINGLE APPLICATION
# ============================================================

@app.get("/api/applications/{application_id}")
def application(application_id: int):

    result = get_application(application_id)

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    return result


# ============================================================
# POLICIES
# ============================================================

@app.get("/api/policies")
def policies():

    return {
        "policies": get_policies()
    }


# ============================================================
# AI CREDIT ANALYSIS
# ============================================================

@app.post("/api/applications/{application_id}/analyze")
def analyze(application_id: int):

    application = get_application(
        application_id
    )

    if application is None:

        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    result = analyze_application(
        application
    )

    return result


# ============================================================
# FRONTEND
# ============================================================

@app.get("/")
def frontend():

    if not FRONTEND_PATH.exists():

        return {
            "message": "CortexOps backend is online",
            "frontend": "not created yet"
        }

    return FileResponse(
        FRONTEND_PATH
    )
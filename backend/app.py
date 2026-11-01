"""
RailSamiksha AI — Unified Full-Stack Backend Server
===================================================
Connects:
  - SAHI + RT-DETR-L AI Inference Engine (PyTorch / CUDA)
  - Indian Railways TMS Relational SQL Database (SQLite / PostgreSQL)
  - Role-Based Access Control (RBAC) Authentication
  - Central TMS CSV Reports & Audit Ledger
  - Static Web Frontend Serving with Full CORS Support
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Dict, Any

from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response, FileResponse
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db_manager import (
    verify_user_login,
    create_user,
    list_all_surveys,
    mark_defect_cleared,
    generate_and_save_survey_csv,
    get_database_stats,
    get_connection,
    DB_PATH,
    SCHEMA_PATH
)
from backend.inference import get_detector, MODEL_REGISTRY

WEB_DIR = ROOT_DIR / "RailSamiksha_Web"

# ============================================================================
# API HANDLERS
# ============================================================================

async def api_status(request):
    """Health check, hardware telemetry, active model, and SQL database stats."""
    import torch
    detector = get_detector()
    stats = get_database_stats()
    return JSONResponse({
        "status": "healthy",
        "app_name": "RailSamiksha AI",
        "version": "2.1.0-production",
        "hardware": {
            "device": detector.device,
            "cuda_available": torch.cuda.is_available(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Host CPU"
        },
        "model": {
            "architecture": "RT-DETR-L (Real-Time Transformer) + SAHI Patch Slicing",
            "active_weights": detector.weights_path.name,
            "available_weights": [
                {"id": "sanitized_85", "name": "RT-DETR-L Sanitized (55.3% Sleeper Precision - 85 Epochs)"},
                {"id": "canonical_85", "name": "RT-DETR-L Canonical (High Sensitivity - 85 Epochs)"},
                {"id": "deployed_prod", "name": "RT-DETR-L Production Deployed (53.75% mAP50 Baseline)"}
            ],
            "class_count": len(detector.names),
            "classes": detector.names
        },
        "database": {
            "engine": "SQLite 3 (Indian Railways TMS Relational Schema)",
            "tables": stats
        }
    })

async def api_auth_login(request):
    """Authenticates credentials against the SQL database."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Invalid JSON body"}, status_code=400)

    identifier = body.get("identifier", "").strip()
    password = body.get("password", "")

    if not identifier or not password:
        return JSONResponse({"success": False, "error": "Email/username and password required"}, status_code=400)

    user, error = verify_user_login(identifier, password)
    if user:
        return JSONResponse({"success": True, "user": user})
    return JSONResponse({"success": False, "error": error or "Invalid credentials"}, status_code=401)

async def api_auth_register(request):
    """Registers a new user in the SQL users table."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Invalid JSON body"}, status_code=400)

    username = body.get("username", "").strip()
    email = body.get("email", "").strip()
    password = body.get("password", "")
    full_name = body.get("full_name", "").strip()
    role = body.get("role", "operator")
    division = body.get("division", "").strip()
    employee_id = body.get("employee_id")

    if not all([username, email, password, full_name, division]):
        return JSONResponse({"success": False, "error": "All required fields must be supplied"}, status_code=400)

    user_id, error = create_user(username, email, password, full_name, role, division, employee_id)
    if user_id:
        user, _ = verify_user_login(username, password)
        return JSONResponse({"success": True, "user": user})
    return JSONResponse({"success": False, "error": error}, status_code=400)

async def api_get_surveys(request):
    """Retrieves all flight surveys and real-time defect punch-lists."""
    surveys = list_all_surveys()
    return JSONResponse({"surveys": surveys})

async def api_submit_survey(request):
    """Marks survey as submitted for clearance in the TMS ledger."""
    try:
        body = await request.json()
        survey_id = body.get("survey_id", "SURV-2026-LIVE")
    except Exception:
        survey_id = "SURV-2026-LIVE"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE surveys
            SET status = 'SUBMITTED_FOR_CLEARANCE',
                status_label = 'Pending Clearance',
                status_badge_class = 'badge-purple'
            WHERE id = ?
        """, (survey_id,))
        conn.commit()
        return JSONResponse({"success": True, "survey_id": survey_id, "status": "SUBMITTED_FOR_CLEARANCE"})
    finally:
        conn.close()

async def api_clear_defect(request):
    """Updates defect clearance status with field gang repair proof."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Invalid JSON"}, status_code=400)

    defect_id = body.get("defect_id")
    gang_name = body.get("gang_name", "Gang 12 (P-Way Agra)")
    je_name = body.get("je_name", "M. Kumar (JE P-Way)")
    action_taken = body.get("action_taken", "IRPWM standard repair applied")

    if not defect_id:
        return JSONResponse({"success": False, "error": "Missing defect_id"}, status_code=400)

    ok, err = mark_defect_cleared(defect_id, gang_name, je_name, action_taken)
    if ok:
        return JSONResponse({"success": True, "defect_id": defect_id, "cleared": True})
    return JSONResponse({"success": False, "error": err}, status_code=400)

async def api_infer_image(request):
    """
    Real-Time SAHI + RT-DETR-L Drone Photo Inference Endpoint.
    Uses exact RailSamiksha_Production_App pipeline.
    Accepts:
      - multipart/form-data with file upload ('file' or 'image')
      - or JSON with base64 image ('image_base64')
      - or 'sample_name' (e.g. 'sample_track_image.jpg')
      - optional 'model' ('deployed_prod', 'sanitized_85', 'canonical_85')
      - optional 'confidence' (default 0.20)
      - optional 'use_sahi' (default true)
    """
    image_bytes = None
    conf_threshold = 0.20
    model_choice = "deployed_prod"
    use_sahi = True

    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file") or form.get("image")
        conf_str = form.get("confidence", "0.20")
        model_choice = form.get("model", "deployed_prod")
        sample_name = form.get("sample_name", "")
        use_sahi_str = form.get("use_sahi", "true")
        use_sahi = str(use_sahi_str).lower() != "false"

        try:
            conf_threshold = float(conf_str)
        except ValueError:
            conf_threshold = 0.20

        if uploaded_file and hasattr(uploaded_file, "read"):
            image_bytes = await uploaded_file.read()
        elif sample_name:
            sample_p = PROD_APP_DIR / "samples" / sample_name
            if sample_p.exists():
                with open(sample_p, "rb") as f:
                    image_bytes = f.read()

    elif "application/json" in content_type:
        try:
            body = await request.json()
            raw_b64 = body.get("image_base64", "")
            conf_threshold = float(body.get("confidence", 0.20))
            model_choice = body.get("model", "deployed_prod")
            sample_name = body.get("sample_name", "")
            use_sahi = bool(body.get("use_sahi", True))

            if sample_name:
                sample_p = PROD_APP_DIR / "samples" / sample_name
                if sample_p.exists():
                    with open(sample_p, "rb") as f:
                        image_bytes = f.read()
            elif raw_b64:
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",")[1]
                image_bytes = base64.b64decode(raw_b64)
        except Exception as e:
            return JSONResponse({"success": False, "error": f"Invalid request body: {str(e)}"}, status_code=400)

    # Fallback to default sample track image if no bytes provided
    if not image_bytes:
        default_sample = PROD_APP_DIR / "samples" / "sample_track_image.jpg"
        if default_sample.exists():
            with open(default_sample, "rb") as f:
                image_bytes = f.read()

    try:
        detector = get_detector()
        if model_choice and model_choice in MODEL_REGISTRY:
            detector.set_model(model_choice)

        result = detector.predict_image(image_bytes, conf_threshold=conf_threshold, use_sahi=use_sahi)
        return JSONResponse(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"success": False, "error": f"Inference error: {str(e)}"}, status_code=500)
        import traceback
        traceback.print_exc()
        return JSONResponse({"success": False, "error": f"Inference error: {str(e)}"}, status_code=500)

async def api_get_csv_report(request):
    """Generates and returns an Indian Railways TMS-compliant CSV file."""
    survey_id = request.query_params.get("survey_id", "SURV-2026-LIVE")
    rep, err = generate_and_save_survey_csv(survey_id)
    if err:
        return JSONResponse({"error": err}, status_code=404)

    return Response(
        content=rep["csv_content"],
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=\"{rep['file_name']}\"",
            "X-SHA256-Checksum": rep["sha256"],
            "X-Record-Count": str(rep["total_records"])
        }
    )

async def api_list_csv_reports(request):
    """Lists all stored CSV reports from the database."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, survey_id, report_type, file_name, file_size_bytes, sha256_checksum, total_records, generated_at
            FROM survey_csv_reports
            ORDER BY generated_at DESC
        """)
        reports = [dict(r) for r in cur.fetchall()]
        return JSONResponse({"reports": reports})
    finally:
        conn.close()

async def api_export_schema(request):
    """Downloads schema.sql."""
    if SCHEMA_PATH.exists():
        return FileResponse(
            path=str(SCHEMA_PATH),
            media_type="text/plain",
            filename="railsamiksha_schema.sql"
        )
    return JSONResponse({"error": "schema.sql not found"}, status_code=404)

# ============================================================================
# APPLICATION INITIALIZATION & ROUTING
# ============================================================================

routes = [
    # Core Health & System Telemetry
    Route("/api/status", api_status, methods=["GET"]),
    
    # User Authentication & RBAC
    Route("/api/auth/login", api_auth_login, methods=["POST"]),
    Route("/api/auth/register", api_auth_register, methods=["POST"]),
    
    # Surveys & Master Ledger
    Route("/api/surveys", api_get_surveys, methods=["GET"]),
    Route("/api/surveys/submit", api_submit_survey, methods=["POST"]),
    
    # Defect Clearance & Remediation
    Route("/api/defects/clear", api_clear_defect, methods=["POST"]),
    
    # AI RT-DETR-L Real-Time Inference (with SAHI)
    Route("/api/infer/image", api_infer_image, methods=["POST"]),
    
    # TMS CSV Reports
    Route("/api/reports/csv", api_get_csv_report, methods=["GET"]),
    Route("/api/reports/list", api_list_csv_reports, methods=["GET"]),
    
    # SQL DDL Export
    Route("/api/db/export-schema", api_export_schema, methods=["GET"]),
]

# Mount static frontend files if directory exists
if WEB_DIR.exists():
    routes.append(Mount("/", app=StaticFiles(directory=str(WEB_DIR), html=True), name="static"))

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "X-SHA256-Checksum", "X-Record-Count"]
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware)

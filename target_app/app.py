
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
import json

app = FastAPI(title="Benign Traffic Target Application")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "evidence" / "application_events.jsonl"

VALID_PAGES = {
    "home",
    "about",
    "services",
    "contact"
}

USERS = {
    101: {"user_id": 101, "name": "Ahmed"},
    102: {"user_id": 102, "name": "Mohamed"},
    103: {"user_id": 103, "name": "Ali"}
}

# Maps each session to its authenticated user.
SESSION_USERS = {}


def log_application_event(request, event_type, details=None):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "event_id": str(uuid4()),
        "experiment_id": request.headers.get("X-Experiment-ID"),
        "run_id": request.headers.get("X-Run-ID"),
        "scenario_id": request.headers.get("X-Scenario-ID"),
        "action_id": request.headers.get("X-Action-ID"),
        "session_id": request.state.session_id,
        "simulation_mode": request.headers.get("X-Simulation-Mode"),
        "intent": request.headers.get("X-Intent"),
        "method": request.method,
        "endpoint": request.url.path,
        "query_params": dict(request.query_params),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {}
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


@app.middleware("http")
async def manage_session(request: Request, call_next):
    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = str(uuid4())

    request.state.session_id = session_id

    # Assign a user to this session if it is new.
    SESSION_USERS.setdefault(session_id, 101)

    response = await call_next(request)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax"
    )

    return response


@app.get("/index.php")
async def navigate_page(request: Request, page: str):
    if page not in VALID_PAGES:
        log_application_event(
            request,
            "invalid_page_requested",
            {"page": page}
        )

        return JSONResponse(
            status_code=404,
            content={"error": "Page not found"}
        )

    log_application_event(
        request,
        "page_viewed",
        {"page": page}
    )

    return {
        "message": "Page loaded successfully",
        "page": page
    }


@app.get("/api/v1/users/me")
async def get_current_user(request: Request):
    session_id = request.state.session_id
    user_id = SESSION_USERS[session_id]

    user = USERS[user_id]

    log_application_event(
        request,
        "current_user_retrieved",
        {"user_id": user_id}
    )

    return user


@app.get("/api/v1/profile")
async def get_profile(request: Request, user_id: int):
    session_id = request.state.session_id
    current_user_id = SESSION_USERS[session_id]

    # Benign prototype: only allow access to the current user's profile.
    if user_id != current_user_id:
        log_application_event(
            request,
            "profile_access_denied",
            {
                "requested_user_id": user_id,
                "current_user_id": current_user_id
            }
        )

        return JSONResponse(
            status_code=403,
            content={"error": "Access denied"}
        )

    user = USERS.get(user_id)

    if user is None:
        log_application_event(
            request,
            "profile_not_found",
            {"user_id": user_id}
        )

        return JSONResponse(
            status_code=404,
            content={"error": "User not found"}
        )

    log_application_event(
        request,
        "profile_viewed",
        {"user_id": user_id}
    )

    return {"profile": user}

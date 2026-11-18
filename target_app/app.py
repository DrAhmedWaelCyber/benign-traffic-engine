
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
import json

app = FastAPI(title="Benign Traffic Target Application")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "evidence" / "application_events.jsonl"

PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 25000},
    {"id": 2, "name": "Keyboard", "price": 1200},
    {"id": 3, "name": "Mouse", "price": 600},
]

CARTS = {}


def log_application_event(request, event_type, details=None):
    event = {
        "event_id": str(uuid4()),
        "experiment_id": request.headers.get("X-Experiment-ID"),
        "run_id": request.headers.get("X-Run-ID"),
        "session_id": request.state.session_id,
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

    response = await call_next(request)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax"
    )

    return response


@app.get("/")
async def homepage(request: Request):
    log_application_event(request, "homepage_visited")

    return {
        "message": "Welcome to our store",
        "session_id": request.state.session_id
    }


@app.get("/products")
async def get_products(request: Request):
    log_application_event(
        request,
        "products_list_viewed",
        {"products_count": len(PRODUCTS)}
    )

    return {"products": PRODUCTS}


@app.get("/products/{product_id}")
async def get_product(product_id: int, request: Request):
    product = next(
        (p for p in PRODUCTS if p["id"] == product_id),
        None
    )

    if product is None:
        log_application_event(
            request,
            "product_not_found",
            {"product_id": product_id}
        )

        return JSONResponse(
            status_code=404,
            content={"error": "Product not found"}
        )

    log_application_event(
        request,
        "product_viewed",
        {"product_id": product_id}
    )

    return {"product": product}


@app.post("/cart")
async def add_to_cart(request: Request, product_id: int):
    session_id = request.state.session_id

    product = next(
        (p for p in PRODUCTS if p["id"] == product_id),
        None
    )

    if product is None:
        log_application_event(
            request,
            "cart_add_failed",
            {"product_id": product_id}
        )

        return JSONResponse(
            status_code=404,
            content={"error": "Product not found"}
        )

    CARTS.setdefault(session_id, []).append(product)

    log_application_event(
        request,
        "product_added_to_cart",
        {"product_id": product_id}
    )

    return {
        "message": "Product added to cart",
        "cart": CARTS[session_id]
    }


@app.get("/cart")
async def get_cart(request: Request):
    session_id = request.state.session_id
    cart = CARTS.get(session_id, [])

    log_application_event(
        request,
        "cart_viewed",
        {
            "items_count": len(cart),
            "product_ids": [item["id"] for item in cart]
        }
    )

    return {
        "session_id": session_id,
        "cart": cart
    }

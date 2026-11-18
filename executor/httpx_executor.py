
import httpx
import json
import time

from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_FILE = PROJECT_ROOT / "evidence" / "executor_events.jsonl"

experiment_id = str(uuid4())
run_id = str(uuid4())


def write_event(event):
    with EVIDENCE_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


def execute_request(client, step, method, endpoint, **kwargs):
    start_time = time.perf_counter()

    response = client.request(
        method,
        endpoint,
        **kwargs
    )

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    event = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "session_id": client.cookies.get("session_id"),
        "step": step,
        "method": method,
        "endpoint": endpoint,
        "status_code": response.status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms
    }

    write_event(event)

    print(f"{step}: {response.status_code}")

    return response


def execute_scenario():
    print("Starting Benign Traffic Scenario")

    with httpx.Client(
    base_url=BASE_URL,
    timeout=10.0,
    headers={
        "X-Experiment-ID": experiment_id,
        "X-Run-ID": run_id
    }
    ) as client:

        execute_request(
            client, "homepage", "GET", "/"
        )

        time.sleep(1)

        execute_request(
            client, "products", "GET", "/products"
        )

        time.sleep(2)

        execute_request(
            client, "product_details", "GET", "/products/1"
        )

        time.sleep(1)

        execute_request(
            client, "add_to_cart", "POST", "/cart",
            params={"product_id": 1}
        )

        time.sleep(1)

        cart_response = execute_request(
            client, "view_cart", "GET", "/cart"
        )

        print("Cart content:", cart_response.json())

    print(f"Evidence saved to: {EVIDENCE_FILE}")
    print("Scenario completed")


if __name__ == "__main__":
    execute_scenario()


import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXECUTOR_FILE = PROJECT_ROOT / "evidence" / "executor_events.jsonl"
APPLICATION_FILE = PROJECT_ROOT / "evidence" / "application_events.jsonl"

EXPECTED_STEPS = [
    "homepage",
    "products",
    "product_details",
    "add_to_cart",
    "view_cart"
]

EXPECTED_EVENTS = [
    "homepage_visited",
    "products_list_viewed",
    "product_viewed",
    "product_added_to_cart",
    "cart_viewed"
]


def load_jsonl(file_path):
    if not file_path.exists():
        return None

    records = []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    raise ValueError(
                        f"Invalid JSON at line {line_number}"
                    )

    except OSError as error:
        raise RuntimeError(
            f"Cannot read {file_path.name}: {error}"
        )

    return records


def get_run_identity(event):
    return (
        event.get("experiment_id"),
        event.get("run_id"),
        event.get("session_id")
    )


def select_latest_run(executor_events, application_events):
    if not executor_events:
        return None, None

    latest = executor_events[-1]
    run_key = get_run_identity(latest)

    if any(value is None for value in run_key):
        return None, None

    selected_executor = [
        event for event in executor_events
        if get_run_identity(event) == run_key
    ]

    selected_application = [
        event for event in application_events
        if get_run_identity(event) == run_key
    ]

    return selected_executor, selected_application


def validate_run(executor_events, application_events):

    if executor_events is None or application_events is None:
        return "INCONCLUSIVE", ["Evidence file missing"]

    if not executor_events or not application_events:
        return "INCONCLUSIVE", ["Evidence is empty"]

    executor_ids = {
        get_run_identity(event)
        for event in executor_events
    }

    application_ids = {
        get_run_identity(event)
        for event in application_events
    }

    if len(executor_ids) != 1 or len(application_ids) != 1:
        return "INCONCLUSIVE", ["Multiple or missing run identities"]

    if executor_ids != application_ids:
        return "INCONCLUSIVE", ["Run identity mismatch"]

    identity = next(iter(executor_ids))

    if any(value is None for value in identity):
        return "INCONCLUSIVE", ["Missing correlation identifiers"]

    steps = [
        event.get("step")
        for event in executor_events
    ]

    events = [
        event.get("event_type")
        for event in application_events
    ]

    if steps != EXPECTED_STEPS:
        return "FAIL", [
            "Executor steps do not match expected sequence"
        ]

    if events != EXPECTED_EVENTS:
        return "FAIL", [
            "Application events do not match expected sequence"
        ]

    if any(
        event.get("status_code") != 200
        for event in executor_events
    ):
        return "FAIL", [
            "One or more HTTP requests failed"
        ]

    cart_event = application_events[-1]
    details = cart_event.get("details", {})

    if details.get("items_count") != 1:
        return "FAIL", [
            "Expected exactly one cart item"
        ]

    if details.get("product_ids") != [1]:
        return "FAIL", [
            "Expected product ID 1 in cart"
        ]

    return "PASS", [
        "All expected behaviors verified"
    ]


def main():
    try:
        executor_events = load_jsonl(EXECUTOR_FILE)
        application_events = load_jsonl(APPLICATION_FILE)

        if executor_events is None or application_events is None:
            status = "INCONCLUSIVE"
            reasons = ["Evidence file missing"]
            selected_executor = []

        else:
            selected_executor, selected_application = select_latest_run(
                executor_events,
                application_events
            )

            if selected_executor is None:
                status = "INCONCLUSIVE"
                reasons = ["No valid run identity found"]

            else:
                status, reasons = validate_run(
                    selected_executor,
                    selected_application
                )

    except (ValueError, RuntimeError) as error:
        status = "INCONCLUSIVE"
        reasons = [str(error)]
        selected_executor = []

    print("\n=== BENIGN TRAFFIC VALIDATION ===")

    if selected_executor:
        print(
            f"Selected Run: "
            f"{selected_executor[0].get('run_id')}"
        )

        print(
            f"Executor Events: {len(selected_executor)}"
        )

        print(
            f"Application Events: {len(selected_application)}"
        )

    print(f"Status: {status}")

    for reason in reasons:
        print(f"- {reason}")


if __name__ == "__main__":
    main()

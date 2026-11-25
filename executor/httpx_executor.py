
import argparse
import httpx
import json
import time

from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCENARIO_FILE = PROJECT_ROOT / "scenarios" / "benign_scenarios.json"
EVIDENCE_FILE = PROJECT_ROOT / "evidence" / "executor_events.jsonl"

experiment_id = str(uuid4())
run_id = str(uuid4())


def load_scenario(scenario_id):
    with SCENARIO_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    scenarios = data.get("scenarios", [])

    if not scenarios:
        raise ValueError("No scenarios found in JSON file")

    for scenario in scenarios:
        if scenario.get("id") == scenario_id:
            if scenario.get("intent") != "benign":
                raise ValueError("Selected scenario is not benign")

            if not scenario.get("actions"):
                raise ValueError("Scenario has no actions")

            return scenario

    raise ValueError(f"Scenario not found: {scenario_id}")


def write_event(event):
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with EVIDENCE_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


def resolve_value(value, context):
    if isinstance(value, str) and value.startswith("$context."):
        key = value.removeprefix("$context.")

        if key not in context:
            raise ValueError(f"Context variable not found: {key}")

        return context[key]

    if isinstance(value, dict):
        return {
            key: resolve_value(item, context)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            resolve_value(item, context)
            for item in value
        ]

    return value


def extract_response_value(response, json_path):
    if not json_path.startswith("$."):
        raise ValueError(f"Unsupported JSON path: {json_path}")

    data = response.json()
    keys = json_path[2:].split(".")

    for key in keys:
        if not isinstance(data, dict) or key not in data:
            raise ValueError(
                f"Response field not found: {json_path}"
            )

        data = data[key]

    return data


def execute_request(
    client,
    scenario_id,
    action,
    session_id,
    context
):
    action_id = action["action_id"]
    method = action["method"].upper()
    endpoint = action["endpoint"]

    params = resolve_value(
        action.get("params") or {},
        context
    )

    payload = resolve_value(
        action.get("payload"),
        context
    )

    request_kwargs = {
        "params": params,
        "headers": {
            "X-Scenario-ID": scenario_id,
            "X-Action-ID": action_id,
            "X-Intent": action.get("intent", "unspecified")
        }
    }

    if payload is not None:
        if isinstance(payload, (dict, list)):
            request_kwargs["json"] = payload
        else:
            request_kwargs["content"] = str(payload)

    start_time = time.perf_counter()

    response = client.request(
        method,
        endpoint,
        **request_kwargs
    )

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    event = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "session_id": session_id,
        "scenario_id": scenario_id,
        "action_id": action_id,
        "method": method,
        "endpoint": endpoint,
        "params": params,
        "status_code": response.status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms
    }

    write_event(event)

    print(f"{action_id}: {response.status_code}")

    save_response = action.get("save_response")

    if save_response:
        for variable, json_path in save_response.items():
            context[variable] = extract_response_value(
                response,
                json_path
            )

            print(f"Saved context variable: {variable}")

    return response


def execute_scenario(scenario_id):
    scenario = load_scenario(scenario_id)

    scenario_id = scenario["id"]
    scenario_name = scenario["name"]
    actions = scenario["actions"]

    session_id = str(uuid4())
    context = {}

    print(f"Starting Scenario: {scenario_name}")
    print(f"Scenario ID: {scenario_id}")
    print(f"Session ID: {session_id}")

    with httpx.Client(
        base_url=BASE_URL,
        timeout=10.0,
        cookies={
            "session_id": session_id
        },
        headers={
            "X-Experiment-ID": experiment_id,
            "X-Run-ID": run_id,
            "X-Simulation-Mode": "secure"
        }
    ) as client:

        last_response = None

        for index, action in enumerate(actions):
            last_response = execute_request(
                client,
                scenario_id,
                action,
                session_id,
                context
            )

            if index < len(actions) - 1:
                time.sleep(1)

        if last_response is not None:
            print("Last response status:", last_response.status_code)

    print(f"Evidence saved to: {EVIDENCE_FILE}")
    print("Scenario completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benign Traffic Scenario Executor"
    )

    parser.add_argument(
        "scenario_id",
        help="ID of the scenario to execute"
    )

    args = parser.parse_args()

    try:
        execute_scenario(args.scenario_id)
    except (
        ValueError,
        OSError,
        json.JSONDecodeError,
        httpx.HTTPError
    ) as error:
        parser.error(str(error))

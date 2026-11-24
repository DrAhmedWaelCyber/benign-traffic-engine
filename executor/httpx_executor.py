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
    with EVIDENCE_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


def execute_request(client, scenario_id, action):
    action_id = action["action_id"]
    method = action["method"].upper()
    endpoint = action["endpoint"]

    request_kwargs = {
        "params": action.get("params") or {}
    }

    payload = action.get("payload")

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
        "session_id": client.cookies.get("session_id"),
        "scenario_id": scenario_id,
        "action_id": action_id,
        "method": method,
        "endpoint": endpoint,
        "status_code": response.status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms
    }

    write_event(event)

    print(f"{action_id}: {response.status_code}")

    return response


def execute_scenario(scenario_id):
    scenario = load_scenario(scenario_id)

    scenario_id = scenario["id"]
    scenario_name = scenario["name"]
    actions = scenario["actions"]

    print(f"Starting Scenario: {scenario_name}")
    print(f"Scenario ID: {scenario_id}")

    with httpx.Client(
        base_url=BASE_URL,
        timeout=10.0,
        headers={
            "X-Experiment-ID": experiment_id,
            "X-Run-ID": run_id
        }
    ) as client:

        last_response = None

        for index, action in enumerate(actions):
            last_response = execute_request(
                client,
                scenario_id,
                action
            )

            if index < len(actions) - 1:
                time.sleep(1)

        if last_response is not None:
            print("Last response status:", last_response.status_code)

            if actions[-1]["endpoint"] == "/cart":
                print("Cart content:", last_response.json())

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
    except (ValueError, OSError, json.JSONDecodeError) as error:
       parser.error(str(error))
# Testing Notes

I tested the current prototype locally using a separate Python virtual environment to make sure it can run without depending on my original development environment.

## Environment

- OS: macOS
- Python: 3.14.7
- Executor: HTTPX
- Application: FastAPI
- Evidence format: JSONL

I installed the required packages using:

```bash
pip install -r requirements.txt
```

Everything installed successfully.

## Running the Scenario

I started the local target application and ran the HTTPX executor.

The executor completed the following steps:

| Action | Status |
|---|---|
| Visit homepage | 200 |
| View products | 200 |
| View product details | 200 |
| Add product to cart | 200 |
| View cart | 200 |

The cart contained the expected product (Laptop, ID: 1).

## Evidence

After execution, the prototype generated two evidence files:

- `executor_events.jsonl`
- `application_events.jsonl`

Both files contained 5 events for the same run.

The events were linked using `experiment_id`, `run_id`, and `session_id`.

## Validation

I ran the validator after the scenario finished.

Result:

```text
Selected Run: 3da7e7ba-4f7c-4091-b76e-8f0aec6a972e
Executor Events: 5
Application Events: 5
Status: PASS
- All expected behaviors verified
```

The validator confirmed that the expected application events were recorded and that the cart contained the expected item.

## Additional Tests

I also tested a few failure cases manually:

- Removed an expected application event.
- Changed the cart result to an incorrect value.
- Changed an HTTP response status to 500.

The validator detected all three cases and returned FAIL.

## Current Result

The basic workflow is working as expected:

- Traffic generation.
- Evidence collection.
- Event correlation.
- Behavior validation.

This is still a local prototype. It has not been connected to the official Cyber Range infrastructure or the main platform backend yet.

Those integration details will be handled once the official interfaces and requirements are available.
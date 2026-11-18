# Benign Traffic Engine

A local prototype for generating realistic benign web application traffic, collecting execution and application evidence, and validating expected user behavior.

## Project Objective

The goal of this prototype is to explore a controlled and repeatable approach to benign traffic generation for the University Cyber Range and Dataset Research Platform.

The prototype focuses on:

- Generating normal user activity.
- Separating traffic execution from the target application.
- Collecting execution and application evidence.
- Correlating events using experiment, run, and session identifiers.
- Validating expected application behavior.

## Current Prototype Architecture

```text
HTTPX Executor
     |
     | HTTP Requests
     v
Local Target Application
     |
     +---- Executor Evidence
     |
     +---- Application Evidence
                  |
                  v
              Validator
                  |
                  v
          PASS / FAIL / INCONCLUSIVE
```

## Current Scenario

The prototype simulates a basic e-commerce user journey:

1. Visit homepage.
2. View products.
3. View product details.
4. Add a product to the cart.
5. View the cart.

## Project Structure

```text
benign-traffic-engine/
├── executor/
│   └── httpx_executor.py
├── target_app/
│   └── app.py
├── validator/
│   └── validator.py
├── evidence/
│   └── Generated JSONL evidence
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10+
- pip

## Installation

Clone the repository:

```bash
git clone <REPOSITORY_URL>
cd benign-traffic-engine
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Prototype

### 1. Start the Target Application

```bash
uvicorn target_app.app:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

### 2. Execute the Benign Scenario

Open another terminal, activate the virtual environment, and run:

```bash
python executor/httpx_executor.py
```

### 3. Validate the Evidence

After the scenario finishes:

```bash
python validator/validator.py
```

The validator checks the collected evidence and reports:

- PASS: Expected behavior was verified.
- FAIL: Evidence indicates an unexpected behavior.
- INCONCLUSIVE: Available evidence is insufficient or invalid.

## Evidence Collection

The prototype currently generates two evidence sources:

**Executor Evidence**

Records HTTP requests, response status codes, execution timestamps, and correlation identifiers.

**Application Evidence**

Records application-level events such as homepage visits, product views, and cart operations.

Both sources use:

- experiment_id
- run_id
- session_id

These identifiers help correlate execution activity with application behavior.

## Current Limitations

- The target application is a temporary local application.
- Cart data is stored in memory.
- Evidence is stored locally in JSONL files.
- The prototype does not yet integrate with the official Cyber Range platform.
- The final integration interfaces and execution contracts are still subject to team agreement.

## Project Status

**Prototype v0.1 — Local Proof of Concept**

This version demonstrates the basic traffic generation, evidence collection, event correlation, and behavioral validation workflow.

It is not a production-ready system.

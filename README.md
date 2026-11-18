# Benign Traffic Engine

A local prototype for generating normal user traffic and checking if the expected actions happened correctly.

The project is part of the University Cyber Range.

## Project Files

- `target_app/` – Local web application.
- `executor/` – Sends HTTP requests using HTTPX.
- `validator/` – Checks the generated evidence.
- `evidence/` – Stores JSONL files.

## Setup

```bash
git clone https://github.com/DrAhmedWaelCyber/benign-traffic-engine.git
cd benign-traffic-engine

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

Start the application:

```bash
uvicorn target_app.app:app --reload
```

Open another terminal and run:

```bash
source .venv/bin/activate
python executor/httpx_executor.py
```

After execution, run the validator:

```bash
python validator/validator.py
```

## Current Status

Version: `v0.1.0`

The local scenario performs five actions: homepage visit, products view, product view, add to cart, and view cart.

The prototype currently works locally. Official Cyber Range integration is not implemented yet.
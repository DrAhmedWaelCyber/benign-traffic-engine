# Benign Traffic Engine

A local prototype for generating normal user traffic and checking if the expected actions happened correctly

The project is part of the University Cyber Range

## Project Files

- `target_app/` – Local web application > DONE
- `executor/` – Sends HTTP requests using HTTPX > DONE 
- `validator/` – Checks the generated evidence > STILL BROOOOOO  
- `evidence/` – Stores JSONL files > DONE 

## Setup

```bash

python3 -m venv .venv
source .venv/bin/activate

```

## Run

Start the PythonApp:

```bash
uvicorn target_app.app:app --reload
```

run:

```bash
python executor/httpx_executor.py
```

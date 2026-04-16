# Backend (Python)

Basic chatbot API for the frontend pages.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Server runs on `http://127.0.0.1:5000`.

## Endpoints

- `GET /health`
- `POST /chat` with JSON body:

```json
{ "message": "your question" }
```

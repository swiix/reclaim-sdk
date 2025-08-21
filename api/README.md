# Reclaim Tasks REST API

Eine einfache REST API für die Verwaltung von Reclaim.ai Aufgaben.

## Features

- **GET /tasks** - Alle Aufgaben abrufen
- **GET /tasks/{task_id}** - Spezifische Aufgabe abrufen
- **GET /health** - Health Check
- **Automatische API-Dokumentation** - Verfügbar unter `/docs`

## Installation

1. **Dependencies installieren:**
```bash
pip install -r api_requirements.txt
```

2. **Reclaim API Token konfigurieren:**
```bash
export RECLAIM_TOKEN="dein_reclaim_api_token"
```

## Verwendung

### Server starten:
```bash
cd api
python main.py
```

Oder mit uvicorn direkt:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Alle Aufgaben abrufen
```bash
curl http://localhost:8000/tasks
```

#### Spezifische Aufgabe abrufen
```bash
curl http://localhost:8000/tasks/{task_id}
```

#### Health Check
```bash
curl http://localhost:8000/health
```

### API Dokumentation

Nach dem Start des Servers ist die interaktive API-Dokumentation verfügbar unter:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Response Format

### Task Response
```json
{
  "id": "task_id",
  "title": "Aufgabenname",
  "notes": "Beschreibung",
  "due": "2023-12-31T23:59:59Z",
  "priority": "P1",
  "duration": 2.5,
  "max_work_duration": 1.5,
  "min_work_duration": 0.5,
  "event_color": "BANANA",
  "up_next": true,
  "completed": false,
  "time_scheme_id": "scheme_id",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

## Fehlerbehandlung

Die API gibt entsprechende HTTP-Statuscodes zurück:

- **200** - Erfolgreich
- **401** - Authentifizierungsfehler
- **404** - Aufgabe nicht gefunden
- **500** - Server-Fehler

## CORS

Die API ist für Frontend-Integration konfiguriert und erlaubt CORS-Requests von allen Origins.

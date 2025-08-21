from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import sys

# Add the current directory to the path to import reclaim_sdk
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def format_duration_text(duration_hours: Optional[float]) -> Optional[str]:
    """Convert duration from hours to human-readable text format"""
    if duration_hours is None:
        return None
    
    if duration_hours == 0:
        return "0 min"
    
    # Convert to minutes
    total_minutes = int(duration_hours * 60)
    
    # Handle different time ranges
    if total_minutes < 60:
        return f"{total_minutes} min"
    elif total_minutes == 60:
        return "1h"
    elif total_minutes < 1440:  # Less than 24 hours
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {minutes}min"
    else:  # 24 hours or more
        days = total_minutes // 1440
        remaining_minutes = total_minutes % 1440
        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60
        
        if hours == 0 and minutes == 0:
            return f"{days}d"
        elif minutes == 0:
            return f"{days}d {hours}h"
        else:
            return f"{days}d {hours}h {minutes}min"

app = FastAPI(
    title="Reclaim Tasks API",
    description="REST API für Reclaim.ai Aufgabenverwaltung",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskResponse(BaseModel):
    id: str
    title: str
    notes: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    at_risk: Optional[bool] = None
    due: Optional[datetime] = None
    duration: Optional[float] = None
    duration_text: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "Reclaim Tasks API",
        "version": "1.0.0",
        "description": "REST API für Reclaim.ai Aufgabenverwaltung mit erweiterten Filtermöglichkeiten",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "root": {
                "path": "/",
                "method": "GET",
                "description": "API-Informationen und Dokumentation",
                "response": "JSON mit API-Details"
            },
            "health": {
                "path": "/health",
                "method": "GET", 
                "description": "Health Check für API-Status",
                "response": "JSON mit Status und Timestamp"
            },
            "all_tasks": {
                "path": "/tasks",
                "method": "GET",
                "description": "Alle Tasks aus Reclaim.ai abrufen",
                "response": "Array von Task-Objekten",
                "example_response": {
                    "id": "9453408",
                    "title": "Task Titel",
                    "notes": "Task Beschreibung",
                    "priority": "TaskPriority.P2",
                    "status": "TaskStatus.IN_PROGRESS",
                    "at_risk": False,
                    "due": "2025-01-15T10:00:00Z",
                    "duration": 2.5,
                    "duration_text": "2h 30min"
                }
            },
            "tasks_at_risk": {
                "path": "/tasks/at-risk",
                "method": "GET",
                "description": "Nur Tasks mit Risiko abrufen (at_risk = true), archivierte Tasks werden ausgeschlossen",
                "response": "JSON mit Anzahl, Array von Task-Objekten und Filter-Informationen",
                "filters": {
                    "at_risk": "true",
                    "exclude_archived": "true"
                },
                "example_response": {
                    "count": 45,
                    "tasks": [
                        {
                            "id": "9453408",
                            "title": "Risiko Task",
                            "notes": "Task mit Risiko",
                            "priority": "TaskPriority.P1",
                            "status": "TaskStatus.SCHEDULED",
                            "at_risk": True,
                            "due": "2025-01-10T10:00:00Z",
                            "duration": 2.0,
                            "duration_text": "2h"
                        }
                    ],
                    "filter_info": {
                        "excluded_archived": True,
                        "description": "Archivierte Tasks werden aus Risiko-Berechnung ausgeschlossen"
                    }
                }
            }
        },
        "task_properties": {
            "id": "Eindeutige Task-ID (String)",
            "title": "Titel der Aufgabe (String)",
            "notes": "Notizen/Beschreibung (String, optional)",
            "priority": "Priorität: P1, P2, P3, P4 (String)",
            "status": "Status: NEW, SCHEDULED, IN_PROGRESS, COMPLETE, CANCELLED, ARCHIVED (String)",
            "at_risk": "Risiko-Status (Boolean)",
            "due": "Fälligkeitsdatum (ISO 8601 String, optional)",
            "duration": "Geplante Dauer in Stunden (Float, optional)",
            "duration_text": "Benutzerfreundliche Dauer-Anzeige (String, optional)"
        },
        "authentication": {
            "method": "API Token",
            "environment_variable": "RECLAIM_TOKEN",
            "setup": "export RECLAIM_TOKEN='your_token_here'"
        },
        "usage_examples": {
            "get_all_tasks": "curl https://your-vercel-url.vercel.app/tasks",
            "get_risk_tasks": "curl https://your-vercel-url.vercel.app/tasks/at-risk",
            "health_check": "curl https://your-vercel-url.vercel.app/health"
        },
        "error_handling": {
            "401": "Authentication failed - Token ungültig",
            "500": "Internal server error - API oder Reclaim.ai Fehler"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/tasks")
async def get_tasks():
    """Get all tasks"""
    try:
        from reclaim_sdk.client import ReclaimClient
        from reclaim_sdk.resources.task import Task
        
        # Configure client with token from environment
        token = os.environ.get("RECLAIM_TOKEN")
        if not token:
            raise HTTPException(
                status_code=500,
                detail="RECLAIM_TOKEN environment variable is not set"
            )
        client = ReclaimClient.configure(token=token)
        
        # Get all tasks
        tasks = Task.list()
        
        # Convert to response format
        task_responses = []
        for task in tasks:
            task_responses.append(TaskResponse(
                id=str(task.id),
                title=task.title,
                notes=task.notes,
                priority=str(task.priority) if task.priority else None,
                status=str(task.status) if task.status else None,
                at_risk=task.at_risk,
                due=task.due,
                duration=task.duration,
                duration_text=format_duration_text(task.duration)
            ))
        
        return task_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/at-risk")
async def get_tasks_at_risk():
    """Get only tasks that are at risk, excluding archived tasks"""
    try:
        from reclaim_sdk.client import ReclaimClient
        from reclaim_sdk.resources.task import Task
        
        # Configure client with token from environment
        token = os.environ.get("RECLAIM_TOKEN")
        if not token:
            raise HTTPException(
                status_code=500,
                detail="RECLAIM_TOKEN environment variable is not set"
            )
        client = ReclaimClient.configure(token=token)
        
        # Get all tasks
        tasks = Task.list()
        
        # Filter tasks that are at risk AND not archived
        at_risk_tasks = [
            task for task in tasks 
            if task.at_risk and str(task.status) != "TaskStatus.ARCHIVED"
        ]
        
        # Convert to response format
        task_responses = []
        for task in at_risk_tasks:
            task_responses.append(TaskResponse(
                id=str(task.id),
                title=task.title,
                notes=task.notes,
                priority=str(task.priority) if task.priority else None,
                status=str(task.status) if task.status else None,
                at_risk=task.at_risk,
                due=task.due,
                duration=task.duration,
                duration_text=format_duration_text(task.duration)
            ))
        
        return {
            "count": len(task_responses),
            "tasks": task_responses,
            "filter_info": {
                "excluded_archived": True,
                "description": "Archivierte Tasks werden aus Risiko-Berechnung ausgeschlossen"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For local development only
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

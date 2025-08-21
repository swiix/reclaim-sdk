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

def format_progress_text(time_chunks_spent: Optional[int], time_chunks_remaining: Optional[int]) -> Optional[str]:
    """Format progress as 'Worksessions X/Y' or 'X remaining'"""
    if time_chunks_spent is None or time_chunks_remaining is None:
        return None
    
    if time_chunks_spent == 0 and time_chunks_remaining == 0:
        return None
    
    total_chunks = time_chunks_spent + time_chunks_remaining
    
    if time_chunks_spent == 0:
        return f"{format_duration_text(time_chunks_remaining / 4)} remaining"
    elif time_chunks_remaining == 0:
        return f"{format_duration_text(time_chunks_spent / 4)} done"
    else:
        spent_hours = time_chunks_spent / 4
        total_hours = total_chunks / 4
        return f"Worksessions {format_duration_text(spent_hours)}/{format_duration_text(total_hours)}"

def format_snooze_days(snooze_until: Optional[datetime]) -> Optional[str]:
    """Format snooze information with days postponed"""
    if snooze_until is None:
        return None
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # Calculate days difference
    days_diff = (snooze_until - now).days
    
    if days_diff > 0:
        return f"Aufgeschoben bis {snooze_until.strftime('%d. %B')} (+{days_diff} Tage)"
    elif days_diff < 0:
        return f"Aufgeschoben bis {snooze_until.strftime('%d. %B')} ({abs(days_diff)} Tage überfällig)"
    else:
        return f"Aufgeschoben bis {snooze_until.strftime('%d. %B')} (heute)"

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
    snooze_until: Optional[datetime] = None
    time_chunks_spent: Optional[int] = None
    time_chunks_remaining: Optional[int] = None
    progress_text: Optional[str] = None

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
                "description": "Nur Tasks mit Risiko abrufen (at_risk = true), archivierte und stornierte Tasks werden ausgeschlossen",
                "response": "JSON mit Anzahl, Array von Task-Objekten und Filter-Informationen",
                "filters": {
                    "at_risk": "true",
                    "exclude_archived": "true",
                    "exclude_cancelled": "true"
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
                        "excluded_cancelled": True,
                        "description": "Archivierte und stornierte Tasks werden aus Risiko-Berechnung ausgeschlossen"
                    }
                }
            },
            "tasks_overdue": {
                "path": "/tasks/overdue",
                "method": "GET",
                "description": "Nur überfällige Tasks abrufen (Fälligkeitsdatum in der Vergangenheit)",
                "response": "JSON mit Anzahl, Array von Task-Objekten und Filter-Informationen",
                "filters": {
                    "due_date_past": "true",
                    "exclude_archived": "true",
                    "exclude_cancelled": "true"
                },
                "example_response": {
                    "count": 3,
                    "tasks": [
                        {
                            "id": "9453408",
                            "title": "Überfälliger Task",
                            "notes": "Task ist überfällig",
                            "priority": "TaskPriority.P1",
                            "status": "TaskStatus.SCHEDULED",
                            "at_risk": True,
                            "due": "2025-01-05T10:00:00Z",
                            "duration": 1.0,
                            "duration_text": "1h"
                        }
                    ],
                    "filter_info": {
                        "excluded_archived": True,
                        "excluded_cancelled": True,
                        "description": "Overdue Tasks (Fälligkeitsdatum in der Vergangenheit)"
                    }
                }
            },
            "tasks_summary": {
                "path": "/tasks/summary",
                "method": "GET",
                "description": "E-Mail-Text mit überfälligen und at-risk Tasks, sortiert nach Priorität",
                "response": "JSON mit E-Mail-Text und Statistiken",
                "features": {
                    "sorted_by_priority": "P1, P2, P3, P4",
                    "email_ready": "true",
                    "german_format": "true"
                },
                "example_response": {
                    "text": "📅 15. Januar 2025\n\n📅 Überfällige Tasks (5):\n• steuerberater wechseln (P1) - 17. August - 3h 30min\n\n⚠️ Tasks mit Risiko (35):\n• Biban Umsetzung (P1) - 31. August - 2h 30min\n\nGesamt: 40 Aufgaben benötigen Aufmerksamkeit\n\n🔗 Direkte Links:\n• https://app.reclaim.ai/planner?taskSort=schedule - Zum Planner (Kalender)\n• https://app.reclaim.ai/priorities - Zum Prioritäts Planner",
                    "html": "<h2>📅 15. Januar 2025</h2>\n\n<h3>📅 Überfällige Tasks (5):</h3>\n<ul>\n<li><strong>steuerberater wechseln</strong> (P1) - 17. August - 3h 30min</li>\n</ul>\n\n<h3>⚠️ Tasks mit Risiko (35):</h3>\n<ul>\n<li><strong>Biban Umsetzung</strong> (P1) - 31. August - 2h 30min</li>\n</ul>\n\n<p><strong>Gesamt: 40 Aufgaben benötigen Aufmerksamkeit</strong></p>\n\n<h3>🔗 Direkte Links:</h3>\n<ul>\n<li><a href=\"https://app.reclaim.ai/planner?taskSort=schedule\">Zum Planner (Kalender)</a></li>\n<li><a href=\"https://app.reclaim.ai/priorities\">Zum Prioritäts Planner</a></li>\n</ul>",
                    "overdue_count": 5,
                    "at_risk_count": 35,
                    "total_count": 40,
                    "generated_at": "2025-01-15T10:00:00Z"
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
                duration_text=format_duration_text(task.duration),
                snooze_until=task.snooze_until,
                time_chunks_spent=task.time_chunks_spent,
                time_chunks_remaining=task.time_chunks_remaining,
                progress_text=format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)
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
        
        # Filter tasks that are at risk AND not archived AND not cancelled
        at_risk_tasks = [
            task for task in tasks 
            if (task.at_risk and 
                str(task.status) != "TaskStatus.ARCHIVED" and
                str(task.status) != "TaskStatus.CANCELLED")
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
                duration_text=format_duration_text(task.duration),
                snooze_until=task.snooze_until,
                time_chunks_spent=task.time_chunks_spent,
                time_chunks_remaining=task.time_chunks_remaining,
                progress_text=format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)
            ))
        
        return {
            "count": len(task_responses),
            "tasks": task_responses,
            "filter_info": {
                "excluded_archived": True,
                "excluded_cancelled": True,
                "description": "Archivierte und stornierte Tasks werden aus Risiko-Berechnung ausgeschlossen"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/overdue")
async def get_overdue_tasks():
    """Get only tasks that are overdue (due date in the past)"""
    try:
        from reclaim_sdk.client import ReclaimClient
        from reclaim_sdk.resources.task import Task
        from datetime import datetime, timezone
        
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
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        
        # Filter tasks that are overdue AND not archived AND not cancelled
        overdue_tasks = [
            task for task in tasks 
            if (task.due and task.due < now and 
                str(task.status) != "TaskStatus.ARCHIVED" and
                str(task.status) != "TaskStatus.CANCELLED")
        ]
        
        # Convert to response format
        task_responses = []
        for task in overdue_tasks:
            task_responses.append(TaskResponse(
                id=str(task.id),
                title=task.title,
                notes=task.notes,
                priority=str(task.priority) if task.priority else None,
                status=str(task.status) if task.status else None,
                at_risk=task.at_risk,
                due=task.due,
                duration=task.duration,
                duration_text=format_duration_text(task.duration),
                snooze_until=task.snooze_until,
                time_chunks_spent=task.time_chunks_spent,
                time_chunks_remaining=task.time_chunks_remaining,
                progress_text=format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)
            ))
        
        return {
            "count": len(task_responses),
            "tasks": task_responses,
            "filter_info": {
                "excluded_archived": True,
                "excluded_cancelled": True,
                "description": "Overdue Tasks (Fälligkeitsdatum in der Vergangenheit)"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/summary")
async def get_tasks_summary():
    """Get a summary of overdue and at-risk tasks as readable email text"""
    try:
        from reclaim_sdk.client import ReclaimClient
        from reclaim_sdk.resources.task import Task
        from datetime import datetime, timezone
        
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
        
        # Get current time in UTC
        now = datetime.now(timezone.utc)
        
        # Filter overdue tasks (not archived, not cancelled)
        overdue_tasks = [
            task for task in tasks 
            if (task.due and task.due < now and 
                str(task.status) != "TaskStatus.ARCHIVED" and
                str(task.status) != "TaskStatus.CANCELLED")
        ]
        
        # Filter at-risk tasks (not archived, not cancelled)
        at_risk_tasks = [
            task for task in tasks 
            if (task.at_risk and 
                str(task.status) != "TaskStatus.ARCHIVED" and
                str(task.status) != "TaskStatus.CANCELLED")
        ]
        
        # Sort by priority (P1, P2, P3, P4)
        def priority_sort_key(task):
            priority_order = {"TaskPriority.P1": 1, "TaskPriority.P2": 2, "TaskPriority.P3": 3, "TaskPriority.P4": 4}
            return priority_order.get(str(task.priority), 5)
        
        overdue_tasks.sort(key=priority_sort_key)
        at_risk_tasks.sort(key=priority_sort_key)
        
        # Generate email text
        current_date = datetime.now().strftime("%d. %B %Y")
        
        email_text = f"📅 {current_date}\n\n"
        
        # Overdue section
        email_text += f"📅 Überfällige Tasks ({len(overdue_tasks)}):\n"
        for task in overdue_tasks:
            due_date = task.due.strftime("%d. %B") if task.due else "Kein Datum"
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.", "")
            snooze_info = f" ({format_snooze_days(task.snooze_until)})" if task.snooze_until else ""
            progress_info = f" [{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}]" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            email_text += f"• {task.title} ({priority_short}) - {due_date} - {duration_text}{snooze_info}{progress_info}\n"
        
        email_text += "\n"
        
        # At-risk section
        email_text += f"⚠️ Tasks mit Risiko ({len(at_risk_tasks)}):\n"
        for task in at_risk_tasks:
            due_date = task.due.strftime("%d. %B") if task.due else "Kein Datum"
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.", "")
            snooze_info = f" ({format_snooze_days(task.snooze_until)})" if task.snooze_until else ""
            progress_info = f" [{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}]" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            email_text += f"• {task.title} ({priority_short}) - {due_date} - {duration_text}{snooze_info}{progress_info}\n"
        
        email_text += f"\nGesamt: {len(overdue_tasks) + len(at_risk_tasks)} Aufgaben benötigen Aufmerksamkeit\n\n"
        email_text += "🔗 Direkte Links:\n"
        email_text += "• https://app.reclaim.ai/planner?taskSort=schedule - Zum Planner (Kalender)\n"
        email_text += "• https://app.reclaim.ai/priorities - Zum Prioritäts Planner"
        
        # Generate HTML version
        html_text = f"<h2>📅 {current_date}</h2>\n\n"
        
        # Overdue section
        html_text += f"<h3>📅 Überfällige Tasks ({len(overdue_tasks)}):</h3>\n<ul>\n"
        for task in overdue_tasks:
            due_date = task.due.strftime("%d. %B") if task.due else "Kein Datum"
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.", "")
            snooze_info = f" <em>({format_snooze_days(task.snooze_until)})</em>" if task.snooze_until else ""
            progress_info = f" <strong>[{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}]</strong>" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            html_text += f"<li><strong><a href=\"https://app.reclaim.ai/tasks/{task.id}\">{task.title}</a></strong> ({priority_short}) - {due_date} - {duration_text}{snooze_info}{progress_info}</li>\n"
        html_text += "</ul>\n\n"
        
        # At-risk section
        html_text += f"<h3>⚠️ Tasks mit Risiko ({len(at_risk_tasks)}):</h3>\n<ul>\n"
        for task in at_risk_tasks:
            due_date = task.due.strftime("%d. %B") if task.due else "Kein Datum"
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.", "")
            snooze_info = f" <em>({format_snooze_days(task.snooze_until)})</em>" if task.snooze_until else ""
            progress_info = f" <strong>[{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}]</strong>" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            html_text += f"<li><strong><a href=\"https://app.reclaim.ai/tasks/{task.id}\">{task.title}</a></strong> ({priority_short}) - {duration_text}{snooze_info}{progress_info}</li>\n"
        html_text += "</ul>\n\n"
        
        html_text += f"<p><strong>Gesamt: {len(overdue_tasks) + len(at_risk_tasks)} Aufgaben benötigen Aufmerksamkeit</strong></p>\n\n"
        html_text += "<h3>🔗 Direkte Links:</h3>\n<ul>\n"
        html_text += '<li><a href="https://app.reclaim.ai/planner?taskSort=schedule">Zum Planner (Kalender)</a></li>\n'
        html_text += '<li><a href="https://app.reclaim.ai/priorities">Zum Prioritäts Planner</a></li>\n'
        html_text += "</ul>"
        
        return {
            "text": email_text,
            "html": html_text,
            "overdue_count": len(overdue_tasks),
            "at_risk_count": len(at_risk_tasks),
            "total_count": len(overdue_tasks) + len(at_risk_tasks),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For local development only
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

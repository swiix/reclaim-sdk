from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import sys

# Add the current directory to the path to import reclaim_sdk
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.task import Task, TaskStatus
from reclaim_sdk.resources.event import Event

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
    """Format progress as clean display without brackets and duplication"""
    if time_chunks_spent is None or time_chunks_remaining is None:
        return None
    
    if time_chunks_spent == 0 and time_chunks_remaining == 0:
        return None
    
    total_chunks = time_chunks_spent + time_chunks_remaining
    
    if time_chunks_spent == 0:
        # Nothing done yet - show sessions only if > 1
        total_hours = time_chunks_remaining / 4
        if total_chunks > 1:
            return f"{format_duration_text(total_hours)} ⏳ ({total_chunks} Sessions)"
        else:
            return f"{format_duration_text(total_hours)} ⏳"
    elif time_chunks_remaining == 0:
        # All done - always show sessions
        total_hours = time_chunks_spent / 4
        return f"✅ ({total_chunks} Sessions)"
    else:
        # Partially done - show progress with time breakdown
        spent_hours = time_chunks_spent / 4
        remaining_hours = time_chunks_remaining / 4
        total_hours = total_chunks / 4
        
        # Calculate percentage
        percentage = int((spent_hours / total_hours) * 100)
        
        return f"{format_duration_text(remaining_hours)} ⏳ {percentage}% ({format_duration_text(spent_hours)}/{format_duration_text(total_hours)})"

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

def get_next_event_for_task(task_id: int, client: ReclaimClient) -> Optional[dict]:
    """Get the next scheduled event for a task"""
    try:
        # Get future events for this task
        future_events = Event.list_future_events(client=client, task_ids=[task_id])
        
        if not future_events:
            return None
        
        # Sort by start time and get the earliest
        future_events.sort(key=lambda e: e.event_start if e.event_start else datetime.max.replace(tzinfo=datetime.now().tzinfo))
        next_event = future_events[0]
        
        if not next_event.event_start:
            return None
        
        # Calculate time until start
        now = datetime.now(next_event.event_start.tzinfo)
        time_until = next_event.event_start - now
        
        # Format time until start
        if time_until.days > 0:
            time_until_text = f"in {time_until.days} Tagen"
        elif time_until.total_seconds() > 3600:
            hours = int(time_until.total_seconds() // 3600)
            time_until_text = f"in {hours}h"
        elif time_until.total_seconds() > 60:
            minutes = int(time_until.total_seconds() // 60)
            time_until_text = f"in {minutes}min"
        else:
            time_until_text = "jetzt"
        
        # Check if event is today and add "HEUTE" indicator
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Convert event start to UTC for comparison
        event_start_utc = next_event.event_start.astimezone(timezone.utc)
        
        if today_start <= event_start_utc < today_end:
            time_until_text = f"HEUTE {time_until_text}"
        
        return {
            "event_id": next_event.event_id,
            "title": next_event.title,
            "start": next_event.event_start.isoformat(),
            "end": next_event.event_end.isoformat() if next_event.event_end else None,
            "duration_hours": next_event.get_duration_hours(),
            "time_until": time_until_text,
            "lock_state": next_event.lock_state,
            "defended": next_event.defended
        }
    except Exception:
        return None

def format_due_date_info(due: Optional[datetime], snooze_until: Optional[datetime]) -> str:
    """Format due date information with snooze details"""
    if due is None:
        return "Kein Datum"
    
    due_date = due.strftime("%d. %B")
    
    if snooze_until is None:
        return due_date
    
    # Calculate days between due and snooze
    snooze_days_diff = (snooze_until - due).days
    
    if snooze_days_diff > 0:
        # Snoozed to future
        return f"{due_date} → {snooze_until.strftime('%d. %B')} (+{snooze_days_diff} Tage)"
    elif snooze_days_diff < 0:
        # Snoozed to past
        return f"{due_date} → {snooze_until.strftime('%d. %B')} ({abs(snooze_days_diff)} Tage früher)"
    else:
        # Same day
        return f"{due_date} → {snooze_until.strftime('%d. %B')} (gleicher Tag)"

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
    next_event: Optional[dict] = None

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
                    "text": "📅 15. Januar 2025\n\n📅 Überfällige Tasks (5):\n• steuerberater wechseln (P1) - 17. August - 3h 30min\n\n⚠️ Tasks mit Risiko (35):\n• Biban Umsetzung (P1) - 31. August - 2h 30min\n\nGesamt: 40 Aufgaben benötigen Aufmerksamkeit\n\n🔗 Direkte Links:\n• https://app.reclaim.ai/planner - Kalender\n• https://app.reclaim.ai/priorities - Prioritäten",
                    "html": "<h2>📅 15. Januar 2025</h2>\n\n<h3>📅 Überfällige Tasks (5):</h3>\n<ul>\n<li><strong>steuerberater wechseln</strong> (P1) - 17. August - 3h 30min</li>\n</ul>\n\n<h3>⚠️ Tasks mit Risiko (35):</h3>\n<ul>\n<li><strong>Biban Umsetzung</strong> (P1) - 31. August - 2h 30min</li>\n</ul>\n\n<p><strong>Gesamt: 40 Aufgaben benötigen Aufmerksamkeit</strong></p>\n\n<h3>🔗 Direkte Links:</h3>\n<ul>\n<li><a href=\"https://app.reclaim.ai/planner\">Kalender</a></li>\n<li><a href=\"https://app.reclaim.ai/priorities\">Prioritäten</a></li>\n</ul>",
                    "overdue_count": 5,
                    "at_risk_count": 35,
                    "total_count": 40,
                    "generated_at": "2025-01-15T10:00:00Z"
                }
            },
            "tasks_daily": {
                "path": "/tasks/daily",
                "method": "GET",
                "description": "Tagesübersicht mit Zeitabschätzungen, Dringlichkeitsindikatoren und Aktionsplan",
                "response": "JSON mit Tagesübersicht und Statistiken",
                "features": {
                    "urgency_groups": "Kritisch, Hohe Priorität, Mittlere Priorität",
                    "time_estimates": "Geschätzte Arbeitszeit",
                    "action_plan": "Heute Fokus-Plan",
                    "daily_focused": "Für den Alltag optimiert"
                },
                "example_response": {
                    "text": "📅 Tagesübersicht - 15. Januar 2025\n\n⏰ Geschätzte Arbeitszeit: 8h 30min\n📊 Aufgaben: 40 (Überfällig: 5, Risiko: 35)\n\n🚨 KRITISCH - Sofort erledigen (2):\n• steuerberater wechseln - 17. August → 21. August (+3 Tage) - 3h 30min\n\n🔥 HOHE PRIORITÄT - Heute erledigen (8):\n• Biban Umsetzung - 31. August → 11. July (52 Tage früher) - 2h 30min\n\n⚡ MITTLERE PRIORITÄT - Diese Woche (5):\n• HEK Dokument ausfüllen - 29. August → 16. August (14 Tage früher) - 1h\n... und 20 weitere\n\n🎯 HEUTE FOKUS:\n1. 2 kritische Tasks zuerst\n2. 8 hohe Priorität\n3. 3 mittlere Priorität\n\n🔗 Schnellzugriff:\n• https://app.reclaim.ai/planner - Kalender\n• https://app.reclaim.ai/priorities - Prioritäten",
                    "critical_count": 2,
                    "high_priority_count": 8,
                    "medium_priority_count": 25,
                    "low_priority_count": 5,
                    "total_time_hours": 8.5,
                    "total_tasks": 40,
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
            # Get next event for this task
            next_event = get_next_event_for_task(task.id, client) if task.id else None
            
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
                progress_text=format_progress_text(task.time_chunks_spent, task.time_chunks_remaining),
                next_event=next_event
            ))
        
        return task_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/at-risk")
async def get_tasks_at_risk():
    """Get only tasks that are at risk, excluding archived tasks"""
    try:
        
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
            due_date_info = format_due_date_info(task.due, task.snooze_until)
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.P1", "P1").replace("TaskPriority.P2", "P2").replace("TaskPriority.P3", "P3").replace("TaskPriority.P4", "P4")
            progress_info = format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)
            
            # Get next event info
            next_event = get_next_event_for_task(task.id, client) if task.id else None
            event_info = f" | 📅 {next_event['time_until']}" if next_event else ""
            
            if progress_info:
                email_text += f"• {task.title} ({priority_short}) - {due_date_info} - {progress_info}{event_info}\n"
            else:
                email_text += f"• {task.title} ({priority_short}) - {due_date_info} - {duration_text}{event_info}\n"
        
        email_text += "\n"
        
        # At-risk section (show all at-risk tasks, but overdue ones are already shown above)
        email_text += f"⚠️ Tasks mit Risiko ({len(at_risk_tasks)}):\n"
        for task in at_risk_tasks:
            due_date_info = format_due_date_info(task.due, task.snooze_until)
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.P1", "P1").replace("TaskPriority.P2", "P2").replace("TaskPriority.P3", "P3").replace("TaskPriority.P4", "P4")
            progress_info = format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)
            
            # Get next event info
            next_event = get_next_event_for_task(task.id, client) if task.id else None
            event_info = f" | 📅 {next_event['time_until']}" if next_event else ""
            
            if progress_info:
                email_text += f"• {task.title} ({priority_short}) - {due_date_info} - {progress_info}{event_info}\n"
            else:
                email_text += f"• {task.title} ({priority_short}) - {due_date_info} - {duration_text}{event_info}\n"
        
        email_text += f"\nGesamt: {len(overdue_tasks) + len(at_risk_tasks)} Aufgaben benötigen Aufmerksamkeit\n\n"
        email_text += "🔗 Direkte Links:\n"
        email_text += "• https://app.reclaim.ai/planner - Kalender\n"
        email_text += "• https://app.reclaim.ai/priorities - Prioritäten"
        
        # Generate HTML version
        html_text = f"<h2>📅 {current_date}</h2>\n\n"
        
        # Overdue section
        html_text += f"<h3>📅 Überfällige Tasks ({len(overdue_tasks)}):</h3>\n<ul>\n"
        for task in overdue_tasks:
            due_date_info = format_due_date_info(task.due, task.snooze_until)
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.P1", "P1").replace("TaskPriority.P2", "P2").replace("TaskPriority.P3", "P3").replace("TaskPriority.P4", "P4")
            progress_info = f" <strong>{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}</strong>" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            
            # Get next event info for HTML
            next_event = get_next_event_for_task(task.id, client) if task.id else None
            event_info = f" | <em>📅 {next_event['time_until']}</em>" if next_event else ""
            
            html_text += f"<li><strong><a href=\"https://app.reclaim.ai/tasks/{task.id}\">{task.title}</a></strong> ({priority_short}) - {due_date_info} - {duration_text}{progress_info}{event_info}</li>\n"
        html_text += "</ul>\n\n"
        
        # At-risk section (show all at-risk tasks, but overdue ones are already shown above)
        html_text += f"<h3>⚠️ Tasks mit Risiko ({len(at_risk_tasks)}):</h3>\n<ul>\n"
        for task in at_risk_tasks:
            due_date_info = format_due_date_info(task.due, task.snooze_until)
            duration_text = format_duration_text(task.duration) or "Keine Dauer"
            priority_short = str(task.priority).replace("TaskPriority.P1", "P1").replace("TaskPriority.P2", "P2").replace("TaskPriority.P3", "P3").replace("TaskPriority.P4", "P4")
            progress_info = f" <strong>{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}</strong>" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
            
            # Get next event info for HTML
            next_event = get_next_event_for_task(task.id, client) if task.id else None
            event_info = f" | <em>📅 {next_event['time_until']}</em>" if next_event else ""
            
            html_text += f"<li><strong><a href=\"https://app.reclaim.ai/tasks/{task.id}\">{task.title}</a></strong> ({priority_short}) - {due_date_info} - {duration_text}{progress_info}{event_info}</li>\n"
        html_text += "</ul>\n\n"
        
        html_text += f"<p><strong>Gesamt: {len(overdue_tasks) + len(at_risk_tasks)} Aufgaben benötigen Aufmerksamkeit</strong></p>\n\n"
        html_text += "<h3>🔗 Direkte Links:</h3>\n<ul>\n"
        html_text += '<li><a href="https://app.reclaim.ai/planner">Kalender</a></li>\n'
        html_text += '<li><a href="https://app.reclaim.ai/priorities">Prioritäten</a></li>\n'
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

@app.get("/tasks/daily")
async def get_daily_tasks():
    """Get a daily-focused view of tasks with time estimates and urgency indicators"""
    try:
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
        
        # Filter tasks (same as summary but with additional logic)
        overdue_tasks = []
        at_risk_tasks = []
        
        for task in tasks:
            # Skip archived and cancelled tasks
            if task.status in [TaskStatus.ARCHIVED, TaskStatus.CANCELLED]:
                continue
                
            # Check if overdue (due date is in the past)
            if task.due and task.due < datetime.now(timezone.utc):
                overdue_tasks.append(task)
            # Check if at risk (but not overdue)
            elif task.at_risk and task.due and task.due >= datetime.now(timezone.utc):
                at_risk_tasks.append(task)
        
        # Sort by priority and due date
        def sort_key(task):
            priority_order = {"TaskPriority.P1": 1, "TaskPriority.P2": 2, "TaskPriority.P3": 3, "TaskPriority.P4": 4}
            return (priority_order.get(str(task.priority), 5), task.due or datetime.max.replace(tzinfo=timezone.utc))
        
        overdue_tasks.sort(key=sort_key)
        at_risk_tasks.sort(key=sort_key)
        
        # Calculate total time needed
        total_time = 0
        for task in overdue_tasks + at_risk_tasks:
            if task.duration:
                total_time += task.duration
        
        # Group by urgency
        critical_tasks = []  # Overdue P1
        high_priority_tasks = []  # Overdue P2 or At-risk P1
        medium_priority_tasks = []  # At-risk P2
        low_priority_tasks = []  # At-risk P3/P4
        
        for task in overdue_tasks:
            if str(task.priority) == "TaskPriority.P1":
                critical_tasks.append(task)
            else:
                high_priority_tasks.append(task)
        
        for task in at_risk_tasks:
            if str(task.priority) == "TaskPriority.P1":
                high_priority_tasks.append(task)
            elif str(task.priority) == "TaskPriority.P2":
                medium_priority_tasks.append(task)
            else:
                low_priority_tasks.append(task)
        
        # Generate daily summary
        current_date = datetime.now().strftime("%d. %B %Y")
        
        daily_text = f"📅 Tagesübersicht - {current_date}\n\n"
        
        # Time estimate
        daily_text += f"⏰ Geschätzte Arbeitszeit: {format_duration_text(total_time)}\n"
        daily_text += f"📊 Aufgaben: {len(overdue_tasks + at_risk_tasks)} (Überfällig: {len(overdue_tasks)}, Risiko: {len(at_risk_tasks)})\n\n"
        
        # Critical tasks (most urgent)
        if critical_tasks:
            daily_text += f"🚨 KRITISCH - Sofort erledigen ({len(critical_tasks)}):\n"
            for task in critical_tasks:
                due_date_info = format_due_date_info(task.due, task.snooze_until)
                duration_text = format_duration_text(task.duration) or "Keine Dauer"
                progress_info = f" {format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
                daily_text += f"• {task.title} - {due_date_info} - {duration_text}{progress_info}\n"
            daily_text += "\n"
        
        # High priority tasks
        if high_priority_tasks:
            daily_text += f"🔥 HOHE PRIORITÄT - Heute erledigen ({len(high_priority_tasks)}):\n"
            for task in high_priority_tasks:
                due_date_info = format_due_date_info(task.due, task.snooze_until)
                duration_text = format_duration_text(task.duration) or "Keine Dauer"
                progress_info = f" {format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
                daily_text += f"• {task.title} - {due_date_info} - {duration_text}{progress_info}\n"
            daily_text += "\n"
        
        # Medium priority tasks
        if medium_priority_tasks:
            daily_text += f"⚡ MITTLERE PRIORITÄT - Diese Woche ({len(medium_priority_tasks)}):\n"
            for task in medium_priority_tasks[:5]:  # Limit to 5 for daily view
                due_date_info = format_due_date_info(task.due, task.snooze_until)
                duration_text = format_duration_text(task.duration) or "Keine Dauer"
                progress_info = f" {format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
                daily_text += f"• {task.title} - {due_date_info} - {duration_text}{progress_info}\n"
            if len(medium_priority_tasks) > 5:
                daily_text += f"... und {len(medium_priority_tasks) - 5} weitere\n"
            daily_text += "\n"
        
        # Quick actions
        daily_text += "🎯 HEUTE FOKUS:\n"
        daily_text += f"1. {len(critical_tasks)} kritische Tasks zuerst\n"
        daily_text += f"2. {len(high_priority_tasks)} hohe Priorität\n"
        daily_text += f"3. {min(3, len(medium_priority_tasks))} mittlere Priorität\n\n"
        
        # Links
        daily_text += "🔗 Schnellzugriff:\n"
        daily_text += "• https://app.reclaim.ai/planner - Kalender\n"
        daily_text += "• https://app.reclaim.ai/priorities - Prioritäten\n"
        
        return {
            "text": daily_text,
            "critical_count": len(critical_tasks),
            "high_priority_count": len(high_priority_tasks),
            "medium_priority_count": len(medium_priority_tasks),
            "low_priority_count": len(low_priority_tasks),
            "total_time_hours": total_time,
            "total_tasks": len(overdue_tasks + at_risk_tasks),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting daily tasks: {str(e)}")

@app.get("/tasks/upcoming")
async def get_upcoming_tasks():
    """Get upcoming tasks sorted by due date"""
    try:
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
        
        # Filter upcoming tasks (not overdue, not archived, not cancelled, with due date)
        upcoming_tasks = []
        now = datetime.now(timezone.utc)
        
        for task in tasks:
            # Skip archived and cancelled tasks
            if task.status in [TaskStatus.ARCHIVED, TaskStatus.CANCELLED]:
                continue
                
            # Skip overdue tasks
            if task.due and task.due < now:
                continue
                
            # Include tasks with due date in the future
            if task.due and task.due >= now:
                upcoming_tasks.append(task)
        
        # Sort by due date (earliest first)
        upcoming_tasks.sort(key=lambda x: x.due or datetime.max.replace(tzinfo=timezone.utc))
        
        # Limit to next 20 tasks for overview
        upcoming_tasks = upcoming_tasks[:20]
        
        # Generate upcoming summary
        current_date = datetime.now().strftime("%d. %B %Y")
        
        upcoming_text = f"📅 Nächste geplante Tasks - {current_date}\n\n"
        
        if not upcoming_tasks:
            upcoming_text += "✅ Keine anstehenden Tasks geplant!\n\n"
        else:
            upcoming_text += f"📊 Nächste {len(upcoming_tasks)} Tasks:\n\n"
            
            for i, task in enumerate(upcoming_tasks, 1):
                # Calculate days until due
                days_until = (task.due - now).days
                
                if days_until == 0:
                    due_info = "HEUTE"
                elif days_until == 1:
                    due_info = "MORGEN"
                elif days_until < 7:
                    due_info = f"in {days_until} Tagen"
                else:
                    due_info = f"in {days_until} Tagen"
                
                due_date = task.due.strftime("%d. %B")
                duration_text = format_duration_text(task.duration) or "Keine Dauer"
                priority_short = str(task.priority).replace("TaskPriority.P1", "P1").replace("TaskPriority.P2", "P2").replace("TaskPriority.P3", "P3").replace("TaskPriority.P4", "P4")
                progress_info = f" [{format_progress_text(task.time_chunks_spent, task.time_chunks_remaining)}]" if format_progress_text(task.time_chunks_spent, task.time_chunks_remaining) else ""
                
                upcoming_text += f"{i:2d}. {task.title} ({priority_short}) - {due_date} ({due_info}) - {duration_text}{progress_info}\n"
        
        # Add quick stats
        if upcoming_tasks:
            today_tasks = [t for t in upcoming_tasks if (t.due - now).days == 0]
            tomorrow_tasks = [t for t in upcoming_tasks if (t.due - now).days == 1]
            this_week_tasks = [t for t in upcoming_tasks if (t.due - now).days <= 7]
            
            upcoming_text += f"\n📈 Übersicht:\n"
            upcoming_text += f"• Heute: {len(today_tasks)} Tasks\n"
            upcoming_text += f"• Morgen: {len(tomorrow_tasks)} Tasks\n"
            upcoming_text += f"• Diese Woche: {len(this_week_tasks)} Tasks\n"
        
        # Links
        upcoming_text += "\n🔗 Schnellzugriff:\n"
        upcoming_text += "• https://app.reclaim.ai/planner - Kalender\n"
        upcoming_text += "• https://app.reclaim.ai/priorities - Prioritäten\n"
        
        return {
            "text": upcoming_text,
            "total_upcoming": len(upcoming_tasks),
            "today_count": len([t for t in upcoming_tasks if (t.due - now).days == 0]),
            "tomorrow_count": len([t for t in upcoming_tasks if (t.due - now).days == 1]),
            "this_week_count": len([t for t in upcoming_tasks if (t.due - now).days <= 7]),
            "next_task_due": upcoming_tasks[0].due.isoformat() if upcoming_tasks else None,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting upcoming tasks: {str(e)}")

# For local development only
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

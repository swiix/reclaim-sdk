from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import sys

# Add the parent directory to the path to import reclaim_sdk
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Simple Reclaim Tasks API",
    description="Simplified API für Reclaim.ai Aufgabenverwaltung",
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

@app.get("/")
async def root():
    return {
        "message": "Reclaim Tasks API",
        "version": "1.0.0",
        "endpoints": {
            "tasks": "/tasks",
            "tasks_at_risk": "/tasks/at-risk",
            "health": "/health"
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
                duration=task.duration
            ))
        
        return task_responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/at-risk")
async def get_tasks_at_risk():
    """Get only tasks that are at risk"""
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
        
        # Filter tasks that are at risk
        at_risk_tasks = [task for task in tasks if task.at_risk]
        
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
                duration=task.duration
            ))
        
        return {
            "count": len(task_responses),
            "tasks": task_responses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

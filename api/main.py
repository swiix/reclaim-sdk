from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import sys

# Add the parent directory to the path to import reclaim_sdk
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reclaim_sdk.client import ReclaimClient
from reclaim_sdk.resources.task import Task
from reclaim_sdk.exceptions import (
    ReclaimAPIError,
    AuthenticationError,
    RecordNotFound
)

app = FastAPI(
    title="Reclaim Tasks API",
    description="REST API für Reclaim.ai Aufgabenverwaltung",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class TaskResponse(BaseModel):
    id: str
    title: str
    notes: Optional[str] = None
    due: Optional[datetime] = None
    priority: Optional[str] = None
    duration: Optional[float] = None
    max_work_duration: Optional[float] = None
    min_work_duration: Optional[float] = None
    event_color: Optional[str] = None
    up_next: Optional[bool] = None
    status: Optional[str] = None
    time_scheme_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ErrorResponse(BaseModel):
    error: str
    message: str

def get_reclaim_client():
    """Dependency to get configured ReclaimClient"""
    try:
        # Check if token is configured
        token = os.environ.get("RECLAIM_TOKEN")
        if not token:
            raise HTTPException(
                status_code=500,
                detail="RECLAIM_TOKEN environment variable is not set"
            )
        
        # Configure client if not already done
        if not ReclaimClient._instance:
            ReclaimClient.configure(token=token)
        
        return ReclaimClient()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Reclaim client: {str(e)}"
        )

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Reclaim Tasks API",
        "version": "1.0.0",
        "endpoints": {
            "tasks": "/tasks",
            "task_by_id": "/tasks/{task_id}",
            "docs": "/docs"
        }
    }

@app.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks(client: ReclaimClient = Depends(get_reclaim_client)):
    """
    Retrieve all tasks from Reclaim.ai
    
    Returns:
        List of all tasks with their details
    """
    try:
        tasks = Task.list()
        
        # Convert Task objects to response models
        task_responses = []
        for task in tasks:
            task_response = TaskResponse(
                id=task.id,
                title=task.title,
                notes=task.notes,
                due=task.due,
                priority=str(task.priority) if task.priority else None,
                duration=task.duration,
                max_work_duration=task.max_work_duration,
                min_work_duration=task.min_work_duration,
                event_color=str(task.event_color) if task.event_color else None,
                up_next=task.on_deck,
                status=str(task.status) if task.status else None,
                time_scheme_id=task.time_scheme_id,
                created_at=task.created,
                updated_at=task.updated
            )
            task_responses.append(task_response)
        
        return task_responses
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
    except ReclaimAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reclaim API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: str,
    client: ReclaimClient = Depends(get_reclaim_client)
):
    """
    Retrieve a specific task by ID
    
    Args:
        task_id: The ID of the task to retrieve
        
    Returns:
        Task details
    """
    try:
        task = Task.get(task_id)
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            notes=task.notes,
            due=task.due,
            priority=str(task.priority) if task.priority else None,
            duration=task.duration,
            max_work_duration=task.max_work_duration,
            min_work_duration=task.min_work_duration,
            event_color=str(task.event_color) if task.event_color else None,
            up_next=task.on_deck,
            status=str(task.status) if task.status else None,
            time_scheme_id=task.time_scheme_id,
            created_at=task.created,
            updated_at=task.updated
        )
        
    except RecordNotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
    except ReclaimAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reclaim API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

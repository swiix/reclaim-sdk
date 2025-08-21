from pydantic import Field, field_validator
from datetime import datetime, timezone
from typing import ClassVar, Optional, List
from enum import Enum
from reclaim_sdk.resources.base import BaseResource


class EventColor(str, Enum):
    NONE = "NONE"
    LAVENDER = "LAVENDER"
    SAGE = "SAGE"
    GRAPE = "GRAPE"
    FLAMINGO = "FLAMINGO"
    BANANA = "BANANA"
    TANGERINE = "TANGERINE"
    PEACOCK = "PEACOCK"
    GRAPHITE = "GRAPHITE"
    BLUEBERRY = "BLUEBERRY"
    BASIL = "BASIL"
    TOMATO = "TOMATO"


class EventCategory(str, Enum):
    WORK = "WORK"
    PERSONAL = "PERSONAL"


class Event(BaseResource):
    ENDPOINT: ClassVar[str] = "/api/events"

    # Core fields
    event_id: Optional[str] = Field(None, alias="eventId", description="Event ID")
    title: Optional[str] = Field(None, description="Event title")
    title_seen_by_others: Optional[str] = Field(
        None, alias="titleSeenByOthers", description="Title seen by others"
    )
    
    # Type and category
    type: Optional[str] = Field(None, description="Event type (WORK, PERSONAL)")
    sub_type: Optional[str] = Field(None, alias="subType", description="Event subtype")
    category: Optional[str] = Field(None, description="Event category")
    scored_type: Optional[str] = Field(None, alias="scoredType", description="Scored type")
    
    # Priority
    priority: Optional[str] = Field(None, description="Event priority")
    priority_source: Optional[str] = Field(None, alias="prioritySource", description="Priority source")
    
    # Time-related fields
    event_start: Optional[datetime] = Field(None, alias="eventStart", description="Event start time")
    event_end: Optional[datetime] = Field(None, alias="eventEnd", description="Event end time")
    time_chunks: Optional[int] = Field(None, alias="timeChunks", description="Time chunks")
    allocated_time_chunks: Optional[int] = Field(None, alias="allocatedTimeChunks", description="Allocated time chunks")
    
    # Calendar and organization
    calendar_id: Optional[int] = Field(None, alias="calendarId", description="Calendar ID")
    key: Optional[str] = Field(None, description="Event key")
    organizer: Optional[str] = Field(None, description="Event organizer")
    
    # Status and visibility
    status: Optional[str] = Field(None, description="Event status")
    public: Optional[bool] = Field(None, description="Is public event")
    private: Optional[bool] = Field(None, description="Is private event")
    free: Optional[bool] = Field(None, description="Is free time")
    published: Optional[bool] = Field(None, description="Is published")
    
    # Color and appearance
    color: Optional[str] = Field(None, description="Event color")
    
    # Reclaim-specific fields
    reclaim_event_type: Optional[str] = Field(None, alias="reclaimEventType", description="Reclaim event type")
    reclaim_managed: Optional[bool] = Field(None, alias="reclaimManaged", description="Is reclaim managed")
    under_assist_control: Optional[bool] = Field(None, alias="underAssistControl", description="Under assist control")
    
    # Task-related fields (from assist object)
    task_id: Optional[int] = Field(None, alias="taskId", description="Associated task ID")
    
    # Additional fields
    requires_travel: Optional[bool] = Field(None, alias="requiresTravel", description="Requires travel")
    rsvp_status: Optional[str] = Field(None, alias="rsvpStatus", description="RSVP status")
    online_meeting_url: Optional[str] = Field(None, alias="onlineMeetingUrl", description="Online meeting URL")
    attendees: Optional[list] = Field(None, description="Event attendees")
    num_attendees: Optional[int] = Field(None, alias="numAttendees", description="Number of attendees")
    
    # Recurring and series
    recurring: Optional[bool] = Field(None, description="Is recurring event")
    recurring_instance: Optional[bool] = Field(None, alias="recurringInstance", description="Is recurring instance")
    recurring_exception: Optional[bool] = Field(None, alias="recurringException", description="Is recurring exception")
    
    # Version and metadata
    version: Optional[str] = Field(None, description="Event version")
    etag: Optional[str] = Field(None, description="Event ETag")
    manually_started: Optional[bool] = Field(None, alias="manuallyStarted", description="Manually started")
    conference_call: Optional[bool] = Field(None, alias="conferenceCall", description="Is conference call")
    source_event_type: Optional[str] = Field(None, alias="sourceEventType", description="Source event type")
    
    @field_validator("time_chunks", "allocated_time_chunks", mode="before")
    @classmethod
    def validate_chunks(cls, v):
        if v is not None:
            return int(v)
        return v

    @field_validator("task_id", mode="before")
    @classmethod
    def validate_task_id(cls, v):
        if v is not None:
            return int(v)
        return v

    @classmethod
    def list_by_date_range(
        cls, 
        start_date: datetime, 
        end_date: datetime, 
        client=None, 
        all_connected: bool = True,
        task_ids: Optional[List[int]] = None,
        **params
    ) -> List["Event"]:
        """
        List events within a date range with optional task filtering
        
        Args:
            start_date: Start date for the range
            end_date: End date for the range
            client: ReclaimClient instance
            all_connected: Include all connected events
            task_ids: Filter by specific task IDs
            **params: Additional query parameters
        """
        if client is None:
            from reclaim_sdk.client import ReclaimClient
            client = ReclaimClient()
        
        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Build query parameters
        query_params = {
            "start": start_str,
            "end": end_str,
            "allConnected": all_connected,
            **params
        }
        
        # Add task IDs if provided
        if task_ids:
            query_params["taskIds"] = ",".join(map(str, task_ids))
        
        data = client.get(cls.ENDPOINT, params=query_params)
        
        # Process events and extract task_id from assist object
        events = []
        for item in data:
            # Extract task_id from assist object if present
            if "assist" in item and isinstance(item["assist"], dict):
                assist = item["assist"]
                if "taskId" in assist:
                    item["taskId"] = assist["taskId"]
            
            events.append(cls.from_api_data(item))
        
        return events

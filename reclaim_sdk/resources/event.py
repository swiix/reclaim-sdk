from pydantic import Field, field_validator
from datetime import datetime, timezone, timedelta
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
    
    # Assist object fields (extracted from assist)
    assist_type: Optional[str] = Field(None, alias="assistType", description="Assist type")
    assist_status: Optional[str] = Field(None, alias="assistStatus", description="Assist status")
    last_controlled_hash: Optional[int] = Field(None, alias="lastControlledHash", description="Last controlled hash")
    defended: Optional[bool] = Field(None, description="Is defended")
    task_index: Optional[int] = Field(None, alias="taskIndex", description="Task index")
    pinned: Optional[bool] = Field(None, description="Is pinned")
    lock_state: Optional[str] = Field(None, alias="lockState", description="Lock state")
    event_type: Optional[str] = Field(None, alias="eventType", description="Event type")
    smart_series: Optional[bool] = Field(None, alias="smartSeries", description="Is smart series")
    assist_reference_valid: Optional[bool] = Field(None, alias="assistReferenceValid", description="Assist reference valid")
    habit_or_task: Optional[bool] = Field(None, alias="habitOrTask", description="Is habit or task")
    conference_buffer: Optional[bool] = Field(None, alias="conferenceBuffer", description="Is conference buffer")
    focus: Optional[bool] = Field(None, description="Is focus")
    custom_habit: Optional[bool] = Field(None, alias="customHabit", description="Is custom habit")
    travel_buffer: Optional[bool] = Field(None, alias="travelBuffer", description="Is travel buffer")
    
    # Merge details
    merge_key: Optional[str] = Field(None, alias="mergeKey", description="Merge key")
    merge_type: Optional[str] = Field(None, alias="mergeType", description="Merge type")
    source_calendar_id: Optional[str] = Field(None, alias="sourceCalendarId", description="Source calendar ID")
    source_reclaim_calendar_id: Optional[int] = Field(None, alias="sourceReclaimCalendarId", description="Source reclaim calendar ID")
    
    # Additional flags
    personal_sync: Optional[bool] = Field(None, alias="personalSync", description="Personal sync")
    reclaim_managed_and_self_organized: Optional[bool] = Field(None, alias="reclaimManagedAndSelfOrganized", description="Reclaim managed and self organized")
    
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
        
        # Process events and extract fields from assist object
        events = []
        for item in data:
            # Extract fields from assist object if present
            if "assist" in item and isinstance(item["assist"], dict):
                assist = item["assist"]
                # Map assist fields to top-level fields
                assist_mapping = {
                    "type": "assistType",
                    "status": "assistStatus", 
                    "lastControlledHash": "lastControlledHash",
                    "defended": "defended",
                    "taskId": "taskId",
                    "taskIndex": "taskIndex",
                    "pinned": "pinned",
                    "lockState": "lockState",
                    "eventType": "eventType",
                    "manuallyStarted": "manuallyStarted",
                    "smartSeries": "smartSeries",
                    "task": "task",
                    "assistReferenceValid": "assistReferenceValid",
                    "habitOrTask": "habitOrTask",
                    "conferenceBuffer": "conferenceBuffer",
                    "focus": "focus",
                    "customHabit": "customHabit",
                    "travelBuffer": "travelBuffer"
                }
                
                for assist_key, field_name in assist_mapping.items():
                    if assist_key in assist:
                        item[field_name] = assist[assist_key]
            
            # Extract fields from mergeDetails if present
            if "mergeDetails" in item and isinstance(item["mergeDetails"], dict):
                merge = item["mergeDetails"]
                merge_mapping = {
                    "key": "mergeKey",
                    "type": "mergeType",
                    "sourceCalendarId": "sourceCalendarId",
                    "sourceReclaimCalendarId": "sourceReclaimCalendarId"
                }
                
                for merge_key, field_name in merge_mapping.items():
                    if merge_key in merge:
                        item[field_name] = merge[merge_key]
            
            events.append(cls.from_api_data(item))
        
        return events

    @classmethod
    def list_future_events(
        cls,
        client=None,
        all_connected: bool = True,
        task_ids: Optional[List[int]] = None,
        **params
    ) -> List["Event"]:
        """
        List future events (events that haven't started yet)
        
        Args:
            client: ReclaimClient instance
            all_connected: Include all connected events
            task_ids: Filter by specific task IDs
            **params: Additional query parameters
        """
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        # Get events for next 6 months
        end_date = now.replace(month=now.month + 6 if now.month <= 6 else now.month - 6, 
                              year=now.year + 1 if now.month > 6 else now.year)
        
        events = cls.list_by_date_range(
            start_date=now,
            end_date=end_date,
            client=client,
            all_connected=all_connected,
            task_ids=task_ids,
            **params
        )
        
        # Filter to only future events
        future_events = []
        for event in events:
            if event.event_start and event.event_start > now:
                future_events.append(event)
        
        return future_events

    @classmethod
    def list_past_events(
        cls,
        client=None,
        all_connected: bool = True,
        task_ids: Optional[List[int]] = None,
        days_back: int = 30,
        **params
    ) -> List["Event"]:
        """
        List past events (events that have already ended)
        
        Args:
            client: ReclaimClient instance
            all_connected: Include all connected events
            task_ids: Filter by specific task IDs
            days_back: How many days back to look (default: 30)
            **params: Additional query parameters
        """
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days_back)
        
        events = cls.list_by_date_range(
            start_date=start_date,
            end_date=now,
            client=client,
            all_connected=all_connected,
            task_ids=task_ids,
            **params
        )
        
        # Filter to only past events
        past_events = []
        for event in events:
            if event.event_end and event.event_end < now:
                past_events.append(event)
        
        return past_events

    @classmethod
    def list_today_events(
        cls,
        client=None,
        all_connected: bool = True,
        task_ids: Optional[List[int]] = None,
        **params
    ) -> List["Event"]:
        """
        List events for today
        
        Args:
            client: ReclaimClient instance
            all_connected: Include all connected events
            task_ids: Filter by specific task IDs
            **params: Additional query parameters
        """
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        events = cls.list_by_date_range(
            start_date=today_start,
            end_date=today_end,
            client=client,
            all_connected=all_connected,
            task_ids=task_ids,
            **params
        )
        
        return events

    def is_future(self) -> bool:
        """Check if this event is in the future"""
        from datetime import datetime, timezone
        
        if not self.event_start:
            return False
        
        now = datetime.now(timezone.utc)
        return self.event_start > now

    def is_past(self) -> bool:
        """Check if this event is in the past"""
        from datetime import datetime, timezone
        
        if not self.event_end:
            return False
        
        now = datetime.now(timezone.utc)
        return self.event_end < now

    def is_today(self) -> bool:
        """Check if this event is today"""
        from datetime import datetime, timezone, timedelta
        
        if not self.event_start:
            return False
        
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        return today_start <= self.event_start < today_end

    def get_duration_hours(self) -> Optional[float]:
        """Get event duration in hours"""
        if self.event_start and self.event_end:
            duration = self.event_end - self.event_start
            return duration.total_seconds() / 3600
        return None

    def get_time_until_start(self) -> Optional[timedelta]:
        """Get time until event starts (for future events)"""
        from datetime import datetime, timezone
        
        if not self.event_start:
            return None
        
        now = datetime.now(timezone.utc)
        if self.event_start > now:
            return self.event_start - now
        return None

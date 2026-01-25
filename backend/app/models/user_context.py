"""
User Context Model

This module defines the user context that gets passed with each LLM call.
It includes information about the user's timezone, location, and current time.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserContext(BaseModel):
    """
    User context information passed with each LLM call.
    
    This provides the AI agents with accurate information about:
    - Current time in the user's timezone
    - User's timezone
    - User's location (for context-aware suggestions)
    - User's locale/language preferences
    """
    
    current_timestamp: datetime = Field(
        ..., 
        description="Current time in the user's timezone"
    )
    
    timezone: str = Field(
        default="UTC", 
        description="User's timezone (e.g., 'America/New_York', 'Asia/Kolkata')"
    )
    
    locale: str = Field(
        default="en_US",
        description="User's locale for language/formatting (e.g., 'en_US', 'hi_IN')"
    )
    
    country: Optional[str] = Field(
        default=None,
        description="User's country code (e.g., 'US', 'IN')"
    )
    
    is_dst: Optional[bool] = Field(
        default=None,
        description="Whether daylight saving time is active in the user's timezone"
    )
    
    offset_hours: float = Field(
        default=0,
        description="UTC offset in hours (e.g., -5 for EST, 5.5 for IST)"
    )
    
    day_of_week: str = Field(
        default="",
        description="Current day of week (e.g., 'Monday')"
    )
    
    time_of_day: str = Field(
        default="",
        description="Time period (e.g., 'morning', 'afternoon', 'evening', 'night')"
    )
    
    @classmethod
    def from_timezone(cls, timezone: str = "UTC", user_timestamp: Optional[datetime] = None) -> "UserContext":
        """
        Create UserContext from timezone string.
        
        Args:
            timezone: Timezone string (e.g., 'America/New_York', 'Asia/Kolkata')
            user_timestamp: Current time in user's timezone (defaults to now)
            
        Returns:
            UserContext instance with calculated values
        """
        from datetime import datetime, timezone as tz
        import pytz
        
        if user_timestamp is None:
            # Get current time in the specified timezone
            tz_obj = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
            user_timestamp = datetime.now(tz_obj)
        
        # Get timezone info
        tz_obj = pytz.timezone(timezone) if timezone != "UTC" else pytz.UTC
        offset = user_timestamp.utcoffset()
        offset_hours = offset.total_seconds() / 3600 if offset else 0
        
        # Get day of week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week = days[user_timestamp.weekday()]
        
        # Get time of day
        hour = user_timestamp.hour
        if hour < 6:
            time_of_day = "night"
        elif hour < 12:
            time_of_day = "morning"
        elif hour < 17:
            time_of_day = "afternoon"
        elif hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Check DST
        is_dst = bool(user_timestamp.dst())
        
        return cls(
            current_timestamp=user_timestamp,
            timezone=timezone,
            offset_hours=offset_hours,
            day_of_week=day_of_week,
            time_of_day=time_of_day,
            is_dst=is_dst
        )
    
    def to_prompt_string(self) -> str:
        """
        Convert context to a string for inclusion in LLM prompts.
        
        Returns:
            Formatted context string
        """
        formatted_time = self.current_timestamp.strftime("%B %d, %Y at %I:%M %p")
        return f"""USER CONTEXT:
- Current Date & Time: {formatted_time}
- Timezone: {self.timezone} (UTC{self.offset_hours:+.1f})
- Day of Week: {self.day_of_week}
- Time of Day: {self.time_of_day.capitalize()}
- Locale: {self.locale}"""

    def to_system_prompt_context(self) -> str:
        """
        Convert context to system prompt context.
        
        Returns:
            System prompt context string
        """
        return f"""You are aware that:
- Today is {self.day_of_week}, {self.current_timestamp.strftime('%B %d, %Y')}
- Current time is {self.current_timestamp.strftime('%I:%M %p')} in {self.timezone}
- It is {self.time_of_day} for the user

When interpreting relative dates or times:
- "tomorrow" means {(self.current_timestamp.replace(hour=0, minute=0, second=0, microsecond=0).day + 1)}
- "today" means {self.current_timestamp.strftime('%B %d, %Y')}
- "next week" means the week starting {self.current_timestamp.strftime('%B %d, %Y')}
- "next {self.day_of_week}" means the {self.day_of_week} of next week"""

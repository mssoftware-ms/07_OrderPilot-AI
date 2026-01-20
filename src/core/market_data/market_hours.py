"""
Market Session Utilities.

Provides functionality to determine active global trading sessions and market status.
"""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
import pytz
from typing import List, Optional

@dataclass
class MarketSession:
    """Represents a market trading session."""
    name: str
    timezone: str
    open_time: time
    close_time: time
    color: str  # Hex color for visual indication

    @property
    def tz(self):
        return pytz.timezone(self.timezone)

    def is_active(self, current_dt: datetime = None) -> bool:
        """Check if session is currently active."""
        if current_dt is None:
            current_dt = datetime.now(pytz.utc)
        
        # Convert current UTC time to market timezone
        market_now = current_dt.astimezone(self.tz)
        
        # Check if weekend
        if market_now.weekday() >= 5:
            return False
            
        current_time = market_now.time()
        
        if self.open_time <= self.close_time:
             return self.open_time <= current_time < self.close_time
        else:
            # Crosses midnight (e.g. Asia/Sydney sometimes)
            return current_time >= self.open_time or current_time < self.close_time

    def time_until_open(self, current_dt: datetime = None) -> timedelta:
        """Time until next open."""
        if current_dt is None:
            current_dt = datetime.now(pytz.utc)
        
        market_now = current_dt.astimezone(self.tz)
        today_open = datetime.combine(market_now.date(), self.open_time).replace(tzinfo=self.tz)
        
        if market_now.time() < self.open_time:
            return today_open - market_now
        else:
            # Tomorrow
            tomorrow_open = today_open + timedelta(days=1)
            return tomorrow_open - market_now

    def time_until_close(self, current_dt: datetime = None) -> timedelta:
        """Time until close (if active)."""
        if not self.is_active(current_dt):
            return timedelta(0)
            
        if current_dt is None:
            current_dt = datetime.now(pytz.utc)
            
        market_now = current_dt.astimezone(self.tz)
        today_close = datetime.combine(market_now.date(), self.close_time).replace(tzinfo=self.tz)
        
        if self.close_time < self.open_time: # Crosses midnight
             if market_now.time() >= self.open_time:
                 today_close += timedelta(days=1)
                 
        return today_close - market_now


# Define Global Sessions
# Using winter/standard times approximations or explicit timezones handling DST
SESSIONS = [
    MarketSession(
        name="London",
        timezone="Europe/London",
        open_time=time(8, 0),
        close_time=time(16, 30),
        color="#0052CC" # Blue
    ),
    MarketSession(
        name="New York",
        timezone="America/New_York",
        open_time=time(9, 30),
        close_time=time(16, 0),
        color="#008DA6" # Cyan/Teal
    ),
    MarketSession(
        name="NY Evening", # After hours / Late session
        timezone="America/New_York",
        open_time=time(16, 0),
        close_time=time(20, 0),
        color="#FF8C00" # Dark Orange
    ),
    MarketSession(
        name="Tokyo",
        timezone="Asia/Tokyo",
        open_time=time(9, 0),
        close_time=time(15, 0),
        color="#E91E63" # Pink
    ),
    MarketSession(
        name="Sydney",
        timezone="Australia/Sydney",
        open_time=time(10, 0),
        close_time=time(16, 0),
        color="#9C27B0" # Purple
    )
]

def get_active_sessions(current_dt: datetime = None) -> List[MarketSession]:
    """Get list of currently active sessions."""
    return [s for s in SESSIONS if s.is_active(current_dt)]

def get_next_event(current_dt: datetime = None) -> str:
    """Get description of next major event."""
    if current_dt is None:
        current_dt = datetime.now(pytz.utc)
        
    # Find active sessions closing soon or inactive sessions opening soon
    events = []
    
    for s in SESSIONS:
        if s.is_active(current_dt):
            remaining = s.time_until_close(current_dt)
            if remaining < timedelta(hours=24):
                events.append((remaining, f"{s.name} Closes"))
        else:
            until_open = s.time_until_open(current_dt)
            if until_open < timedelta(hours=24):
                 events.append((until_open, f"{s.name} Opens"))
    
    if not events:
        return "Market Closed"
        
    events.sort(key=lambda x: x[0])
    next_evt = events[0]
    
    # Format time
    seconds = int(next_evt[0].total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    return f"{next_evt[1]} in {hours}h {minutes}m"

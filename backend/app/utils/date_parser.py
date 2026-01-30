"""
Date parsing utilities for natural language and ISO format date strings.

This module provides unified date parsing functionality used across agents
and services to convert various date formats into standardized datetime objects.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date string in various formats to datetime object.

    Handles:
    - ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    - Natural language: "tomorrow", "next week", "next friday"
    - Relative: "in 3 days", "in 7 days"

    Args:
        date_str: Date string to parse (case-insensitive)

    Returns:
        datetime object or None if unparseable. Uses datetime.now() as fallback
        for unparseable dates (logs warning).

    Examples:
        >>> parse_date_string("2026-02-05")
        datetime.datetime(2026, 2, 5, 0, 0)

        >>> parse_date_string("tomorrow").date() == (datetime.now().date() + timedelta(days=1))
        True

        >>> parse_date_string("next friday")
        datetime.datetime(..., 0, 0)
    """
    if not date_str:
        return None

    date_str_lower = date_str.lower().strip()
    today = datetime.now().date()

    # Try ISO format first
    try:
        return datetime.fromisoformat(date_str_lower)
    except (ValueError, TypeError):
        pass

    # Handle natural language dates
    if "tomorrow" in date_str_lower:
        return datetime.combine(today + timedelta(days=1), datetime.min.time())
    elif "today" in date_str_lower:
        return datetime.combine(today, datetime.min.time())
    elif "next week" in date_str_lower:
        return datetime.combine(today + timedelta(days=7), datetime.min.time())
    elif "next" in date_str_lower and any(
        day in date_str_lower
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
    ):
        # Find next occurrence of specified day
        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        for day_name, day_num in weekday_map.items():
            if day_name in date_str_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return datetime.combine(
                    today + timedelta(days=days_ahead), datetime.min.time()
                )
    elif "in 3" in date_str_lower or "3 days" in date_str_lower:
        return datetime.combine(today + timedelta(days=3), datetime.min.time())
    elif "in 7" in date_str_lower or "week" in date_str_lower:
        return datetime.combine(today + timedelta(days=7), datetime.min.time())

    # Default fallback - return current datetime with warning
    logger.warning(f"Could not parse date: {date_str}, using current datetime")
    return datetime.now()


def parse_relative_date(date_string: str) -> str:
    """
    Parse relative date strings to ISO format (YYYY-MM-DD).

    This is the string-based version preferred by some agents that need
    ISO string format for API calls.

    Args:
        date_string: Date string like "tomorrow", "next week", "next friday"

    Returns:
        ISO formatted date string (YYYY-MM-DD)

    Examples:
        >>> parse_relative_date("tomorrow")
        "2026-01-30"

        >>> parse_relative_date("2026-02-05")
        "2026-02-05"

        >>> parse_relative_date("next monday")
        "2026-02-03"
    """
    today = datetime.now().date()
    date_string_lower = date_string.lower().strip()

    # Check for various relative date patterns
    if "tomorrow" in date_string_lower:
        return (today + timedelta(days=1)).isoformat()
    elif "today" in date_string_lower:
        return today.isoformat()
    elif "next week" in date_string_lower:
        return (today + timedelta(days=7)).isoformat()
    elif "next" in date_string_lower and any(
        day in date_string_lower
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
    ):
        # Find next occurrence of specified day
        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        for day_name, day_num in weekday_map.items():
            if day_name in date_string_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).isoformat()
    elif "in 3 days" in date_string_lower or "3 days" in date_string_lower:
        return (today + timedelta(days=3)).isoformat()
    elif (
        "in 7 days" in date_string_lower
        or ("week" in date_string_lower and "next" not in date_string_lower)
    ):
        return (today + timedelta(days=7)).isoformat()
    else:
        # Try to parse as ISO format if already in YYYY-MM-DD format
        try:
            datetime.fromisoformat(date_string_lower)
            return date_string_lower
        except (ValueError, TypeError):
            # Default to 3 days from now if unparseable
            logger.warning(f"Could not parse date: {date_string}, using 3 days from now")
            return (today + timedelta(days=3)).isoformat()

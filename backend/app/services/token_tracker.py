"""
Token Usage Tracking Service

Tracks OpenAI token consumption per user for billing and analytics.
"""

from app.firebase import get_firestore_client
from firebase_admin import firestore
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TokenTracker:
    """
    Tracks token usage per user for billing and monitoring.
    
    Usage is stored daily in Firestore:
    users/{userId}/usage/tokens/{YYYY-MM-DD}
    """

    def __init__(self):
        self.db = get_firestore_client()

    def record_usage(
        self,
        user_id: str,
        tokens: int,
        model: str = "gpt-4o-mini",
        cost: Optional[float] = None
    ) -> None:
        """
        Record token usage for a user.

        Args:
            user_id: Firebase UID
            tokens: Number of tokens consumed
            model: Model used (for cost calculation)
            cost: Pre-calculated cost (optional)
        """
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Calculate cost if not provided
            if cost is None:
                cost = self._calculate_cost(tokens, model)

            # Get reference to today's usage document
            usage_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("usage")
                .document("tokens")
                .collection("daily")
                .document(today)
            )

            # Update or create the document
            usage_ref.set({
                "date": today,
                "openai_tokens": firestore.Increment(tokens),
                "requests_count": firestore.Increment(1),
                "cost_estimate": firestore.Increment(cost),
                f"models.{model}": firestore.Increment(tokens),
                "updated_at": firestore.SERVER_TIMESTAMP
            }, merge=True)

            # Update user's total usage summary
            user_ref = self.db.collection("users").document(user_id)
            user_ref.set({
                "total_tokens_used": firestore.Increment(tokens),
                "last_activity": firestore.SERVER_TIMESTAMP
            }, merge=True)

            logger.info(f"Recorded {tokens} tokens for user {user_id}, model {model}")

        except Exception as e:
            logger.error(f"Error recording token usage: {e}")
            # Don't raise - we don't want to fail the request due to tracking errors

    def get_user_usage(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, any]:
        """
        Get user's token usage for the last N days.

        Args:
            user_id: Firebase UID
            days: Number of days to look back

        Returns:
            Dict with total usage and daily breakdown
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Query daily usage documents
            usage_collection = (
                self.db.collection("users")
                .document(user_id)
                .collection("usage")
                .document("tokens")
                .collection("daily")
            )

            # Get documents for date range
            docs = usage_collection.where(
                filter=firestore.FieldFilter("date", ">=", start_date.strftime("%Y-%m-%d"))
            ).where(
                filter=firestore.FieldFilter("date", "<=", end_date.strftime("%Y-%m-%d"))
            ).stream()

            daily_usage = []
            total_tokens = 0
            total_cost = 0.0
            total_requests = 0

            for doc in docs:
                data = doc.to_dict()
                daily_usage.append({
                    "date": data.get("date"),
                    "tokens": data.get("openai_tokens", 0),
                    "requests": data.get("requests_count", 0),
                    "cost": data.get("cost_estimate", 0.0),
                    "models": data.get("models", {})
                })
                total_tokens += data.get("openai_tokens", 0)
                total_cost += data.get("cost_estimate", 0.0)
                total_requests += data.get("requests_count", 0)

            # Sort by date
            daily_usage.sort(key=lambda x: x["date"])

            return {
                "user_id": user_id,
                "period_start": start_date.strftime("%Y-%m-%d"),
                "period_end": end_date.strftime("%Y-%m-%d"),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "total_requests": total_requests,
                "daily_usage": daily_usage
            }

        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            return {
                "user_id": user_id,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_usage": []
            }

    def get_system_usage(
        self,
        days: int = 30
    ) -> Dict[str, any]:
        """
        Get system-wide token usage for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dict with system-wide usage statistics
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get all users
            users = self.db.collection("users").stream()

            total_tokens = 0
            total_cost = 0.0
            total_requests = 0
            active_users = set()
            daily_totals = {}

            for user_doc in users:
                user_id = user_doc.id
                usage_data = self.get_user_usage(user_id, days)

                if usage_data["total_tokens"] > 0:
                    active_users.add(user_id)
                    total_tokens += usage_data["total_tokens"]
                    total_cost += usage_data["total_cost"]
                    total_requests += usage_data["total_requests"]

                    # Aggregate daily totals
                    for day in usage_data["daily_usage"]:
                        date = day["date"]
                        if date not in daily_totals:
                            daily_totals[date] = {
                                "tokens": 0,
                                "cost": 0.0,
                                "users": set()
                            }
                        daily_totals[date]["tokens"] += day["tokens"]
                        daily_totals[date]["cost"] += day["cost"]
                        daily_totals[date]["users"].add(user_id)

            # Convert to list
            daily_breakdown = [
                {
                    "date": date,
                    "tokens": data["tokens"],
                    "cost": data["cost"],
                    "active_users": len(data["users"])
                }
                for date, data in sorted(daily_totals.items())
            ]

            return {
                "period_start": start_date.strftime("%Y-%m-%d"),
                "period_end": end_date.strftime("%Y-%m-%d"),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "total_requests": total_requests,
                "unique_users": len(active_users),
                "daily_breakdown": daily_breakdown
            }

        except Exception as e:
            logger.error(f"Error getting system usage: {e}")
            return {
                "total_tokens": 0,
                "total_cost": 0.0,
                "unique_users": 0,
                "daily_breakdown": []
            }

    def check_user_limit(
        self,
        user_id: str,
        tier: str = "free"
    ) -> Dict[str, any]:
        """
        Check if user has exceeded their tier's token limit.

        Args:
            user_id: Firebase UID
            tier: User's subscription tier

        Returns:
            Dict with limit status and usage info
        """
        # Get tier limits from config
        tier_limits = {
            "free": 100000,      # 100k tokens/month
            "pro": 1000000,      # 1M tokens/month
            "enterprise": -1     # Unlimited
        }

        limit = tier_limits.get(tier, 100000)

        # Get current month usage
        now = datetime.utcnow()
        first_day = now.replace(day=1)
        days_in_month = (now - first_day).days + 1

        usage = self.get_user_usage(user_id, days=days_in_month)

        exceeded = False
        if limit > 0:
            exceeded = usage["total_tokens"] >= limit

        return {
            "user_id": user_id,
            "tier": tier,
            "limit": limit,
            "used": usage["total_tokens"],
            "remaining": max(0, limit - usage["total_tokens"]) if limit > 0 else -1,
            "exceeded": exceeded,
            "percentage": (usage["total_tokens"] / limit * 100) if limit > 0 else 0
        }

    def get_top_users(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get top users by token consumption.

        Args:
            days: Number of days to look back
            limit: Number of top users to return

        Returns:
            List of users sorted by token usage
        """
        try:
            # Get all users with their total usage
            users = self.db.collection("users").stream()

            user_usage = []
            for user_doc in users:
                user_id = user_doc.id
                user_data = user_doc.to_dict()
                usage = self.get_user_usage(user_id, days)

                if usage["total_tokens"] > 0:
                    user_usage.append({
                        "user_id": user_id,
                        "email": user_data.get("email"),
                        "tokens": usage["total_tokens"],
                        "cost": usage["total_cost"],
                        "requests": usage["total_requests"]
                    })

            # Sort by tokens descending
            user_usage.sort(key=lambda x: x["tokens"], reverse=True)

            # Add ranking
            for i, user in enumerate(user_usage[:limit], 1):
                user["rank"] = i

            return user_usage[:limit]

        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []

    @staticmethod
    def _calculate_cost(tokens: int, model: str) -> float:
        """
        Calculate cost based on OpenAI pricing.

        Pricing as of Jan 2026:
        - gpt-4o: $5/1M input, $15/1M output (avg $10/1M)
        - gpt-4o-mini: $0.15/1M input, $0.60/1M output (avg $0.375/1M)
        - gpt-4-turbo: $10/1M input, $30/1M output (avg $20/1M)
        """
        pricing = {
            "gpt-4o": 10.0 / 1_000_000,
            "gpt-4o-mini": 0.375 / 1_000_000,
            "gpt-4-turbo": 20.0 / 1_000_000,
            "gpt-3.5-turbo": 0.5 / 1_000_000,
        }

        rate = pricing.get(model, 0.375 / 1_000_000)  # Default to gpt-4o-mini
        return tokens * rate


# Global instance
_tracker_instance = None


def get_token_tracker() -> TokenTracker:
    """Get global token tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = TokenTracker()
    return _tracker_instance

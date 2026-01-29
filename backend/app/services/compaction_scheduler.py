"""
Background Compaction Scheduler for Conversation Memory.

This service provides scheduled compaction of conversation history,
automatically summarizing and compacting old messages to optimize
storage and improve query performance.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CompactionScheduler:
    """Manages scheduled compaction of conversation memory across users."""
    
    _instance: Optional["CompactionScheduler"] = None
    _scheduler: Optional[BackgroundScheduler] = None
    _running_compactions: Dict[str, bool] = {}  # Track running jobs per user
    
    def __new__(cls):
        """Singleton pattern for scheduler."""
        if cls._instance is None:
            cls._instance = super(CompactionScheduler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the compaction scheduler."""
        self.scheduler = self._get_scheduler()
    
    @classmethod
    def _get_scheduler(cls) -> BackgroundScheduler:
        """Get or create the background scheduler."""
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler(daemon=True)
            logger.info("Initialized background scheduler for compaction")
        return cls._scheduler
    
    def start(self) -> None:
        """Start the background scheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Background compaction scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self) -> None:
        """Stop the background scheduler."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Background compaction scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
    
    def schedule_user_compaction(self, user_id: str, hour: int = 2, minute: int = 0) -> None:
        """
        Schedule daily compaction for a user at a specific time.
        
        Args:
            user_id: The user's Firebase UID
            hour: Hour of day to run compaction (0-23, default 2 AM)
            minute: Minute of hour to run compaction (default 0)
        """
        try:
            job_id = f"compaction_{user_id}"
            
            # Remove existing job if present
            existing = self.scheduler.get_job(job_id)
            if existing:
                self.scheduler.remove_job(job_id)
            
            # Add new job with daily trigger at specified time
            self.scheduler.add_job(
                self._compact_user_conversation,
                CronTrigger(hour=hour, minute=minute),
                id=job_id,
                args=[user_id],
                replace_existing=True,
                name=f"Compaction for {user_id}"
            )
            logger.info(f"Scheduled daily compaction for user {user_id} at {hour:02d}:{minute:02d}")
        
        except Exception as e:
            logger.error(f"Failed to schedule compaction for user {user_id}: {e}")
    
    def schedule_global_compaction(self, hour: int = 3, minute: int = 0) -> None:
        """
        Schedule global compaction for all users at a specific time.
        
        Args:
            hour: Hour of day to run compaction (0-23, default 3 AM)
            minute: Minute of hour to run compaction (default 0)
        """
        try:
            job_id = "global_compaction"
            
            # Remove existing job if present
            existing = self.scheduler.get_job(job_id)
            if existing:
                self.scheduler.remove_job(job_id)
            
            # Add new job with daily trigger
            self.scheduler.add_job(
                self._compact_all_conversations,
                CronTrigger(hour=hour, minute=minute),
                id=job_id,
                replace_existing=True,
                name="Global compaction for all users"
            )
            logger.info(f"Scheduled global compaction at {hour:02d}:{minute:02d}")
        
        except Exception as e:
            logger.error(f"Failed to schedule global compaction: {e}")
    
    @staticmethod
    def _compact_user_conversation(user_id: str) -> None:
        """
        Compact conversation history for a single user.
        
        Args:
            user_id: The user's Firebase UID
        """
        try:
            job_id = f"compaction_{user_id}"
            
            # Skip if already running
            if CompactionScheduler._running_compactions.get(job_id):
                logger.debug(f"Skipping compaction for {user_id} - already running")
                return
            
            CompactionScheduler._running_compactions[job_id] = True
            
            # Import here to avoid circular imports
            from app.services.conversation_memory import ConversationMemory
            
            start_time = datetime.now()
            logger.info(f"Starting scheduled compaction for user {user_id}")
            
            conv_mem = ConversationMemory(user_id)
            summary = conv_mem.summarize_and_compact(retain_last=30)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if summary:
                logger.info(
                    f"Compaction completed for user {user_id} in {elapsed:.2f}s - "
                    f"Summary: {summary[:100]}..."
                )
            else:
                logger.debug(f"No compaction needed for user {user_id}")
        
        except Exception as e:
            logger.error(f"Scheduled compaction failed for user {user_id}: {e}")
        
        finally:
            CompactionScheduler._running_compactions[f"compaction_{user_id}"] = False
    
    @staticmethod
    def _compact_all_conversations() -> None:
        """Compact conversation history for all users."""
        try:
            job_id = "global_compaction"
            
            # Skip if already running
            if CompactionScheduler._running_compactions.get(job_id):
                logger.debug("Skipping global compaction - already running")
                return
            
            CompactionScheduler._running_compactions[job_id] = True
            
            # Import here to avoid circular imports
            from app.firebase import get_firestore_client
            from app.services.conversation_memory import ConversationMemory
            
            db = get_firestore_client()
            start_time = datetime.now()
            
            logger.info("Starting global scheduled compaction for all users")
            
            # Get all users with conversations
            user_docs = db.collection("conversations").stream()
            compacted_count = 0
            
            for user_doc in user_docs:
                user_id = user_doc.id
                try:
                    conv_mem = ConversationMemory(user_id)
                    summary = conv_mem.summarize_and_compact(retain_last=30)
                    if summary:
                        compacted_count += 1
                        logger.debug(f"Compacted conversation for user {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to compact user {user_id}: {e}")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Global compaction completed in {elapsed:.2f}s - "
                f"Compacted {compacted_count} users"
            )
        
        except Exception as e:
            logger.error(f"Global scheduled compaction failed: {e}")
        
        finally:
            CompactionScheduler._running_compactions["global_compaction"] = False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, any]]:
        """
        Get status of a scheduled job.
        
        Args:
            job_id: The job ID
            
        Returns:
            Job information dict or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None
            
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "running": self._running_compactions.get(job_id, False),
            }
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None
    
    def list_jobs(self) -> list:
        """
        List all scheduled compaction jobs.
        
        Returns:
            List of job information dicts
        """
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "running": self._running_compactions.get(job.id, False),
                })
            return jobs
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []


# Global scheduler instance
_scheduler_instance: Optional[CompactionScheduler] = None


def get_compaction_scheduler() -> CompactionScheduler:
    """
    Get the global compaction scheduler instance.
    
    Returns:
        CompactionScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CompactionScheduler()
    return _scheduler_instance

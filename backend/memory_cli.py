#!/usr/bin/env python3
"""
Memory Management CLI Tool for TaskTrail.

Provides command-line utilities for managing conversation memory,
compaction, export, and diagnostics.

Usage:
    python memory_cli.py [command] [options]

Commands:
    stats [user-id]                    Show memory statistics for a user
    compact [user-id] [--retain N]     Manually compact user conversations
    export [user-id] [--format FORMAT] Export conversations
    prune [user-id] [--before DATE]    Delete conversations before a date
    diagnose [user-id]                 Run diagnostic checks
    cleanup-old [--days N]             Clean up old conversations (global)
    scheduler-status                   Check background scheduler status
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        from app.firebase import initialize_firebase
        initialize_firebase()
        logger.info("Firebase initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        sys.exit(1)


def cmd_stats(user_id: str) -> int:
    """Show memory statistics for a user."""
    try:
        from app.services.memory_analytics import MemoryAnalytics
        
        analytics = MemoryAnalytics(user_id)
        stats = analytics.get_memory_stats()
        
        print(f"\n=== Memory Statistics for {user_id} ===\n")
        print(json.dumps(stats, indent=2, default=str))
        
        return 0
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return 1


def cmd_compact(user_id: str, retain: int = 30) -> int:
    """Manually compact user conversations."""
    try:
        from app.services.conversation_memory import ConversationMemory
        
        print(f"\nCompacting conversations for {user_id}...")
        conv_mem = ConversationMemory(user_id)
        
        summary = conv_mem.summarize_and_compact(retain_last=retain)
        
        if summary:
            print(f"✓ Compaction successful")
            print(f"Summary: {summary[:200]}...")
            return 0
        else:
            print(f"! No compaction needed (fewer than {retain} messages)")
            return 0
    
    except Exception as e:
        logger.error(f"Error compacting: {e}")
        return 1


def cmd_export(user_id: str, format: str = "json") -> int:
    """Export conversations for a user."""
    try:
        from app.services.conversation_export import ConversationExporter
        
        if format not in ["json", "csv", "markdown"]:
            logger.error(f"Invalid format: {format}")
            return 1
        
        exporter = ConversationExporter(user_id)
        
        if format == "json":
            content = exporter.export_json(pretty=True)
            filename = f"conversations_{user_id}.json"
        elif format == "csv":
            content = exporter.export_csv()
            filename = f"conversations_{user_id}.csv"
        elif format == "markdown":
            content = exporter.export_markdown()
            filename = f"conversations_{user_id}.md"
        
        with open(filename, "w") as f:
            f.write(content)
        
        print(f"✓ Exported {format.upper()} to {filename}")
        return 0
    
    except Exception as e:
        logger.error(f"Error exporting: {e}")
        return 1


def cmd_prune(user_id: str, before_date: Optional[str] = None) -> int:
    """Delete conversations before a specified date."""
    try:
        from app.firebase import get_firestore_client
        
        if before_date:
            try:
                cutoff = datetime.fromisoformat(before_date)
            except ValueError:
                logger.error(f"Invalid date format: {before_date} (use YYYY-MM-DD)")
                return 1
        else:
            cutoff = datetime.now() - timedelta(days=30)
        
        db = get_firestore_client()
        conversations_ref = (
            db.collection("conversations")
            .document(user_id)
            .collection("messages")
        )
        
        # Query messages before cutoff date
        query = conversations_ref.where("timestamp", "<", cutoff).stream()
        deleted_count = 0
        
        for doc in query:
            doc.reference.delete()
            deleted_count += 1
        
        print(f"✓ Deleted {deleted_count} conversations before {cutoff.date()}")
        return 0
    
    except Exception as e:
        logger.error(f"Error pruning: {e}")
        return 1


def cmd_diagnose(user_id: str) -> int:
    """Run diagnostic checks on memory systems."""
    try:
        from app.services.memory_analytics import MemoryAnalytics
        from app.services.vector_memory import VectorMemory
        
        print(f"\n=== Diagnostics for {user_id} ===\n")
        
        # Check memory stats
        print("1. Checking conversation memory...")
        analytics = MemoryAnalytics(user_id)
        msg_count = analytics.get_message_count()
        summary_count = analytics.get_summary_count()
        print(f"   ✓ Messages: {msg_count}")
        print(f"   ✓ Summaries: {summary_count}")
        
        # Check vector memory
        print("\n2. Checking vector memory...")
        vec_mem = VectorMemory()
        vec_status = vec_mem.get_status()
        print(f"   ✓ Enabled: {vec_status['enabled']}")
        print(f"   ✓ Error count: {vec_status['error_count']}")
        if vec_status['last_error']:
            print(f"   ! Last error: {vec_status['last_error']}")
        
        # Check compaction health
        print("\n3. Checking compaction health...")
        if msg_count <= 50:
            print(f"   ✓ Compaction not needed (< 50 messages)")
        elif msg_count <= 100:
            print(f"   ⚠ Consider running compaction ({msg_count} messages)")
        else:
            print(f"   ! Compaction recommended ({msg_count} messages)")
        
        print("\n✓ Diagnostics complete\n")
        return 0
    
    except Exception as e:
        logger.error(f"Error running diagnostics: {e}")
        return 1


def cmd_cleanup_old(days: int = 90) -> int:
    """Clean up old conversations globally."""
    try:
        from app.firebase import get_firestore_client
        
        db = get_firestore_client()
        cutoff = datetime.now() - timedelta(days=days)
        
        print(f"\nCleaning up conversations older than {days} days ({cutoff.date()})...")
        
        # Get all users
        user_docs = db.collection("conversations").stream()
        total_deleted = 0
        
        for user_doc in user_docs:
            user_id = user_doc.id
            conversations_ref = (
                db.collection("conversations")
                .document(user_id)
                .collection("messages")
            )
            
            # Query messages before cutoff
            query = conversations_ref.where("timestamp", "<", cutoff).stream()
            user_deleted = 0
            
            for doc in query:
                doc.reference.delete()
                user_deleted += 1
            
            if user_deleted > 0:
                print(f"   {user_id}: {user_deleted} conversations deleted")
                total_deleted += user_deleted
        
        print(f"\n✓ Total deleted: {total_deleted} conversations")
        return 0
    
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
        return 1


def cmd_scheduler_status() -> int:
    """Check background scheduler status."""
    try:
        from app.services.compaction_scheduler import get_compaction_scheduler
        
        scheduler = get_compaction_scheduler()
        jobs = scheduler.list_jobs()
        
        print(f"\n=== Scheduler Status ===\n")
        print(f"Running: {scheduler.scheduler.running if scheduler.scheduler else 'Not initialized'}")
        print(f"Jobs: {len(jobs)}\n")
        
        for job in jobs:
            print(f"Job: {job['name']}")
            print(f"  ID: {job['id']}")
            print(f"  Next run: {job['next_run_time']}")
            print(f"  Running: {job['running']}")
            print()
        
        return 0
    
    except Exception as e:
        logger.error(f"Error checking scheduler: {e}")
        return 1


def main():
    """Parse arguments and dispatch commands."""
    parser = argparse.ArgumentParser(
        description="TaskTrail Memory Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show memory statistics")
    stats_parser.add_argument("user_id", help="User Firebase UID")
    
    # Compact command
    compact_parser = subparsers.add_parser("compact", help="Compact conversations")
    compact_parser.add_argument("user_id", help="User Firebase UID")
    compact_parser.add_argument("--retain", type=int, default=30, help="Messages to retain (default: 30)")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export conversations")
    export_parser.add_argument("user_id", help="User Firebase UID")
    export_parser.add_argument("--format", choices=["json", "csv", "markdown"], default="json", help="Export format")
    
    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Delete old conversations")
    prune_parser.add_argument("user_id", help="User Firebase UID")
    prune_parser.add_argument("--before", help="Delete before date (YYYY-MM-DD)")
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run diagnostics")
    diagnose_parser.add_argument("user_id", help="User Firebase UID")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup-old", help="Clean up old conversations")
    cleanup_parser.add_argument("--days", type=int, default=90, help="Delete older than N days (default: 90)")
    
    # Scheduler status command
    subparsers.add_parser("scheduler-status", help="Check scheduler status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize Firebase for all commands except help
    init_firebase()
    
    # Dispatch commands
    if args.command == "stats":
        return cmd_stats(args.user_id)
    elif args.command == "compact":
        return cmd_compact(args.user_id, args.retain)
    elif args.command == "export":
        return cmd_export(args.user_id, args.format)
    elif args.command == "prune":
        return cmd_prune(args.user_id, args.before)
    elif args.command == "diagnose":
        return cmd_diagnose(args.user_id)
    elif args.command == "cleanup-old":
        return cmd_cleanup_old(args.days)
    elif args.command == "scheduler-status":
        return cmd_scheduler_status()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

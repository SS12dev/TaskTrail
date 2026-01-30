"""
Tests for token usage tracking functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.token_tracker import TokenTracker, get_token_tracker


def test_calculate_cost():
    """Test token cost calculation for different models."""
    # Test GPT-4o-mini (cheapest)
    cost = TokenTracker._calculate_cost(1000, "gpt-4o-mini")
    assert cost == pytest.approx(0.000375, rel=1e-6)
    
    # Test GPT-4o
    cost = TokenTracker._calculate_cost(1000, "gpt-4o")
    assert cost == pytest.approx(0.01, rel=1e-6)
    
    # Test unknown model (should default to gpt-4o-mini)
    cost = TokenTracker._calculate_cost(1000, "unknown-model")
    assert cost == pytest.approx(0.000375, rel=1e-6)


@pytest.mark.asyncio
async def test_record_usage():
    """Test recording token usage."""
    with patch('app.services.token_tracker.get_firestore_client') as mock_db:
        # Setup mocks
        mock_db_client = MagicMock()
        mock_usage_ref = MagicMock()
        mock_user_ref = MagicMock()
        
        # Mock the collection chain
        mock_db_client.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_usage_ref
        mock_db_client.collection.return_value.document.return_value = mock_user_ref
        
        mock_db.return_value = mock_db_client
        
        tracker = TokenTracker()
        
        # Record usage
        tracker.record_usage(
            user_id="user123",
            tokens=1000,
            model="gpt-4o-mini",
            cost=0.375
        )
        
        # Verify set was called
        mock_usage_ref.set.assert_called_once()
        mock_user_ref.set.assert_called_once()


def test_get_user_usage():
    """Test retrieving user token usage."""
    with patch('app.services.token_tracker.get_firestore_client') as mock_db:
        # Setup mock data
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {
            "date": "2026-01-29",
            "openai_tokens": 1000,
            "requests_count": 5,
            "cost_estimate": 0.375,
            "models": {"gpt-4o-mini": 1000}
        }
        
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {
            "date": "2026-01-30",
            "openai_tokens": 2000,
            "requests_count": 10,
            "cost_estimate": 0.75,
            "models": {"gpt-4o-mini": 2000}
        }
        
        # Mock the query chain
        mock_query = MagicMock()
        mock_query.where.return_value.where.return_value.stream.return_value = [mock_doc1, mock_doc2]
        
        mock_collection = MagicMock()
        mock_collection.document.return_value.collection.return_value.document.return_value.collection.return_value = mock_query
        
        mock_db_client = MagicMock()
        mock_db_client.collection.return_value = mock_collection
        mock_db.return_value = mock_db_client
        
        tracker = TokenTracker()
        usage = tracker.get_user_usage("user123", days=30)
        
        assert usage["user_id"] == "user123"
        assert usage["total_tokens"] == 3000
        assert usage["total_cost"] == 1.125
        assert usage["total_requests"] == 15
        assert len(usage["daily_usage"]) == 2


def test_check_user_limit():
    """Test user limit checking."""
    with patch('app.services.token_tracker.get_firestore_client') as mock_db:
        with patch.object(TokenTracker, 'get_user_usage') as mock_get_usage:
            # Mock usage data
            mock_get_usage.return_value = {
                "total_tokens": 80000,
                "total_cost": 30.0
            }
            
            tracker = TokenTracker()
            
            # Test free tier (100k limit)
            limit_status = tracker.check_user_limit("user123", tier="free")
            assert limit_status["limit"] == 100000
            assert limit_status["used"] == 80000
            assert limit_status["remaining"] == 20000
            assert limit_status["exceeded"] == False
            assert limit_status["percentage"] == 80.0
            
            # Test exceeded limit
            mock_get_usage.return_value = {"total_tokens": 110000, "total_cost": 40.0}
            limit_status = tracker.check_user_limit("user123", tier="free")
            assert limit_status["exceeded"] == True
            
            # Test enterprise (unlimited)
            limit_status = tracker.check_user_limit("user123", tier="enterprise")
            assert limit_status["limit"] == -1
            assert limit_status["exceeded"] == False


def test_get_top_users():
    """Test getting top users by token consumption."""
    with patch('app.services.token_tracker.get_firestore_client') as mock_db:
        with patch.object(TokenTracker, 'get_user_usage') as mock_get_usage:
            # Mock user documents
            user1 = MagicMock()
            user1.id = "user1"
            user1.to_dict.return_value = {"email": "user1@test.com"}
            
            user2 = MagicMock()
            user2.id = "user2"
            user2.to_dict.return_value = {"email": "user2@test.com"}
            
            user3 = MagicMock()
            user3.id = "user3"
            user3.to_dict.return_value = {"email": "user3@test.com"}
            
            mock_collection = MagicMock()
            mock_collection.stream.return_value = [user1, user2, user3]
            
            mock_db_client = MagicMock()
            mock_db_client.collection.return_value = mock_collection
            mock_db.return_value = mock_db_client
            
            # Mock usage data (different amounts)
            def mock_usage_side_effect(user_id, days):
                usage_map = {
                    "user1": {"total_tokens": 50000, "total_cost": 18.75, "total_requests": 100},
                    "user2": {"total_tokens": 100000, "total_cost": 37.5, "total_requests": 200},
                    "user3": {"total_tokens": 75000, "total_cost": 28.125, "total_requests": 150}
                }
                return usage_map.get(user_id, {"total_tokens": 0, "total_cost": 0, "total_requests": 0})
            
            mock_get_usage.side_effect = mock_usage_side_effect
            
            tracker = TokenTracker()
            top_users = tracker.get_top_users(days=30, limit=3)
            
            # Should be sorted by tokens descending
            assert len(top_users) == 3
            assert top_users[0]["user_id"] == "user2"
            assert top_users[0]["tokens"] == 100000
            assert top_users[0]["rank"] == 1
            
            assert top_users[1]["user_id"] == "user3"
            assert top_users[1]["tokens"] == 75000
            assert top_users[1]["rank"] == 2
            
            assert top_users[2]["user_id"] == "user1"
            assert top_users[2]["tokens"] == 50000
            assert top_users[2]["rank"] == 3


def test_get_token_tracker_singleton():
    """Test that token tracker is a singleton."""
    tracker1 = get_token_tracker()
    tracker2 = get_token_tracker()
    assert tracker1 is tracker2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

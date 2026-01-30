# Admin Dashboard Guide

## Overview

The TaskTrail Admin Dashboard provides comprehensive monitoring, user management, and system configuration capabilities. This guide covers setup, features, and best practices.

## Table of Contents

1. [Setup & Access](#setup--access)
2. [User Management](#user-management)
3. [Analytics & Monitoring](#analytics--monitoring)
4. [Configuration Management](#configuration-management)
5. [Audit Logs](#audit-logs)
6. [Security Best Practices](#security-best-practices)

---

## Setup & Access

### Creating the First Super Admin

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run the super admin creation script:**
   ```bash
   python create_super_admin.py admin@yourdomain.com SecurePassword123!
   ```

3. **Verify creation:**
   - Check Firebase Console → Authentication
   - Check Firestore → `admins` collection

### Admin Roles

| Role | Permissions | Use Case |
|------|-------------|----------|
| **super_admin** | Full system access, configuration management, user deletion | System administrators |
| **admin** | User management, analytics viewing, limited config access | Daily operations |
| **support** | Read-only access to users and analytics | Customer support team |

### Accessing the Admin Dashboard

**Development:**
```
http://localhost:3001/admin
```

**Production:**
```
https://admin.yourdomain.com
```

---

## User Management

### Viewing All Users

**Endpoint:** `GET /api/v1/admin/users`

**Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)
- `search` (string): Search by email
- `tier` (string): Filter by subscription tier
- `suspended` (boolean): Filter by suspension status

**Example:**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/v1/admin/users?page=1&page_size=50&tier=free"
```

**Response:**
```json
{
  "users": [
    {
      "uid": "user123",
      "email": "user@example.com",
      "display_name": "John Doe",
      "task_count": 42,
      "project_count": 5,
      "total_tokens_used": 15000,
      "current_tier": "free",
      "is_suspended": false,
      "created_at": "2026-01-15T10:30:00Z",
      "last_login": "2026-01-30T14:22:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

### Viewing User Details

**Endpoint:** `GET /api/v1/admin/users/{user_id}`

Provides detailed information including:
- Complete profile data
- Token usage statistics
- Task and project counts
- Usage limit status
- Activity history

### Updating User Properties

**Endpoint:** `PATCH /api/v1/admin/users/{user_id}`

**Permissions:** `edit_users`

**Request Body:**
```json
{
  "is_suspended": false,
  "current_tier": "pro",
  "notes": "Upgraded to pro tier manually"
}
```

**Use Cases:**
- Suspend/unsuspend users
- Change subscription tiers
- Add admin notes

### Deleting Users

**Endpoint:** `DELETE /api/v1/admin/users/{user_id}`

**Permissions:** `super_admin` only

⚠️ **WARNING:** This permanently deletes:
- User's Firebase Auth account
- All tasks and projects
- Conversation history
- Usage data

**GDPR Compliance:** This endpoint can be used to fulfill "right to be forgotten" requests.

---

## Analytics & Monitoring

### System Overview

**Endpoint:** `GET /api/v1/admin/analytics/overview`

Provides high-level metrics:

```json
{
  "total_users": 1523,
  "active_users_7d": 842,
  "active_users_30d": 1205,
  "total_tasks": 45678,
  "total_projects": 8934,
  "total_conversations": 12456,
  "tokens_today": 125000,
  "tokens_this_month": 3800000,
  "cost_this_month": 1425.00,
  "avg_tokens_per_user": 2495.08
}
```

**Key Metrics:**
- **Active Users (7d/30d):** Users with activity in last 7/30 days
- **Tokens This Month:** OpenAI tokens consumed this calendar month
- **Cost This Month:** Estimated OpenAI costs (USD)
- **Avg Tokens Per User:** Average consumption across all users

### Top Users by Usage

**Endpoint:** `GET /api/v1/admin/analytics/top-users`

**Parameters:**
- `days` (int): Lookback period (default: 30)
- `limit` (int): Number of users to return (default: 10, max: 100)

**Example Response:**
```json
{
  "top_users": [
    {
      "user_id": "user789",
      "email": "poweruser@example.com",
      "tokens": 250000,
      "cost": 93.75,
      "requests": 500,
      "rank": 1
    }
  ],
  "period_days": 30
}
```

**Use Cases:**
- Identify heavy users for tier upgrades
- Monitor for potential abuse
- Capacity planning

### User Token Usage Details

**Endpoint:** `GET /api/v1/admin/users/{user_id}/usage`

**Parameters:**
- `days` (int): Lookback period (1-365)

**Response:**
```json
{
  "user_id": "user123",
  "period_start": "2026-01-01",
  "period_end": "2026-01-30",
  "total_tokens": 85000,
  "total_cost": 31.875,
  "daily_usage": [
    {
      "date": "2026-01-30",
      "tokens": 3500,
      "requests": 12,
      "cost": 1.3125,
      "models": {
        "gpt-4o-mini": 3500
      }
    }
  ]
}
```

---

## Configuration Management

### Viewing Current Configuration

**Endpoint:** `GET /api/v1/admin/config`

**Permissions:** `view_config`

Returns current system configuration:
```json
{
  "openai": {
    "api_key": "sk-proj-...hidden...",
    "default_model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "tiers": {
    "free": {
      "name": "free",
      "monthly_token_limit": 100000,
      "rate_limit_per_minute": 10,
      "features": ["basic_tasks", "ai_chat"],
      "price_per_month": 0.0
    },
    "pro": {
      "name": "pro",
      "monthly_token_limit": 1000000,
      "rate_limit_per_minute": 60,
      "features": ["basic_tasks", "ai_chat", "projects", "analytics"],
      "price_per_month": 19.99
    }
  },
  "maintenance_mode": false,
  "feature_flags": {
    "enable_a2a": true,
    "enable_vector_memory": true
  }
}
```

### Updating Configuration

**Endpoint:** `PATCH /api/v1/admin/config`

**Permissions:** `super_admin` only

**Request Body (partial update):**
```json
{
  "openai": {
    "api_key": "sk-proj-new-key-here",
    "default_model": "gpt-4o",
    "temperature": 0.8
  },
  "tiers": {
    "free": {
      "monthly_token_limit": 150000
    }
  },
  "maintenance_mode": false,
  "feature_flags": {
    "enable_new_feature": true
  }
}
```

### Configuration Best Practices

1. **API Key Rotation:**
   - Rotate OpenAI keys monthly
   - Update via admin panel
   - Old keys are automatically overwritten

2. **Tier Limits:**
   - Set conservative limits initially
   - Monitor usage before increasing
   - Consider cost implications

3. **Feature Flags:**
   - Use for gradual rollouts
   - Easy rollback if issues arise
   - No code deployment needed

4. **Maintenance Mode:**
   - Enable during critical updates
   - Returns 503 Service Unavailable to users
   - Admin endpoints remain accessible

---

## Audit Logs

### Viewing Audit Logs

**Endpoint:** `GET /api/v1/admin/audit-logs`

**Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `action` (string): Filter by action type
- `resource_type` (string): Filter by resource type

**Example Response:**
```json
{
  "logs": [
    {
      "id": "log123",
      "admin_id": "admin456",
      "admin_email": "admin@tasktrail.com",
      "action": "update_user",
      "resource_type": "user",
      "resource_id": "user789",
      "timestamp": "2026-01-30T15:22:10Z",
      "ip_address": "192.168.1.100",
      "details": {
        "is_suspended": true,
        "reason": "Terms violation"
      },
      "success": true
    }
  ],
  "total": 1234,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

### Tracked Actions

All admin actions are automatically logged:

| Action | Description |
|--------|-------------|
| `list_users` | Viewed user list |
| `view_user_detail` | Viewed user details |
| `view_user_usage` | Viewed user token usage |
| `update_user` | Modified user properties |
| `delete_user` | Deleted user account |
| `view_overview` | Viewed system overview |
| `view_top_users` | Viewed top users analytics |
| `view_config` | Viewed configuration |
| `update_config` | Modified configuration |
| `create_super_admin` | Created super admin account |

### Audit Log Retention

- **Default:** Logs retained for 1 year
- **Compliance:** Logs are immutable
- **Export:** Available for compliance audits

---

## Security Best Practices

### Password Requirements

For admin accounts:
- Minimum 12 characters (16+ recommended)
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- No personal information
- Rotate every 90 days

### Multi-Factor Authentication (MFA)

**Highly Recommended for Admins:**

1. Enable in Firebase Console:
   - Authentication → Settings → Multi-factor authentication
   
2. Enforce for all admins:
   ```javascript
   // In admin creation script
   firebase.auth().multiFactor.enroll(...)
   ```

### IP Whitelisting

For production environments:

1. **Add to firewall rules:**
   ```
   # Allow only from office IPs
   api.yourdomain.com/api/v1/admin/* - 203.0.113.0/24
   ```

2. **Application-level (future enhancement):**
   - Store allowed IPs in config
   - Check in admin middleware

### Session Management

- **Session timeout:** 30 minutes of inactivity
- **Max concurrent sessions:** 2 per admin
- **Force re-authentication:** For sensitive operations

### Access Control

1. **Principle of Least Privilege:**
   - Start with `support` role
   - Upgrade to `admin` only when needed
   - Reserve `super_admin` for infrastructure team

2. **Regular Audits:**
   - Review admin list monthly
   - Remove inactive admins
   - Audit permission changes

3. **Separation of Duties:**
   - Different admins for different regions
   - Read-only for most operations
   - Write access only for designated admins

### Monitoring Alerts

Set up alerts for:
- Failed login attempts (>3 in 5 minutes)
- User deletions
- Configuration changes
- Unusual usage spikes
- Tier limit exceeded

---

## API Reference Summary

### Authentication

```http
POST /api/v1/auth/verify
Authorization: Bearer <firebase_token>
```

All admin endpoints require:
- Valid Firebase JWT token
- Admin role in Firestore
- Active account status

### User Management

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/api/v1/admin/users` | `view_users` |
| GET | `/api/v1/admin/users/{id}` | `view_users` |
| GET | `/api/v1/admin/users/{id}/usage` | `view_users` |
| PATCH | `/api/v1/admin/users/{id}` | `edit_users` |
| DELETE | `/api/v1/admin/users/{id}` | `super_admin` |

### Analytics

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/api/v1/admin/analytics/overview` | `view_analytics` |
| GET | `/api/v1/admin/analytics/top-users` | `view_analytics` |

### Configuration

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/api/v1/admin/config` | `view_config` |
| PATCH | `/api/v1/admin/config` | `super_admin` |

### Audit Logs

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/api/v1/admin/audit-logs` | `view_audit_logs` |

---

## Troubleshooting

### Common Issues

#### 1. "Access denied. Admin privileges required."

**Cause:** User is not in the `admins` collection.

**Solution:**
```bash
python create_super_admin.py user@email.com password
```

#### 2. "Admin account is inactive."

**Cause:** Admin's `is_active` field is `false`.

**Solution:**
```javascript
// In Firebase Console → Firestore
admins/{admin_id}:
  is_active: true
```

#### 3. Token usage not showing

**Cause:** Token tracking not integrated in agent service.

**Solution:** See "Integrating Token Tracking" below.

### Integrating Token Tracking

Add to `app/agents/multi_agent_system.py`:

```python
from app.services.token_tracker import get_token_tracker

class MultiAgentSystem:
    async def process_message(self, state: AgentState) -> AgentState:
        # ... existing code ...
        
        # After OpenAI API call
        if response.usage:
            tracker = get_token_tracker()
            tracker.record_usage(
                user_id=state.get("user_context", {}).get("user_id"),
                tokens=response.usage.total_tokens,
                model=state.get("model", "gpt-4o-mini"),
                cost=None  # Auto-calculated
            )
        
        return result_state
```

---

## Future Enhancements

### Planned Features

1. **Real-time Dashboard:**
   - WebSocket updates
   - Live user activity feed
   - Real-time token consumption

2. **Advanced Analytics:**
   - Custom date ranges
   - Export to CSV/PDF
   - Scheduled reports

3. **Automated Actions:**
   - Auto-suspend on limit exceed
   - Automatic tier upgrades
   - Usage alerts

4. **Multi-tenant Support:**
   - Organization management
   - Per-org configuration
   - Cross-org analytics

### API Expansion

Future endpoints:
- `POST /api/v1/admin/users/{id}/reset-password`
- `POST /api/v1/admin/bulk-actions`
- `GET /api/v1/admin/reports/export`
- `POST /api/v1/admin/webhooks`

---

## Support

For admin dashboard issues:
- **Email:** admin-support@tasktrail.com
- **Documentation:** https://docs.tasktrail.com/admin
- **GitHub Issues:** https://github.com/tasktrail/tasktrail/issues

---

*Last Updated: January 30, 2026*

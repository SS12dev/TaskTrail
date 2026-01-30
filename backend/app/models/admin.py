"""
Admin-related Pydantic models for authentication and authorization.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime


# ============================================================================
# Admin User Models
# ============================================================================

class AdminRole(BaseModel):
    """Admin role definition."""
    role: Literal["super_admin", "admin", "support"] = Field(
        ..., 
        description="Admin role level"
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="Specific permissions granted to this role"
    )


class AdminUser(BaseModel):
    """Admin user information."""
    uid: str = Field(..., description="Admin Firebase UID")
    email: EmailStr = Field(..., description="Admin email address")
    role: Literal["super_admin", "admin", "support"] = Field(
        default="admin",
        description="Admin access level"
    )
    display_name: Optional[str] = Field(None, description="Admin display name")
    created_at: datetime = Field(..., description="When admin was created")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    is_active: bool = Field(default=True, description="Whether admin account is active")


class AdminLoginRequest(BaseModel):
    """Request model for admin login."""
    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., min_length=8, description="Admin password")


class AdminLoginResponse(BaseModel):
    """Response model for admin login."""
    token: str = Field(..., description="Firebase ID token")
    admin: AdminUser = Field(..., description="Admin user information")


# ============================================================================
# User Management Models
# ============================================================================

class UserSummary(BaseModel):
    """Summary of a user for admin listing."""
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    task_count: int = 0
    project_count: int = 0
    total_tokens_used: int = 0
    current_tier: str = "free"
    is_suspended: bool = False


class UserDetail(UserSummary):
    """Detailed user information for admin view."""
    email_verified: bool
    photo_url: Optional[str]
    metadata: dict = Field(default_factory=dict)
    usage_stats: dict = Field(default_factory=dict)


class UserListResponse(BaseModel):
    """Paginated list of users."""
    users: List[UserSummary]
    total: int
    page: int
    page_size: int
    has_next: bool


class UserUpdateRequest(BaseModel):
    """Request to update user properties."""
    is_suspended: Optional[bool] = None
    current_tier: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# Token Usage Models
# ============================================================================

class TokenUsageDay(BaseModel):
    """Token usage for a single day."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    openai_tokens: int = Field(default=0, description="OpenAI tokens consumed")
    requests_count: int = Field(default=0, description="Number of API requests")
    cost_estimate: float = Field(default=0.0, description="Estimated cost in USD")
    models_used: dict = Field(
        default_factory=dict,
        description="Breakdown by model: {model_name: token_count}"
    )


class TokenUsageResponse(BaseModel):
    """User token usage over a period."""
    user_id: str
    period_start: str
    period_end: str
    total_tokens: int
    total_cost: float
    daily_usage: List[TokenUsageDay]


class SystemUsageStats(BaseModel):
    """System-wide usage statistics."""
    total_tokens: int
    total_cost: float
    total_requests: int
    unique_users: int
    period_start: str
    period_end: str


# ============================================================================
# Analytics Models
# ============================================================================

class SystemOverview(BaseModel):
    """High-level system statistics."""
    total_users: int
    active_users_7d: int
    active_users_30d: int
    total_tasks: int
    total_projects: int
    total_conversations: int
    tokens_today: int
    tokens_this_month: int
    cost_this_month: float
    avg_tokens_per_user: float


class UserRanking(BaseModel):
    """User ranking by usage."""
    uid: str
    email: Optional[str]
    tokens_used: int
    cost: float
    rank: int


class UsageTrend(BaseModel):
    """Usage trend data point."""
    date: str
    tokens: int
    users: int
    cost: float


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics data."""
    overview: SystemOverview
    top_users: List[UserRanking]
    trends: List[UsageTrend]


# ============================================================================
# Configuration Models
# ============================================================================

class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(..., description="OpenAI API key (will be encrypted)")
    default_model: str = Field(default="gpt-4o-mini", description="Default model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=32000)
    fallback_model: Optional[str] = Field(None, description="Fallback if primary fails")


class TierConfig(BaseModel):
    """Subscription tier configuration."""
    name: str = Field(..., description="Tier name: free, pro, enterprise")
    monthly_token_limit: int = Field(..., description="Token limit per month")
    rate_limit_per_minute: int = Field(default=10, description="API calls per minute")
    features: List[str] = Field(default_factory=list, description="Enabled features")
    price_per_month: float = Field(default=0.0, description="Monthly price in USD")


class SystemConfig(BaseModel):
    """Complete system configuration."""
    openai: OpenAIConfig
    tiers: dict[str, TierConfig] = Field(
        default_factory=dict,
        description="Tier configurations keyed by tier name"
    )
    maintenance_mode: bool = Field(default=False, description="System maintenance mode")
    feature_flags: dict[str, bool] = Field(
        default_factory=dict,
        description="Feature toggles"
    )


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""
    openai: Optional[OpenAIConfig] = None
    tiers: Optional[dict[str, TierConfig]] = None
    maintenance_mode: Optional[bool] = None
    feature_flags: Optional[dict[str, bool]] = None


# ============================================================================
# Audit Log Models
# ============================================================================

class AuditLog(BaseModel):
    """Audit log entry."""
    id: str = Field(..., description="Log entry ID")
    admin_id: str = Field(..., description="Admin who performed action")
    admin_email: str = Field(..., description="Admin email")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of affected resource")
    timestamp: datetime = Field(..., description="When action occurred")
    ip_address: Optional[str] = Field(None, description="Admin IP address")
    details: dict = Field(default_factory=dict, description="Additional context")
    success: bool = Field(default=True, description="Whether action succeeded")


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""
    logs: List[AuditLog]
    total: int
    page: int
    page_size: int
    has_next: bool


# ============================================================================
# Action Response Models
# ============================================================================

class AdminActionResponse(BaseModel):
    """Response for admin actions."""
    success: bool
    message: str
    data: Optional[dict] = None

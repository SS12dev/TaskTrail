from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    """
    Response model for user information.

    This model is returned by authenticated endpoints to provide
    user details to the frontend.
    """
    uid: str
    email: Optional[str] = None
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None


class TokenVerifyResponse(BaseModel):
    """
    Response model for token verification endpoint.

    Used by /auth/verify to confirm token validity and return user info.
    """
    valid: bool
    user: UserResponse


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoints.

    Provides basic status information about the API.
    """
    status: str
    message: str
    environment: str

# In app/models.py

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# This will be our single, complete model for incoming chat requests.
class ChatRequest(BaseModel):
    # The user's message is the only truly required field to start a chat
    message: str = Field(..., min_length=2)

    # All other lead fields are optional, as they may be collected during the conversation
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Optional fields that the wizard or user might provide
    zip_code: Optional[str] = None
    quote_type: Optional[str] = None
    coverage_category: Optional[str] = None
    vehicle_year: Optional[str] = None
    home_type: Optional[str] = None

# The separate 'Lead' model is no longer needed for request validation,
# as its fields are now included in ChatRequest.
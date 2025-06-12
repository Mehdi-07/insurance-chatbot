# app/models.py
from pydantic import BaseModel, Field, EmailStr, ValidationError

# Model for incoming chat requests
class ChatRequest(BaseModel):
    """
    Represents the expected structure for incoming chat messages.
    - message: A string field, which must have a minimum length of 3 characters.
    """
    message: str = Field(..., min_length=3) # '...' means required, min_length is a validator

# Model for lead information (e.g., to be stored in the database)
class Lead(BaseModel):
    """
    Represents the structure for a new insurance lead.
    - name: Required string.
    - email: Optional email string (Pydantic validates email format).
    - zip: Optional string for zip code.
    - quote_type: Optional string (e.g., 'auto', 'home', 'life').
    - raw_message: Required string, to store the original user query.
    """
    name: str
    email: EmailStr | None = None # Use EmailStr for email format validation, | None for optional
    zip: str | None = None
    quote_type: str | None = None
    raw_message: str

# You can add more models here as your application grows
# For example, ChatResponse, or specific quote request models.
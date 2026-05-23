from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class BookingRatingBase(BaseModel):
    booking_id: int = Field(..., ge=1)
    rating_value: float = Field(..., ge=1.0, le=5.0)
    review_comment: Optional[str] = Field(None, max_length=1000)

    @field_validator("rating_value")
    @classmethod
    def validate_rating_step(cls, value: float):
        # enforce 0.5 increments: 1.0, 1.5, 2.0 ... 5.0
        if abs((value * 2) - round(value * 2)) > 1e-9:
            raise ValueError("rating_value must be in 0.5 increments")
        return value

    @field_validator("review_comment", mode="before")
    @classmethod
    def normalize_review_comment(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized if normalized else None
        return value


class BookingRatingCreate(BookingRatingBase):
    pass


class BookingRatingUpdate(BaseModel):
    rating_value: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_comment: Optional[str] = Field(None, max_length=1000)

    @field_validator("rating_value")
    @classmethod
    def validate_rating_step(cls, value: Optional[float]):
        if value is None:
            return value
        if abs((value * 2) - round(value * 2)) > 1e-9:
            raise ValueError("rating_value must be in 0.5 increments")
        return value

    @field_validator("review_comment", mode="before")
    @classmethod
    def normalize_review_comment(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized if normalized else None
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if self.rating_value is None and self.review_comment is None:
            raise ValueError("Provide at least one field to update")
        return self


class BookingRatingResponse(BookingRatingBase):
    id: UUID
    tenant_id: int
    created_on: datetime
    updated_on: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


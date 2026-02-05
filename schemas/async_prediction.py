from pydantic import BaseModel, Field
from datetime import datetime

class AsyncPredictRequest(BaseModel):
    item_id: int = Field(gt=0)

class AsyncPredictResponse(BaseModel):
    task_id: int = Field(gt=0)
    status:  str = Field(min_length=1, max_length=10)
    message: str = Field(min_length=1, max_length=256)

class ModerationResult(BaseModel):
    id:             int
    item_id:             int
    status:              str = Field(min_length=1, max_length=10)
    is_violation:        bool | None = None
    probability:         float | None = Field(None, ge=0.0, le=1.0)
    error_message:       str | None = None
    created_at:          datetime | None = None
    updated_at:          datetime | None = None
    processed_at:        str | None = None
    retry_count:         int = Field(0, ge=0)
    max_retries:         int = Field(3, ge=1)
from pydantic import BaseModel, Field
from typing import Optional

class PredictionRequest(BaseModel):
    seller_id:          int = Field(gt=0)
    is_verified_seller: bool
    item_id:            int = Field(gt=0)
    name:               str = Field(min_length=1, max_length=256)
    description:        str = Field(min_length=0, max_length=2**14)
    category:           int = Field(gt=0)
    images_qty:         int = Field(ge=0)


class PredictionResponse(BaseModel):
    is_violation: bool  = Field()
    probability:  float = Field(ge=0.0, le=1.0)
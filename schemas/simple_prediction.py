from pydantic import BaseModel, Field

class User(BaseModel):
    seller_id:          int = Field(gt=0)
    is_verified_seller: bool
    
class Advertisement(BaseModel):
    item_id:            int = Field(gt=0)
    seller_id:          int = Field(gt=0)
    name:               str = Field(min_length=1, max_length=256)
    description:        str = Field(min_length=0, max_length=2**14)
    category:           int = Field(gt=0)
    images_qty:         int = Field(ge=0)

class SimplePredictRequest(BaseModel):
    item_id: int = Field(gt=0)

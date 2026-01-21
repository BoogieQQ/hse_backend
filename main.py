from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI()

class PredictionRequest(BaseModel):
    seller_id:          int = Field(gt=0)
    is_verified_seller: bool
    item_id:            int = Field(gt=0)
    name:               str = Field(min_length=1, max_length=256)
    description:        str = Field(min_length=0, max_length=2**14)
    category:           int = Field(gt=0)
    images_qty:         int = Field(ge=0)
    
@app.get("/")
async def root():
    return {'message': 'Hello World'}

@app.post("/predict")
async def predict(request: PredictionRequest) -> bool:
    """
    Return:
        False - если объявление не содержит нарушений,
        True - иначе
    """
    try:
        return not(request.is_verified_seller or request.images_qty != 0) 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Что-то пошло не так: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
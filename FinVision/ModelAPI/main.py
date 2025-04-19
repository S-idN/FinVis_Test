from fastapi import FastAPI
from pydantic import BaseModel
from simplified_recommender import SimplifiedProductRecommender

app = FastAPI()
recommender = SimplifiedProductRecommender("category.csv")
recommender.train_models()

class ProductRequest(BaseModel):
    product_id: str
    method: str = "basic"

@app.get("/")
def home():
    return {"status": "Recommender service is up"}

@app.post("/recommend")
def recommend_product(request: ProductRequest):
    result = recommender.scan_product(request.product_id, method=request.method)
    return result

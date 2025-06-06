from fastapi import APIRouter, Query
from fastapi import APIRouter
from fastapi import HTTPException
from app.services.db import artifacts
from typing import List
from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/search")
async def search_heritage_data(request: QueryRequest):
    try:
        results = []
        for doc in artifacts.find({"$text": {"$search": request.query}}).limit(10):
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

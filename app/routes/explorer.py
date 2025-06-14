from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.services.db import artifacts
from app.services.vertexai import embed_query  # <--- Adjust the import path if needed
import re

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    k: int = 20  # default number of results

def combined_score(doc, query):
    # Prefer higher vector score and title match
    vector_score = doc.get("vector_score", 0)
    text_score = doc.get("text_score", 0)
    title = doc.get("title", "").lower()
    query_keywords = [kw.lower() for kw in re.findall(r'\w+', query)]
    title_match_bonus = sum(1 for kw in query_keywords if kw in title) * 0.2
    return vector_score + text_score + title_match_bonus

@router.post("/search")
async def search_heritage_data(request: QueryRequest):
    try:
        embedding = embed_query(request.query)
        k = getattr(request, "k", 20)

        # --- 1. Vector search ---
        vector_pipeline = [
            {
                "$vectorSearch": {
                    "index": "embedding_knn",
                    "queryVector": embedding,
                    "path": "embedding",
                    "numCandidates": 100,
                    "k": k,
                    "limit": k
                }
            },
            {
                "$project": {
                    "title": 1,
                    "description": 1,
                    "region": 1,
                    "image_url": 1,
                    "themes": 1,
                    "period": 1,
                    "reference_link": 1,
                    "vector_score": { "$meta": "vectorSearchScore" }
                }
            }
        ]
        vector_results = list(artifacts.aggregate(vector_pipeline))

        # --- 2. Text search ---
        text_pipeline = [
            {
                "$search": {
                    "text": {
                        "query": request.query,
                        "path": ["title", "description", "region"]
                    }
                }
            },
            {
                "$project": {
                    "title": 1,
                    "description": 1,
                    "region": 1,
                    "image_url": 1,
                    "themes": 1,
                    "period": 1,
                    "reference_link": 1,
                    "text_score": { "$meta": "searchScore" }
                }
            },
            { "$limit": k }
        ]
        text_results = list(artifacts.aggregate(text_pipeline))

        # --- 3. Combine and deduplicate (by _id) ---
        docs: Dict[str, dict] = {}
        for doc in vector_results:
            doc["_id"] = str(doc["_id"])
            docs[doc["_id"]] = doc
        for doc in text_results:
            doc["_id"] = str(doc["_id"])
            # Merge/keep best scores if present in both
            if doc["_id"] in docs:
                docs[doc["_id"]]["text_score"] = doc.get("text_score", 0)
            else:
                doc["vector_score"] = 0  # ensure both scores exist
                docs[doc["_id"]] = doc

        # --- 4. Rerank by combined score ---
        combined_results = sorted(
            docs.values(),
            key=lambda d: combined_score(d, request.query),
            reverse=True
        )[:k]

        return {"results": combined_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
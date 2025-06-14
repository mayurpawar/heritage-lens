# ai_loader/batch_embed_local.py

import os
from tqdm import tqdm
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# --- MongoDB from env vars ---
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB_NAME")
COLLECTION = os.environ.get("MONGO_COLLECTION")

# --- Config ---
BATCH_SIZE = 32
SKIP_IF_PRESENT = True  # Set to False to always re-embed

# --- Load Model ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLLECTION]

# --- Get all docs (that need embedding, if desired) ---
query = {} if not SKIP_IF_PRESENT else {"embedding": {"$exists": False}}
total = coll.count_documents(query)
cursor = coll.find(query)

print(f"Embedding {total} artifacts...")

for doc in tqdm(cursor, total=total):
    text = " ".join([
        doc.get("title", ""),
        doc.get("description", ""),
        doc.get("region", "")
    ])
    embedding = model.encode(text).tolist()
    coll.update_one(
        {"_id": doc["_id"]},
        {"$set": {"embedding": embedding}}
    )

print("Batch embedding complete. MongoDB search/text index remains unchanged.")
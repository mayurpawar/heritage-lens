import os
from tqdm import tqdm
from pymongo import MongoClient
from vertexai.preview.language_models import TextEmbeddingModel

# --- MongoDB from env vars ---
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB_NAME")
COLLECTION = os.environ.get("MONGO_COLLECTION")

# --- CONFIG ---
EMBED_MODEL = "text-embedding-005"   
BATCH_SIZE = 100
SKIP_IF_PRESENT = True

def vertex_embed(texts):
    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL)
    results = model.get_embeddings(texts)
    # Each result has .values attribute (a list of floats)
    return [r.values for r in results]

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLLECTION]

query = {} if not SKIP_IF_PRESENT else {"embedding": {"$exists": False}}
total = coll.count_documents(query)
cursor = coll.find(query)

batch = []
docs = []
for doc in tqdm(cursor, total=total):
    text = " ".join([
        doc.get("title", ""),
        doc.get("description", ""),
        doc.get("region", "")
    ])
    batch.append(text)
    docs.append(doc)

    if len(batch) == BATCH_SIZE:
        embeddings = vertex_embed(batch)
        for d, emb in zip(docs, embeddings):
            coll.update_one({"_id": d["_id"]}, {"$set": {"embedding": emb}})
        batch = []
        docs = []

# Do remaining docs
if batch:
    embeddings = vertex_embed(batch)
    for d, emb in zip(docs, embeddings):
        coll.update_one({"_id": d["_id"]}, {"$set": {"embedding": emb}})

print("Batch embedding complete using Vertex AI.")
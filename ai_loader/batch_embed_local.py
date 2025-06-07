# ai_loader/batch_embed_local.py

import json, sys, os, shutil
from tqdm import tqdm
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# --- ARGUMENT CHECK ---
if len(sys.argv) != 2:
    print("Usage: python batch_embed_local.py <data_file_name>")
    sys.exit(1)

file_name = sys.argv[1]
data_path = os.path.join(os.path.dirname(__file__), "../data", file_name)
archive_path = os.path.join(os.path.dirname(__file__), "../archive", file_name)

if not os.path.exists(data_path):
    print(f"Error: Data file '{file_name}' does not exist in ../data/.")
    sys.exit(1)

# --- Load Model ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Load Data ---
with open(data_path, "r") as f:
    artifacts = json.load(f)

# --- MongoDB from env vars ---
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB_NAME")
COLLECTION = os.environ.get("MONGO_COLLECTION")

if not all([MONGO_URI, DB_NAME, COLLECTION]):
    print("Error: MONGO_URI, MONGO_DB_NAME, and MONGO_COLLECTION env vars must be set.")
    sys.exit(1)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLLECTION]

# --- Process & Insert ---
for art in tqdm(artifacts, desc="Uploading Artifacts"):
    text = " ".join([art.get("title", ""), art.get("description", "")])
    embedding = model.encode(text).tolist()
    art["embedding"] = embedding
    coll.replace_one({"_id": art["_id"]}, art, upsert=True)

print("Batch import and embedding complete!")

# --- Move File to Archive (unless sample_artifacts.json) ---
if file_name != "sample_artifacts.json":
    archive_dir = os.path.dirname(archive_path)
    os.makedirs(archive_dir, exist_ok=True)
    shutil.move(data_path, archive_path)
    print(f"Moved {file_name} to archive.")
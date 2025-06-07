import os, sys, csv, json, ast
from pymongo import MongoClient

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
    
# --- MongoDB from env vars ---
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB_NAME")
COLLECTION = os.environ.get("MONGO_COLLECTION")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLLECTION]
    
ext = os.path.splitext(file_name)[1].lower()
if ext == ".json":
    # Load data
    with open(data_path, "r") as f:
        artifacts = json.load(f)
        
    # Optionally: Prevent duplicate insertion using unique field
    for art in artifacts:
        coll.update_one(
            {"title": art["title"], "region": art.get("region", "")},  # Or use another unique field
            {"$setOnInsert": art},
            upsert=True
        )

    print(f"Inserted or updated {len(artifacts)} artifacts.")
    
elif ext == ".csv":
    with open(data_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip().lower().replace('"', '') for h in reader.fieldnames]
        count = 0
        for row in reader:
            row = {k.replace('"','').strip(): v.replace('"','').strip() for k, v in row.items()}
            title = row.get("title") or row.get("\ufefftitle") or ""
            artifact = {
                "title": title,
                "region": row.get("region", ""),
                "period": row.get("period", ""),
                "description": row.get("description", ""),
                "image_url": row.get("image_url", ""),
                "themes": [t.strip() for t in row.get("themes", "").split(",") if t.strip()],
            }
            coll.update_one(
                {"title": artifact["title"], "region": artifact["region"]},
                {"$setOnInsert": artifact},
                upsert=True
            )
            count += 1

    print(f"Upserted {count} records into MongoDB collection!") 

else:
    print("Error: Unsupported file type. Please supply a .csv or .json file.")   
    
# --- Move File to Archive (unless sample_artifacts.json) ---
if file_name not in ("sample_artifacts.json", "sample_artifacts.csv"):
    archive_dir = os.path.dirname(archive_path)
    os.makedirs(archive_dir, exist_ok=True)
    shutil.move(data_path, archive_path)
    print(f"Moved {file_name} to archive.")    
else:
    print(f"Did not archive sample file: {file_name}")
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.environ.get("MONGO_DB_NAME")
COLLECTION = os.environ.get("MONGO_COLLECTION")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile='/etc/ssl/certs/ca-certificates.crt',
    serverSelectionTimeoutMS=30000
)
db = client[DB_NAME]
artifacts = db[COLLECTION]

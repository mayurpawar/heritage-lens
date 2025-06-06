import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile='/etc/ssl/certs/ca-certificates.crt',
    serverSelectionTimeoutMS=30000
)
db = client["heritage_lens"]
artifacts = db["artifacts"]

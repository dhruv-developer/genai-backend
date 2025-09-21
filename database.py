# import os
# from pymongo import MongoClient
# from dotenv import load_dotenv

# # Load environment variables from .env
# load_dotenv()

# MONGO_URI = os.getenv("MONGO_URI")
# DB_NAME = os.getenv("DB_NAME")

# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]

import logging
from pymongo import MongoClient
from settings import settings

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]

logger.info(f"Connected to MongoDB at {settings.MONGO_URI}, DB: {settings.MONGO_DB}")

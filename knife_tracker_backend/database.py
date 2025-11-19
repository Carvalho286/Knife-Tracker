from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)
db = client["knife_tracker"]

tokens_collection = db["device_tokens"]
assets_collection = db["seen_assets"]


async def create_indexes():
    # O _id já é UNIQUE automaticamente, não precisas de índice extra
    await tokens_collection.create_index("expoToken")  # não precisa UNIQUE

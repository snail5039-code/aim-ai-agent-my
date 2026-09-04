import os
import asyncio
import httpx
from google import genai
from dotenv import load_dotenv

load_dotenv()

TMDB_TOKEN = os.getenv("token")

BASE_URL = "https://api.themoviedb.org/3"

headers = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}

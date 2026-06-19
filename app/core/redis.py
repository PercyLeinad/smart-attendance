import redis
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("host")
password = os.getenv("password")
port = os.getenv("port")

redis_client = redis.Redis(
    host=host,
    port=port,
    password=password,
    decode_responses=True
)
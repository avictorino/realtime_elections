import logging
import os
from celery import Celery
import redis
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level="INFO")
logger = logging.getLogger("geo_redis")

flask_app = Flask(__name__)
celery_app = Celery(broker=os.getenv(f"REDIS_BROKER_URL"))
redis_mayors = redis.from_url(os.getenv(f"REDIS_MAYORS_URL"))
redis_cities = redis.from_url(os.getenv(f"REDIS_CITIES_URL"))

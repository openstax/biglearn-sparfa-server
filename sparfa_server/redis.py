from redis import StrictRedis

from .config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

redis = StrictRedis(host=REDIS_HOST, post=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB)

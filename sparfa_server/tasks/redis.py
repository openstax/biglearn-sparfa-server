from redis import StrictRedis

from ..config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB)

from django.conf import settings
import redis


def get_config(item_name):
    try:
        redis_con = redis.StrictRedis(host=settings.REDIS_HOST,
                                      port=settings.REDIS_PORT,
                                      db=settings.REDIS_DB)
        value = redis_con.get(item_name)
    except Exception as exc:
        print exc
        return None

    if value and len(value):
        return value

    return None

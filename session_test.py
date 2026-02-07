import redis
import json

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

# تست اتصال
print("اتصال به Redis:", r.ping())

# تست ذخیره داده
r.set('test_key', 'test_value')
print("داده تست:", r.get('test_key'))

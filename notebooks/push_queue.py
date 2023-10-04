import redis

queue_name = 'my_queue'
redis_client = redis.Redis(host='localhost', port=6379, db=0)

redis_client.rpush(queue_name, 'Dustin')
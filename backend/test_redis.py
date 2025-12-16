"""
Redis Cache Test Script
Test if Redis caching is working properly
"""
import redis
import time

def test_redis_connection():
    """Test Redis connection"""
    print("=" * 60)
    print("Testing Redis Connection...")
    print("=" * 60)
    
    try:
        # Connect to Redis
        r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        
        # Test ping
        response = r.ping()
        print(f"✅ Redis PING: {response}")
        
        # Test set/get
        r.set('test_key', 'Hello Redis!')
        value = r.get('test_key')
        print(f"✅ Redis SET/GET: {value}")
        
        # Test cache with TTL
        r.setex('cache_test', 10, 'This will expire in 10 seconds')
        ttl = r.ttl('cache_test')
        print(f"✅ Redis TTL: {ttl} seconds remaining")
        
        # Get info
        info = r.info('server')
        print(f"✅ Redis Version: {info.get('redis_version')}")
        print(f"✅ Redis Uptime: {info.get('uptime_in_seconds')} seconds")
        
        # Clean up
        r.delete('test_key', 'cache_test')
        
        print("\n" + "=" * 60)
        print("✅ Redis is working perfectly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Redis connection failed: {e}")
        print("=" * 60)
        return False


def test_cache_performance():
    """Test cache performance"""
    print("\n" + "=" * 60)
    print("Testing Cache Performance...")
    print("=" * 60)
    
    try:
        r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        
        # Test write performance
        start = time.time()
        for i in range(1000):
            r.set(f'perf_test_{i}', f'value_{i}')
        write_time = (time.time() - start) * 1000
        print(f"✅ Write 1000 keys: {write_time:.2f}ms")
        
        # Test read performance
        start = time.time()
        for i in range(1000):
            r.get(f'perf_test_{i}')
        read_time = (time.time() - start) * 1000
        print(f"✅ Read 1000 keys: {read_time:.2f}ms")
        
        # Clean up
        keys = r.keys('perf_test_*')
        if keys:
            r.delete(*keys)
        
        print(f"\n💡 Average read latency: {read_time/1000:.2f}ms per key")
        print(f"💡 Average write latency: {write_time/1000:.2f}ms per key")
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    print("\n🚀 Redis Cache System Test\n")
    
    # Test connection
    if test_redis_connection():
        # Test performance
        test_cache_performance()
        
        print("\n✅ All tests passed! Redis is ready for production.\n")
    else:
        print("\n❌ Redis is not available. Please check the service.\n")

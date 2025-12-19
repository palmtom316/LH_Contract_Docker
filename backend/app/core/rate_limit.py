"""
Safe Mode Rate Limit
Completely mocking the limiter to remove slowapi dependency.
"""

class MockLimiter:
    def limit(self, limit_value):
        def decorator(func):
            return func
        return decorator

limiter = MockLimiter()

def setup_rate_limiting(app):
    pass

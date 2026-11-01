# Owner: Person A
"""
Throttling configuration for high-concurrency Tatkal booking endpoints.
Prevents bots and aggressive spamming during the critical 10:00 AM / 11:00 AM Tatkal window.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class TatkalBurstThrottle(UserRateThrottle):
    scope = "tatkal_burst"

class TatkalSustainedThrottle(UserRateThrottle):
    scope = "tatkal_sustained"

class TatkalAnonThrottle(AnonRateThrottle):
    scope = "anon"

"""
Rate limiting middleware using slowapi.
Limits are per client IP. Behind Cloudflare Tunnel the real IP comes
via X-Forwarded-For; slowapi reads this automatically.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Shared limit strings — adjust these as needed.
ANSWER_LIMIT = "10/minute"
INFO_LIMIT = "30/minute"

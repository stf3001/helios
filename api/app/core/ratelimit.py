"""Rate limiting (doc 10 sécurité) — protège l'auth (brute force) et le chat (abus)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Clé = adresse IP du client. En prod derrière un proxy, s'assurer que X-Forwarded-For est fiable.
limiter = Limiter(key_func=get_remote_address, default_limits=[])

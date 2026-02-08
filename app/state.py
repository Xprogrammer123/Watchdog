from typing import Dict
from .models import ScammerStatus

# In-memory store for scammer status
scammer_db: Dict[str, ScammerStatus] = {}

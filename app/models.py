from pydantic import BaseModel
from typing import List, Optional

class VerificationRequest(BaseModel):
    user_wallet: str
    scammer_wallet: str
    transaction_signature: str

class VerificationResponse(BaseModel):
    verified: bool
    amount: float
    token: str = "SOL"
    mint: Optional[str] = None
    timestamp: int
    message: str

class MonitorRequest(BaseModel):
    scammer_wallet: str

class ScammerStatus(BaseModel):
    address: str
    balance: float
    status: str
    risk_label: str
    latest_activity: List[str]

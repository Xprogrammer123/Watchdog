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

class TokenInfo(BaseModel):
    mint: str
    amount: float
    decimals: int

class AccountInfo(BaseModel):
    sol_balance: float
    tokens: List[TokenInfo]

class ScammerStatus(BaseModel):
    address: str
    balance: float # Kept for backward compatibility, but should sync with account_info.sol_balance
    status: str
    risk_label: str
    latest_activity: List[str] # Signatures
    recent_logs: List[str] = [] # Human readable alerts
    account_info: Optional[AccountInfo] = None

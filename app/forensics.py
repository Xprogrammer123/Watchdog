import json
import os
from solders.signature import Signature
from solana.rpc.api import Client

# Load Risk Database from JSON
# Assuming risk_data.json is in ../data/ relative to this file
RISK_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "risk_data.json")

def load_risk_db():
    try:
        with open(RISK_DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load risk data: {e}")
        return {}

KNOWN_EXCHANGES = load_risk_db()

def get_risk_label(address: str) -> str:
    """
    Checks if an address is a known high-risk exchange or entity.
    """
    for name, addr in KNOWN_EXCHANGES.items():
        if addr == address:
            return f"High Risk: {name}"
    return "Unknown"

def verify_receipt(signature: str, rpc_url: str = "https://api.mainnet-beta.solana.com") -> dict:
    """
    Verifies if a transaction receipt exists and is confirmed.
    Returns a dictionary with status and details.
    """
    client = Client(rpc_url)
    try:
        sig = Signature.from_string(signature)
        # Fetch transaction details with max_supported_transaction_version=0
        tx = client.get_transaction(sig, max_supported_transaction_version=0)
        
        if not tx.value:
            return {"verified": False, "message": "Transaction not found on-chain"}
            
        meta = tx.value.transaction.meta
        if meta.err:
             return {"verified": False, "message": "Transaction failed on-chain"}
             
        return {
            "verified": True, 
            "slot": tx.value.slot,
            "block_time": tx.value.block_time,
            "message": "Transaction receipt verified and confirmed."
        }
        
    except Exception as e:
        return {"verified": False, "message": f"Verification error: {str(e)}"}

import requests
import sys

# ==========================================
# 🚨 ENTER YOUR REAL DATA HERE
# ==========================================
# The scammer's wallet address you want to monitor
SCAMMER_WALLET = "ENTER_SCAMMER_WALLET_HERE" 

# Your wallet address (sender)
USER_WALLET = "ENTER_YOUR_WALLET_HERE" 

# The transaction signature (TxID) of the funds sent to scammer
TRANSACTION_SIGNATURE = "ENTER_TRANSACTION_SIGNATURE_HERE" 
# ==========================================

def test_verify():
    print(f"\n[1] Testing Verification for Transaction: {TRANSACTION_SIGNATURE}")
    url = "http://localhost:8000/api/v1/verify"
    payload = {
        "user_wallet": USER_WALLET,
        "scammer_wallet": SCAMMER_WALLET,
        "transaction_signature": TRANSACTION_SIGNATURE
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data['verified']:
                print("✅ VERIFIED! The blockchain confirms this transaction.")
                print(f"   Amount: {data['amount']} SOL")
            else:
                print("❌ NOT VERIFIED.")
                print(f"   Reason: {data['message']}")
        else:
            print(f"❌ Server Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_monitor():
    print(f"\n[2] Starting Watchdog for Scammer: {SCAMMER_WALLET}")
    url = "http://localhost:8000/api/v1/monitor"
    payload = {"scammer_wallet": SCAMMER_WALLET}
    
    try:
        response = requests.post(url, json=payload)
        print(f"Watchdog Status: {response.json()}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    if "ENTER_" in SCAMMER_WALLET:
        print("⚠️  PLEASE EDIT THIS FILE AND ADD REAL DATA FIRST!")
        sys.exit(1)
        
    test_verify()
    test_monitor()

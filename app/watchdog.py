import asyncio
import websockets
import json
from solders.pubkey import Pubkey
from solana.rpc.api import Client

import os

# Load Risk Database from JSON
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
   
    for name, addr in KNOWN_EXCHANGES.items():
        if addr == address:
            return f"High Risk: {name}"
    return "Unknown"

async def trigger_whatsapp_alert(message: str):
  
    print(f"[WhatsApp Alert]: {message}")
   

class Watchdog:
    def __init__(self):
        self.active_monitors = set()
        self.ws_url = "wss://api.mainnet-beta.solana.com"

    async def start_monitoring(self, address: str):
        if address in self.active_monitors:
            print(f"Already monitoring {address}")
            return
        
        self.active_monitors.add(address)
        print(f"Started monitoring {address}")
        
        async with websockets.connect(self.ws_url) as websocket:
     
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": [address]},
                    {"commitment": "confirmed"}
                ]
            }
            await websocket.send(json.dumps(subscription_request))
            
            try:
                while address in self.active_monitors:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "method" in data and data["method"] == "logsNotification":
                        # Transaction detected
                        logs = data["params"]["result"]["value"]["logs"]
                        signature = data["params"]["result"]["value"]["signature"]
                        

                        # Analyze transaction
                        print(f"Activity detected on {address}! Signature: {signature}")
                        
                        # Update status in DB
                        from .state import scammer_db
                        if address in scammer_db:
                            scammer_db[address].latest_activity.append(signature)
                        
                        client = Client("https://api.mainnet-beta.solana.com")
                        try:
                            # We allow some time for propagation or retry
                            tx = client.get_transaction(Signature.from_string(signature), max_supported_transaction_version=0)
                            if tx.value:
                                # Simple logic: find where money went
                                # For now, we just look at the account keys and assume the second one used is destination (very naive)
                                # In reality, parsing logs or instructions is needed
                                account_keys = tx.value.transaction.transaction.message.account_keys
                                dest_address = str(account_keys[1]) if len(account_keys) > 1 else "Unknown"
                                
                                risk_label = get_risk_label(dest_address)
                                alert_msg = f"Funds moved from {address} to {dest_address}. Risk: {risk_label}. Sig: {signature}"
                                await trigger_whatsapp_alert(alert_msg)
                                
                                # Update DB with risk label
                                if address in scammer_db:
                                    scammer_db[address].risk_label = risk_label
                                    scammer_db[address].status = "Active Movement"

                        except Exception as tx_err:
                            print(f"Could not fetch tx details: {tx_err}")
                        
            except Exception as e:
                print(f"Error monitoring {address}: {e}")
            finally:
                self.active_monitors.remove(address)
                print(f"Stopped monitoring {address}")

    def stop_monitoring(self, address: str):
        if address in self.active_monitors:
            self.active_monitors.remove(address)

watchdog_service = Watchdog()

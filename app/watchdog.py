import asyncio
import websockets
import json
from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
import os
import traceback
from typing import Optional, List

from .models import ScammerStatus, TokenInfo, AccountInfo
from .state import scammer_db

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
    # In a real app, you would make a POST request to the WhatsApp API here

class Watchdog:
    def __init__(self):
        self.active_monitors = set()
        self.ws_url = "wss://api.mainnet-beta.solana.com"
        self.rpc_client = Client("https://api.mainnet-beta.solana.com")
        self.token_program_id = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

    def get_account_details(self, address: str) -> AccountInfo:
        try:
            pubkey = Pubkey.from_string(address)
            
            # 1. Get SOL Balance
            balance_resp = self.rpc_client.get_balance(pubkey)
            sol_balance = balance_resp.value / 1e9
            
            # 2. Get Token Accounts (Parsed)
            # encoding='jsonParsed' is supported by standard RPC, checking python wrapper support
            # logic: we try to fetch and parse manually if needed, but jsonParsed is best.
            opts = TokenAccountOpts(program_id=self.token_program_id, encoding="jsonParsed")
            resp = self.rpc_client.get_token_accounts_by_owner(pubkey, opts)
            
            tokens: List[TokenInfo] = []
            if resp.value:
                for item in resp.value:
                    try:
                        # item.account.data is parsed if encoding='jsonParsed'
                        data = item.account.data.parsed
                        info = data['info']
                        mint = info['mint']
                        amount = float(info['tokenAmount']['uiAmount'] or 0)
                        decimals = info['tokenAmount']['decimals']
                        
                        if amount > 0: # Only store non-zero balances
                            tokens.append(TokenInfo(mint=mint, amount=amount, decimals=decimals))
                    except Exception as parse_err:
                        print(f"Error parsing token account: {parse_err}")
                        continue
            
            return AccountInfo(sol_balance=sol_balance, tokens=tokens)

        except Exception as e:
            print(f"Error fetching account details for {address}: {e}")
            return AccountInfo(sol_balance=0.0, tokens=[])

    async def start_monitoring(self, address: str):
        if address in self.active_monitors:
            print(f"Already monitoring {address}")
            return
        
        self.active_monitors.add(address)
        print(f"Started monitoring {address}")
        
        # Immediate fetch of initial state
        self._update_db_info(address)

        while address in self.active_monitors:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    print(f"Connected to WS for {address}")
                    
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
                    
                    while address in self.active_monitors:
                        try:
                            response = await websocket.recv()
                            data = json.loads(response)
                            
                            if "method" in data and data["method"] == "logsNotification":
                                self._handle_notification(address, data)
                                
                        except websockets.ConnectionClosed:
                            print(f"WebSocket closed for {address}")
                            break
                        except Exception as e:
                            print(f"Error receiving data for {address}: {e}")
                            break
            
            except Exception as conn_err:
                print(f"Connection failed for {address}: {conn_err}. Retrying in 5s...")
                await asyncio.sleep(5)
        
        print(f"Stopped monitoring loop for {address}")

    def stop_monitoring(self, address: str):
        if address in self.active_monitors:
            self.active_monitors.remove(address)
            print(f"Stopping monitoring for {address}")

    def _update_db_info(self, address: str):
        """Helper to fetch and update account info in DB"""
        if address in scammer_db:
            info = self.get_account_details(address)
            scammer_db[address].account_info = info
            scammer_db[address].balance = info.sol_balance
            print(f"Updated info for {address}: {info.sol_balance} SOL, {len(info.tokens)} tokens")

    def _handle_notification(self, address: str, data: dict):
        try:
            logs = data["params"]["result"]["value"]["logs"]
            signature = data["params"]["result"]["value"]["signature"]
            
            print(f"Activity detected on {address}! Signature: {signature}")
            
            # Update activity log
            if address in scammer_db:
                scammer_db[address].latest_activity.append(signature)
                # Keep only last 50
                if len(scammer_db[address].latest_activity) > 50:
                    scammer_db[address].latest_activity.pop(0)

            # Re-fetch account info (Balance/Tokens) changed!
            self._update_db_info(address)

            # Analyze Transaction asynchronously to avoid blocking loop? 
            # Ideally yes, but here we do it inline or create a task.
            # Creating a task is safer for the WS loop.
            asyncio.create_task(self._analyze_transaction(address, signature))

        except Exception as e:
            print(f"Error handling notification: {e}")
            traceback.print_exc()

    async def _analyze_transaction(self, monitored_address: str, signature: str):
        try:
            # Allow propagation
            await asyncio.sleep(2) 
            
            sig_obj = Signature.from_string(signature)
            tx = self.rpc_client.get_transaction(sig_obj, max_supported_transaction_version=0)
            
            if not tx.value:
                return

            # Reuse logic from verification.py or custom logic here
            # For now, let's look for SOL transfers OUT of the monitored address
            
            meta = tx.value.transaction.meta
            if meta.err:
                return

            account_keys = tx.value.transaction.transaction.message.account_keys
            str_keys = [str(k) for k in account_keys]
            
            pre_balances = meta.pre_balances
            post_balances = meta.post_balances
            
            if monitored_address in str_keys:
                idx = str_keys.index(monitored_address)
                diff = (post_balances[idx] - pre_balances[idx]) / 1e9
                
                if diff < -0.001: # Significant decrease (sending funds)
                    # Find who received positive amount
                    # Naive: just find the biggest gainer
                    max_gain = 0
                    receiver = "Unknown"
                    
                    for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
                        gain = (post - pre) / 1e9
                        if gain > max_gain and i != idx:
                            max_gain = gain
                            receiver = str_keys[i]
                    
                    if max_gain > 0:
                        risk = get_risk_label(receiver)
                        msg = f"⚠ ALERT: {monitored_address} moved {abs(diff):.4f} SOL to {receiver}. Risk: {risk}"
                        
                        if monitored_address in scammer_db:
                            scammer_db[monitored_address].risk_label = risk
                            scammer_db[monitored_address].status = "Active Movement"
                            scammer_db[monitored_address].recent_logs.append(msg)
                            # Keep only last 50 logs
                            if len(scammer_db[monitored_address].recent_logs) > 50:
                                scammer_db[monitored_address].recent_logs.pop(0)
                            
                        await trigger_whatsapp_alert(msg)

        except Exception as e:
            print(f"Error analyzing tx {signature}: {e}")

watchdog_service = Watchdog()

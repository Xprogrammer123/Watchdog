from solana.rpc.api import Client
from solders.signature import Signature
import os

def get_solana_client():
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    return Client(rpc_url)

def check_sol_transfer(meta, account_keys, sender: str, receiver: str) -> dict:
    """
    Checks for direct SOL transfers by analyzing pre/post lamport balances.
    """
    try:
        if sender not in account_keys or receiver not in account_keys:
            return {"verified": False}

        sender_idx = account_keys.index(sender)
        receiver_idx = account_keys.index(receiver)

        pre_balances = meta.pre_balances
        post_balances = meta.post_balances

        # Calculate changes (in SOL)
        sender_change = (post_balances[sender_idx] - pre_balances[sender_idx]) / 1e9
        receiver_change = (post_balances[receiver_idx] - pre_balances[receiver_idx]) / 1e9

       
        
        if receiver_change > 0:
            return {
                "verified": True,
                "amount": receiver_change,
                "token": "SOL",
                "message": "Verified SOL transfer"
            }
            
    except ValueError:
        pass
        
    return {"verified": False}

def check_token_transfer(meta, sender: str, receiver: str) -> dict:
    """
    Checks for SPL Token transfers by analyzing pre/post token balances.
    We look for a token account owned by 'receiver' that increased in balance,
    and a token account owned by 'sender' that decreased (optional, sometimes mints happen).
    """
    # pre_token_balances is a list of objects with {accountIndex, mint, uiTokenAmount, owner}
    # We care about the 'owner' field mostly.
    
    pre_tokens = meta.pre_token_balances
    post_tokens = meta.post_token_balances
    
    # Map (owner, mint) -> balance
    def map_balances(token_list):
        balances = {}
        for item in token_list:
            owner = item.owner
            mint = item.mint
            amount = float(item.ui_token_amount.ui_amount or 0)
            balances[(owner, mint)] = amount
        return balances

    pre_map = map_balances(pre_tokens)
    post_map = map_balances(post_tokens)
    
    # Check if Receiver gained any tokens
    # We iterate through post_tokens to find accounts owned by receiver
    for item in post_tokens:
        if item.owner == receiver:
            mint = item.mint
            new_bal = float(item.ui_token_amount.ui_amount or 0)
            old_bal = pre_map.get((receiver, mint), 0.0)
            
            diff = new_bal - old_bal
            
            if diff > 0:
                # Found a positive transfer to receiver!
                # Ideally check if sender lost same token (omitted for loose verification)
                return {
                    "verified": True,
                    "amount": diff,
                    "token": f"SPL Token ({mint[:4]}...)", # Shortened mint address
                    "mint": mint,
                    "message": f"Verified SPL Token transfer"
                }

    return {"verified": False}

def verify_transaction(signature: str, sender: str, receiver: str) -> dict:
    client = get_solana_client()
    try:
        sig = Signature.from_string(signature)
        # Fetch transaction details
        tx = client.get_transaction(sig, max_supported_transaction_version=0)
        
        if not tx.value:
            return {"verified": False, "message": "Transaction not found"}

        meta = tx.value.transaction.meta
        if meta.err:
             return {"verified": False, "message": "Transaction failed on chain"}
             
        # Get Account Keys as strings
        account_keys = tx.value.transaction.transaction.message.account_keys
        str_keys = [str(k) for k in account_keys]
        
        # 1. Check SOL Transfer
        sol_result = check_sol_transfer(meta, str_keys, sender, receiver)
        if sol_result["verified"]:
            sol_result["timestamp"] = tx.value.block_time
            return sol_result

        # 2. Check SPL Token Transfer
        token_result = check_token_transfer(meta, sender, receiver)
        if token_result["verified"]:
             token_result["timestamp"] = tx.value.block_time
             return token_result

        return {"verified": False, "message": "No significant SOL or Token movement found to the scammer address."}

    except Exception as e:
        return {"verified": False, "message": f"Error: {str(e)}"}

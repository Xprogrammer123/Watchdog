from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict
from .models import VerificationRequest, VerificationResponse, MonitorRequest, ScammerStatus
from .verification import verify_transaction
from .watchdog import watchdog_service
from .state import scammer_db

router = APIRouter()

@router.post("/verify", response_model=VerificationResponse)
async def verify_tx(request: VerificationRequest):
    result = verify_transaction(request.transaction_signature, request.user_wallet, request.scammer_wallet)
    
    if result["verified"]:
        return VerificationResponse(
            verified=True,
            amount=result.get("amount", 0.0),
            token=result.get("token", "SOL"),
            mint=result.get("mint"),
            timestamp=result.get("timestamp", 0),
            message=result.get("message", "Transaction Verified")
        )
    else:
        # Return HTTP 400 or just a failed verification response?
        # Let's return the response with verified=False
        return VerificationResponse(
            verified=False,
            amount=0.0,
            token="SOL",
            mint=None,
            timestamp=0,
            message=result["message"]
        )

@router.post("/monitor")
async def start_monitoring(request: MonitorRequest, background_tasks: BackgroundTasks):
    # Update DB
    scammer_db[request.scammer_wallet] = ScammerStatus(
        address=request.scammer_wallet,
        balance=0.0, # Fetch real balance
        status="Monitoring",
        risk_label="Unknown",
        latest_activity=[]
    )
    
    # Start the watchdog in python background task
    background_tasks.add_task(watchdog_service.start_monitoring, request.scammer_wallet)
    
    return {"status": "Monitoring started", "address": request.scammer_wallet}

@router.get("/status/{address}", response_model=ScammerStatus)
async def get_status(address: str):
    if address not in scammer_db:
        raise HTTPException(status_code=404, detail="Address not found in monitoring")
    return scammer_db[address]

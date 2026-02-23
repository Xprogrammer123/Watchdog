# Watchdog API

Watchdog-API is the backend service for the [Watchdog Protocol](https://github.com/Xprogrammer123/Sol-Watchdog), a tool designed to monitor and detect fraudulent transactions on the Solana blockchain. This API, built with Python and FastAPI, provides endpoints to verify transactions, monitor suspicious wallets, and retrieve the status of monitored wallets.

## Features

-   **Transaction Verification:** Verifies if funds have been transferred from a victim's wallet to a suspected scammer wallet.
-   **Real-Time Wallet Monitoring:** Uses WebSockets to monitor suspected wallets in real-time.
-   **Risk Analysis:** Basic risk labeling based on the destination address.
-   **Asynchronous Tasks:** Utilizes FastAPI's background tasks to handle wallet monitoring without blocking the API.

## Tech Stack

-   Python 3.11
-   FastAPI
-   Uvicorn
-   solana & solders
-   WebSockets
-   python-dotenv

## Getting Started

### Prerequisites

-   Python 3.11 or later
-   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Xprogrammer123/Watchdog-api.git
    cd Watchdog-api
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

After installing the dependencies, you can run the API using uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be accessible at `http://localhost:8000`.

## API Endpoints

### POST /api/v1/verify

Verifies a Solana transaction.

**Request Body:**

```json
{
  "user_wallet": "86FbQt7Z19radRCBQDNxCzAoDkf6M3Fau1LAKdWc4Qfah",
  "scammer_wallet": "4xs5BN6aEQWjYedw39hDjYTy2wfDGmp1dBvWwuSVmXwz",
  "transaction_signature": "e2tFJY94RyFiBrrjYT3v2yYVBhWEDQZRbbrxdacxAtj5LvLimhzq9ra6Hy3z4yRwQg8W5ShHFpRpzJzJBpEa85"
}
```

**Successful Response:**

```json
{
  "verified": true,
  "amount": 0.245,
  "token": "SOL",
  "mint": null,
  "timestamp": 1685493864,
  "message": "Transaction Verified"
}
```

### POST /api/v1/monitor

Starts monitoring a scammer wallet.

**Request Body:**

```json
{
  "scammer_wallet": "4xs5BN6aEQWjYedw38hDjYTy2wfdGMp1dBvWwuSZmXwz"
}
```

### GET /api/v1/status/{wallet_address}

Retrieves the current status of a monitored wallet.

**Successful Response:**

```json
{
  "address": "4xs5BN6aEQWjYedw39hDjYTy2wfDGmp1dBvWwuSVmXwz",
  "balance": 0.5,
  "status": "Monitoring",
  "risk_label": "Unknown",
  "latest_activity": []
}
```

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

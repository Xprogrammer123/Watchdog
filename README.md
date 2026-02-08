# Watchdog API

Backend for the Watchdog tool to monitor scammer wallets on Solana.

## Setup

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```
2.  Install dependencies:
    ```bash
    ./venv/bin/pip install -r requirements.txt
    ```

## Running the Server

```bash
./venv/bin/python -m app.main
```

## Features

-   **Verification**: Verifies that funds moved from a user wallet to a scammer wallet.
-   **Monitoring**: Real-time WebSocket monitoring of scammer addresses.
-   **Alerts**: Placeholder for WhatsApp alerts (see `app/watchdog.py`).
-   **Risk Analysis**: Basic risk labeling based on destination address.

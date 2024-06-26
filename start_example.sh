#!/bin/bash

export TELEGRAM_TOKEN="123:abc"
export ADMIN_TELEGRAM_ID="123"

export WEBHOOK_HOST="https://example.com"
export WEBAPP_PORT="5000"

export DONATE_URL="https://pay.cloudtips.ru/p/0a19cb8e"
export SUBSCRIBE_URL="https://boosty.to/dant4ick"
export CRYPTO_PAY_API_TOKEN = "123:abc"
export CRYPTO_PAY_NET="testnet"

until python3 run.py; do
    echo "The program crashed at `date +%H:%M:%S`. Restarting the script..."
done

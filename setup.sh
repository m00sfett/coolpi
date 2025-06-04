#!/bin/bash
# Setup script for CoolPi

set -e

BASE_DIR="/opt/coolpi"
CONFIG_FILE="$BASE_DIR/config/coolpi.conf"
SERVICE_FILE="/etc/systemd/system/coolpi.service"

# default values
LOGLEVEL=1
ACTIVE=0
TEMP_HIGH=50.0
TEMP_LOW=45.0
INTERVAL=5
GPIO=13

read -p "Log level [${LOGLEVEL}]: " ans
LOGLEVEL=${ans:-$LOGLEVEL}
read -p "Enable fan control (1/0) [${ACTIVE}]: " ans
ACTIVE=${ans:-$ACTIVE}
read -p "Temperature to turn fan on [${TEMP_HIGH}]: " ans
TEMP_HIGH=${ans:-$TEMP_HIGH}
read -p "Temperature to turn fan off [${TEMP_LOW}]: " ans
TEMP_LOW=${ans:-$TEMP_LOW}
read -p "Measurement interval (seconds) [${INTERVAL}]: " ans
INTERVAL=${ans:-$INTERVAL}
read -p "GPIO pin [${GPIO}]: " ans
GPIO=${ans:-$GPIO}

mkdir -p "$BASE_DIR"
cp -r src config requirements.txt "$BASE_DIR/"

cat > "$CONFIG_FILE" <<CFG
[console]
loglevel = $LOGLEVEL

[fan]
active = $ACTIVE
temphigh = $TEMP_HIGH
templow = $TEMP_LOW
interval = $INTERVAL
gpio = $GPIO
CFG

pip install -r "$BASE_DIR/requirements.txt"

cp systemd/coolpi.service "$SERVICE_FILE"
if command -v systemctl >/dev/null; then
    systemctl daemon-reload
    systemctl enable coolpi.service
    systemctl start coolpi.service
fi

echo "Installation complete."

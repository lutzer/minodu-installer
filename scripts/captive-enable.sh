#!/bin/bash

CONF_NAME="captive.conf"
CONF_DIR="/etc/dnsmasq.d"
DISABLED_DIR="/etc/dnsmasq.disabled"
CONF_FILE="$CONF_DIR/$CONF_NAME"
DISABLED_FILE="$DISABLED_DIR/$CONF_NAME"

# Ensure disabled dir exists
mkdir -p "$DISABLED_DIR"

if [ "$(id -u)" -ne 0 ]; then
  echo "❌ This script must be run as root (use sudo)." >&2
  exit 1
fi

case "$1" in
  enable)
    if [ -f "$DISABLED_FILE" ]; then
      echo "🔼 Enabling $CONF_NAME..."
      mv "$DISABLED_FILE" "$CONF_FILE"
      systemctl restart dnsmasq
      echo "✅ Config enabled and dnsmasq restarted."
    else
      echo "ℹ️ $CONF_NAME is already enabled or not found in disabled dir." >&2
      exit 1
    fi
    ;;
  disable)
    if [ -f "$CONF_FILE" ]; then
      echo "🔻 Disabling $CONF_NAME..."
      mv "$CONF_FILE" "$DISABLED_FILE"
      systemctl restart dnsmasq
      echo "✅ Config disabled and dnsmasq restarted."
    else
      echo "ℹ️ $CONF_NAME is already disabled or missing." >&2
      exit 1
    fi
    ;;
  *)
    echo "Usage: sudo $0 [enable|disable]" >&2
    exit 1
    ;;
esac

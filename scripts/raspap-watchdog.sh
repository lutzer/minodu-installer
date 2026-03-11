#!/bin/bash
# /usr/local/bin/raspap-watchdog.sh

IFACE="wlan1"

# Check if interface exists
if ! ip link show $IFACE > /dev/null 2>&1; then
    exit 0
fi

# Check if any clients connected
CLIENTS=$(iw dev $IFACE station dump | grep Station)

# If no clients, restart RaspAP (hostapd + dnsmasq)
if [ -z "$CLIENTS" ]; then
    echo "No clients, restarting RaspAP..."
    systemctl restart raspapd
fi
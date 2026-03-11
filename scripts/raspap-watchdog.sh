#!/bin/bash

IFACE="wlan1"

# Check if AP interface exists
if ! ip link show $IFACE > /dev/null 2>&1; then
    exit 0
fi

# Restart hostapd if it crashed
if ! systemctl is-active --quiet hostapd; then
    echo "hostapd stopped, restarting..."
    systemctl restart hostapd
fi

# Restart DHCP if needed
if ! systemctl is-active --quiet dnsmasq; then
    echo "dnsmasq stopped, restarting..."
    systemctl restart dnsmasq
fi

# Check if interface is still up
STATE=$(cat /sys/class/net/$IFACE/operstate)

if [ "$STATE" != "up" ]; then
    echo "AP interface down, restarting hotspot..."
    systemctl restart hostapd
    systemctl restart dnsmasq
fi
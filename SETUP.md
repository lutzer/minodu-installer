# Setup RaspPi for Minodu

## Setup Base System

* install raspberry pi os lite 64 bit with raspberry pi imager from [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)
  * set hostname to minodupi
  * enable ssh

* connect via ethernet cable to mac
  * set manual dhcp address to 192.168.2.1
  * enable internet sharing

* pi should be avalaible via `ssh pi@œminodupi.local`

* open `sudo raspi-config`, go to *Localisation Options* > *WLAN Country* > Togo

## Install dependencies

* `sudo apt update`
* `sudo apt-get install git`
* `sudo apt install dkms git build-essential bc`
* `sudo apt install linux-headers-$(uname -r)`

## Setup AP

### Hardware

* WIFI Adapters: https://github.com/morrownr/USB-WiFi?tab=readme-ov-file
* using TP Link AC600 Acrher T2U Plus
* plug it into usb1 port:
  ```
  [eth] [usb1] [usb2]
  [   ] [usb3] [usb4]
  ```

### Install drivers (not necessary on newer raspbian versions)

* `git clone https://github.com/RaspAP/raspap-tools.git`
* `chmod 755 install_wlan_drivers.sh`
* `./install_wlan_drivers.sh`
* to check if evertyhing is installed correctly:
  ```
  # Check if WLAN interface exists
  ip link show

  # Or specifically look for wireless interfaces
  iwconfig

  # Check loaded drivers/modules
  lsmod | grep -i 8188  # for Realtek (common USB adapters)
  lsmod | grep -i brcm  # for Broadcom (built-in Pi WiFi)

  # Check dmesg for driver errors
  dmesg | grep -i wlan
  dmesg | grep -i firmware

  # Check if firmware loaded successfully
  sudo rfkill list
  ```

### Installation

* clone repo with `git clone https://github.com/RaspAP/raspap-webgui.git`
* run `cd raspy-webgui`
* run  `sudo bash installers/raspbian.sh --yes`
* change webinterface port:
  * edit `/etc/lighttpd/lighttpd.conf`
    ```
    # change port to 81 by changing line: 
    server.port                 = 81
    ```
  * sudo reboot

### Router Config

* open webinterface with `http://minodupi.local:81/`
* standard credentials: admin / secret
* change credentials

### Adjust config

* edit config files

  * open `sudo nano /etc/hostapd/hostapd.conf` and replace content with:

  ```
  driver=nl80211
  ctrl_interface=/var/run/hostapd
  ctrl_interface_group=0
  auth_algs=1
  wpa_key_mgmt=WPA-PSK
  beacon_int=100
  ssid=Minodu
  channel=1
  hw_mode=g
  ieee80211n=1
  interface=wlan1
  wpa=none
  wpa_pairwise=CCMP
  country_code=DE
  ignore_broadcast_ssid=0
  ap_max_inactivity=600
  disassoc_low_ack=1
  skip_inactivity_poll=1
  wmm_enabled=1
  ```

* Change `sudo nano /etc/dnsmasq.d/090_wlan1.conf`to

  ```
  # RaspAP wlan1 configuration
  interface=wlan1
  dhcp-range=10.20.1.100,10.20.1.255,255.255.255.0,12h
  ```
  
* `sudo nano /etc/dhcpcd.conf`, change:

  ```
  # RaspAP wlan1 configuration
  interface wlan1
  static ip_address=10.20.1.1/24
  static routers=10.20.1.1
  static domain_name_servers=1.1.1.1 8.8.8.8
  ```

* reboot with `sudo reboot`

* login into the webinterface via *minodupi.local:81*

* check if wlan1 interface is startd with `iw dev`
  * if wlan1 isnt starting run `sudo rfkill unblock all`

* disable usb power maganement by adding at the end to `sudo nano /boot/firmware/cmdline.txt`
  ```
  #disable usb power suspsend
  usbcore.autosuspend=-1
  ```
* disable wlan power managment with `sudo nano /etc/udev/rules.d/70-rtl88x2bu-pm.rules`
  ```
  ACTION=="add", SUBSYSTEM=="net", KERNEL=="wlan1", RUN+="/sbin/iwconfig wlan1 power off"
  ```

* cp reboot service files with `sudo cp scripts/daily-* /etc/systemd/system/`
  ```
* enable reboot timer
 `sudo systemctl daemon-reload && sudo systemctl enable daily-reboot.timer && sudo systemctl start daily-reboot.timer`

## Setup captive portal

* create file `sudo nano /etc/dnsmasq.d/captive.conf`

	```
  interface=wlan1
  address=/#/10.20.1.1
  ```
  
 * redirect all traffic to router with `sudo iptables -t nat -A PREROUTING -i wlan1 -p udp --dport 53 -j DNAT --to 10.20.1.1 && sudo iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 53 -j DNAT --to 10.20.1.1`

* create file `/home/minodu/www/hotspot-detect.html`

  ```
  <!DOCTYPE html>
  <html>
  <head>
    <title>Captive Portal</title>
    <script type="text/javascript">
          // Redirect to the index.html page (your captive portal)
          window.location.href = "http://minodupi.local";
    </script>
  </head>
  <body>
    <h1>Success</h1>
  </body>
  </html>
  ```

## Setup Weather Station

* connect weatherstation to wifi
* set post url to `http://minodupi.local/api/backend/v1/weather`

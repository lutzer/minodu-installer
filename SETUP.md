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

  * open ` sudo nano /etc/hostapd/hostapd.conf` and replace content with:

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
  ieee80211n=0
  interface=wlan1
  wpa=none
  wpa_pairwise=CCMP
  country_code=DE
  ignore_broadcast_ssid=0
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

* change`/etc/lighttpd/lighttpd-80.conf`

  ```sh
  include_shell "/usr/share/lighttpd/create-mime.conf.pl"
  
  server.port                 = 80
  server.document-root        = "/home/minodu/www"
  server.username             = "www-data"
  server.groupname            = "www-data"
  server.errorlog             = "/var/log/lighttpd/error.log"
  server.pid-file             = "/run/lighttpd.pid"
  
  server.modules = (
      "mod_indexfile",
      "mod_dirlisting",
      "mod_staticfile",
      "mod_redirect",
      "mod_rewrite"
  )
  
  index-file.names = ( "index.html" )
  
  # Allow directory listing if no index file is found
  dir-listing.activate = "enable"
  
  # Redirect all unknown requests to /index.html (without causing loops)
  $HTTP["url"] !~ "^/(index\.html|captive\.css|logo\.png)?$" {
      url.rewrite-if-not-file = ( ".*" => "/index.html" )
  }
  
  # Captive portal probe handling
  
  # Apple devices (macOS, iOS) - serve the Success page to captive.apple.com
  $HTTP["host"] == "captive.apple.com" {
      url.rewrite-once = ( ".*" => "/hotspot-detect.html" )
  }
  
  # Android devices (connectivitycheck.gstatic.com, clients3.google.com)
  $HTTP["host"] =~ "^(connectivitycheck\.gstatic\.com|clients3\.google\.com)$" {
      url.rewrite-once = ( ".*" => "/index.html" )
  }
  
  # Windows devices (www.msftconnecttest.com)
  $HTTP["host"] == "www.msftconnecttest.com" {
      url.rewrite-once = ( ".*" => "/index.html" )
  }
  
  # Android specific path - generate_204
  $HTTP["url"] =~ "^/generate_204$" {
      url.rewrite-once = ( ".*" => "/index.html" )
  }
  ```

  

## Setup Docker

* install with 

  ```
  sudo apt update
  sudo apt upgrade
  curl -sSL https://get.docker.com | sh
  ```

* add current user to docker group with

  ```
  sudo usermod -aG docker $USER
  ```

* `logout`and check if everything works correcly with

  ```
  docker run hello-world
  ```

* autostart docker with `sudo systemctl enable docker`

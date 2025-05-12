# Setup RaspPi as router

## Hardware

* WIFI Adapters: https://github.com/morrownr/USB-WiFi?tab=readme-ov-file

## Installation

* clone repo with `git clone https://github.com/RaspAP/raspap-webgui.git`
* run `cd raspy-webgui`
* run  `sudo bash installers/raspbian.sh --yes`

## Adjust config

* edit config files

  * open` sudo nano /etc/hostapd/hostapd.conf` and replace content with:

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
  interface=wlan0
  wpa=none
  wpa_pairwise=CCMP
  country_code=DE
  ignore_broadcast_ssid=0
  ```

* change webinterface port

  * edit `/etc/lighttpd/lighttpd.conf`

    ```
    # change port to 81 by changing line: 
    server.port                 = 81
    ```

* change hostname with `hostnamectl set-hostname minodupi.local`

* reboot with `sudo reboot`

## Router Config

* open webinterface with `http://minodupi.local:81/`
* credentials: admin / secret

# Setupo second Lighttp Instance

* Create new lighttp conf `/etc/lighttpd/lighttpd-80.conf`

  ```
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
      "mod_redirect"
  )
  
  index-file.names = ( "index.html" )
  
  # Allow directory listing if no index file is found
  dir-listing.activate = "enable"
  
  # Redirect everything except index.html to captive portal domain
  $HTTP["url"] !~ "^/(index\.html)?$" {
      url.redirect = (
          ".*" => "http://minodupi.local/"
      )
  }
  ```
  
* change file permissions of www directory to 755 with `chmod -R 755 /home/minodu/www`

* Create system d service:

  * Create file `sudo nano /etc/systemd/system/lighttpd-80.service`

    ```
    [Unit]
    Description=Lighttpd Daemon
    After=network-online.target
    
    [Service]
    Type=simple
    PIDFile=/run/lighttpd.pid
    ExecStartPre=/usr/sbin/lighttpd -tt -f /etc/lighttpd/lighttpd-80.conf
    ExecStart=/usr/sbin/lighttpd -D -f /etc/lighttpd/lighttpd-80.conf
    ExecReload=/bin/kill -USR1 $MAINPID
    Restart=on-failure
    
    [Install]
    WantedBy=multi-user.target
    ```

  * Create and start new service

    ```
    # run in shell
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl start lighttpd-80.service
    sudo systemctl enable lighttpd-80.service
    ```

# Setup captive portal

* create file `sudo nano /etc/dnsmasq.d/captive.conf`

	```
  interface=wlan0
  address=/#/10.3.141.1
  ```
  
 * redirect all traffic to router with:

   ```
   sudo iptables -t nat -A PREROUTING -i wlan0 -p udp --dport 53 -j DNAT --to 10.3.141.1
   sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 53 -j DNAT --to 10.3.141.1
   ```
* create file `/home/minodu/www/hotspot-detect.html`

  ```
  <!DOCTYPE html>
  <html>
  <head>
    <title>Captive Portal</title>
    <script type="text/javascript">
          // Redirect to the index.html page (your captive portal)
          window.location.href = "http://minodupi.local/index.html";
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

  

# Setup Docker

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

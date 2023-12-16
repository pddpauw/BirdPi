**this repository is a copy of: https://github.com/mcguirepr89/BirdNET-Pi/**

> [!CAUTION]
> rights linked to the original repository also apply to this one

Intent of this repository is to have a working installation script for the Pi5 running Bookworm.

> [!IMPORTANT]
> Ensure you have installed the 64bit LITE Bookworm OS on your raspberry Pi5.

to install, run the following script:
```
curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/newinstaller.sh| bash
```

following changes have been implemented on the original repository from mcguirepr89:
1) right verions of php in the CaddyFile (current version is 8.2)
2) disable Apache (which get installed)
3) enable Caddy as systemd service
4) change permission in /home/ to make this work

> [!TIP]
> Changing your IP to a static IP can be done like this in Bookworm:
```
nmcli con show
```
select the device you wish to change, and then (change the IP addresses, depending on your local LAN and DHCP settings):
```
sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addr 192.168.15.56/24
sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.15.1
sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8"
sudo nmcli con up "Wired connection 1"
```

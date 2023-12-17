# Intro

**this repository is a copy of: https://github.com/mcguirepr89/BirdNET-Pi/**  
please use this original repo for install instructions etc... All is very wel described there.

> [!CAUTION]
> rights linked to the original repository also apply to this one

Intent of this repository is to have a working installation script for the Pi5 running Bookworm.  Preferably and ideally, those changes get included in the original repo.

> [!IMPORTANT]
> Ensure you have installed the 64bit LITE Bookworm OS on your raspberry Pi5.

to install, run the following script (can easily take 20-30 mins):
```
curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/newinstaller.sh| bash
```

# Changes vs original repository
following changes have been implemented on the original repository from mcguirepr89:
1) right verions of php in the CaddyFile (current version is 8.2)
2) disable Apache (which gets installed)
3) enable Caddy as systemd service
4) change permission in /home/pi/ to make this work (chmod 755 to this folder) - note that this is not ideal.  Preferably, we move all www data to /var/www/.  It works, but can be optimized.
5) change in the requirement.txt file to tflite_runtime-2.14.0-cp311-cp311-manylinux_2_34_armv7l.whl



# Changing IP address in Bookworm
```
nmcli con show
```
> select the device you wish to change, and then (change the IP addresses, depending on your local LAN and DHCP settings):
```
sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addr 192.168.15.56/24
sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.15.1
sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8"
sudo nmcli con up "Wired connection 1"
```

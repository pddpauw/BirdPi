# Intro

**this repository is a copy of: https://github.com/mcguirepr89/BirdNET-Pi/**  and is updated for installation on Raspberry 5 (Bookworm) and has some additional updates as described below.  Unfort, the original repository is no longer maintained, and thus changes for installation on Bookworm (Pi5) has not been included.
Please use the original repo for install instructions etc... All is very wel described there.

> [!CAUTION]
> rights linked to the original repository also apply to this one: you may not use BirdNET-Pi to develop a commercial product!  Review the license here: https://github.com/mcguirepr89/BirdNET-Pi/blob/main/LICENSE

Intent of this repository is to have a working installation script for the Pi5 running Bookworm.  Preferably and ideally, those changes get included in the original repo.

> [!IMPORTANT]
> Ensure you have installed the 64bit LITE Bookworm OS on your raspberry Pi5.

to install, run the following script (can easily take 20-30 mins):
```
curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/newinstaller.sh| bash
```

A live version can be found here: http://studiomondo.myqnapcloud.com:82/

# Changes vs original repository
following changes have been implemented on the original repository from mcguirepr89:
1) right verions of php in the CaddyFile (current version is 8.2)
2) disable Apache (which gets installed)
3) enable Caddy as systemd service
4) change permission in /home/pi/ to make this work (chmod 755 to this folder) - note that this is not ideal.  Preferably, we move all www data to /var/www/.  It works, but can be optimized.
5) change in the requirement.txt file to tflite_runtime-2.14.0-cp311-cp311-manylinux_2_34_armv7l.whl
6) refresh the database in the script plotly_streamlit.py (st.cache_resource.clear())
7) disable the terminal from the webpage _Importantly, if you wish to enable this, then feel free to adapt in views.php in your homepage/ folder (after installation), and uncomment line 264, and comment line 265_
8) change table in homepage to 50 species (change # readings in daily_plot.py (line 46))

# Changing IP address in Bookworm
network settings in Bookworm are managed via nmcli
```
nmcli con show
```
select the device you wish to change, and then (change the IP addresses, depending on your local LAN and DHCP settings), e.g. for your wired LAN connection:
```
sudo nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addr 192.168.15.56/24
sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.15.1
sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8"
sudo nmcli con up "Wired connection 1"
```

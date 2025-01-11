# Intro

I've stopped maintinging this one, please use this repository: https://github.com/Nachtzuster/BirdNET-Pi

A live version can be found here: http://studiomondo.myqnapcloud.com:82/

# Optimize for environment to limit data transfer
the php pages send updates (e.g. spectrogram, overview table) which consumes a considerable amount of data.  For mobile connections, this can impact speed and budget.
If you don't wish to have the refresh, could you use below script to update the file daily_plot.py and overview.php.  Please use those commands (from your BirdNET-Pi folder):
```
curl -s https://raw.githubusercontent.com/pddpauw/BirdPi/main/replace_lower_bandwith.sh| bash
```

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

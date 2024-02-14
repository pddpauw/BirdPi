#!/usr/bin/env bash
# this script will replace 2 files to reduce data rate (e.g. for 4G connections)

set -x

if [ "$EUID" == 0 ]
  then echo "Please run as a non-root user."
  exit
fi

# Simple new installer
HOME=$HOME
USER=$USER

export HOME=$HOME
export USER=$USER

wget -P $HOME/BirdNET-Pi/scripts https://github.com/pddpauw/BirdPi/raw/222576a3c9608ee414b4ab9e1504a57fe1fd11fb/scripts/LB_daily_plot.py
wget -P $HOME/BirdNET-Pi/scripts https://github.com/pddpauw/BirdPi/raw/7dcd54e6624c9f5394d940dd893ad46255d72b64/scripts/LB_overview.php

mv $HOME/BirdNET-Pi/scripts/daily_plot.py $HOME/BirdNET-Pi/scripts/daily_plot_OLD.py 
mv $HOME/BirdNET-Pi/scripts/daily_plot.py $HOME/BirdNET-Pi/scripts/daily_plot_OLD.py 

mv $HOME/BirdNET-Pi/scripts/LB_daily_plot.py $HOME/BirdNET-Pi/scripts/daily_plot.py 
mv $HOME/BirdNET-Pi/scripts/LB_overview.php $HOME/BirdNET-Pi/scripts/overview.php

sudo chmod +x $HOME/BirdNET-Pi/scripts/daily_plot.py
sudo chmod 775 $HOME/BirdNET-Pi/scripts/daily_plot.py
sudo chmod 664 $HOME/BirdNET-Pi/scripts/daily_plot.py

$HOME/BirdNET-Pi/scripts/restart_services.sh

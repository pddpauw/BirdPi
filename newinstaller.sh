#!/usr/bin/env bash
# test for Pi5 version

if [ "$EUID" == 0 ]
  then echo "Please run as a non-root user."
  exit
fi

if [ "$(uname -m)" != "aarch64" ] && [ "$(uname -m)" != "x86_64" ];then
  echo "BirdNET-Pi requires a 64-bit OS.
It looks like your operating system is using $(uname -m),
but would need to be aarch64.
Please take a look at https://birdnetwiki.pmcgui.xyz for more
information"
  exit 1
fi

# the php code expects the user with uid 1000 on this system
PRIMARY=$(awk -F: '/1000/{print $1}' /etc/passwd)
if [ $USER != $PRIMARY ]; then
  echo "Current user \"$USER\" does not match the user with uid 1000 on this system \"$PRIMARY\". Aborting"
  exit
fi

# Simple new installer
HOME=$HOME
USER=$USER

export HOME=$HOME
export USER=$USER

PACKAGES_MISSING=
for cmd in git jq ; do
  if ! which $cmd &> /dev/null;then
      PACKAGES_MISSING="${PACKAGES_MISSING} $cmd"
  fi
done
if [[ ! -z $PACKAGES_MISSING ]] ; then
  sudo apt update
  sudo apt -y install $PACKAGES_MISSING
fi

branch=main
git clone -b $branch --depth=1 https://github.com/pddpauw/BirdPi.git ${HOME}/BirdNET-Pi &&

$HOME/BirdNET-Pi/scripts/install_birdnet.sh
sudo chmod +x $HOME/BirdNET-Pi/scripts/changes_pi_5.sh
sudo chmod 755 $HOME/
sudo chmod 777 $HOME/BirdSongs/
sudo touch $HOME/BirdNET-Pi/scripts/blacklisted_images.txt
$HOME/BirdNET-Pi/scripts/changes_pi_5.sh
if [ ${PIPESTATUS[0]} -eq 0 ];then
  echo "Installation completed successfully"
  sudo reboot
else
  echo "The installation exited unsuccessfully."
  exit 1
fi

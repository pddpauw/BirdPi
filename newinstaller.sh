#!/usr/bin/env bash
# Simple new installer
HOME=/home/pi
USER=pi
branch=git_install
sudo apt update
if ! which git &> /dev/null;then
  sudo apt -y install git
fi
git clone -b ${branch} https://github.com/mcguirepr89/BirdNET-Pi.git ${HOME}/BirdNET-Pi
${HOME}/BirdNET-Pi/scripts/birdnet-pi-config

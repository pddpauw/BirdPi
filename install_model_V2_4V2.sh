#!/usr/bin/env bash
# this script will replace the V2.4 model file with the new V2.4V2 model file

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

wget -P $HOME/BirdNET-Pi/model https://github.com/pddpauw/BirdPi/raw/5dc2a1edec6f669f8baff06be08b6cc996db36a2/model/NEW_BirdNET_GLOBAL_6K_V2.4_Model_FP16.tflite

mv $HOME/BirdNET-Pi/model/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite $HOME/BirdNET-Pi/model/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16_OLD.tflite

mv $HOME/BirdNET-Pi/model/NEW_BirdNET_GLOBAL_6K_V2.4_Model_FP16.tflite $HOME/BirdNET-Pi/model/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite
sudo chmod 664 $HOME/BirdNET-Pi/model/BirdNET_GLOBAL_6K_V2.4_MData_Model_FP16.tflite

$HOME/BirdNET-Pi/scripts/restart_services.sh

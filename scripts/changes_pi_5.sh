#!/usr/bin/env bash
# Execute the necessary changes for difference in set up on the Pi5 (bookworm):
set -x

# Turn off Apache2 
sudo systemctl disable apache2 && sudo systemctl stop apache2
echo "Apached2 disabled and stopped"

# Enable and turn on Caddy
sudo systemctl enable caddy && sudo systemctl start caddy
echo "Caddy enabled and started"

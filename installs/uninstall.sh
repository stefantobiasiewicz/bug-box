#!/bin/bash

echo "uninstalling bug-box app"

sudo systemctl disable bug-box
sudo systemctl stop bug-box
sudo rm -rf /etc/systemd/system/bug-box.service
sudo rm -rf /opt/bug-box

echo "uninstall DONE..."

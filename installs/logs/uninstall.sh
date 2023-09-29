#!/bin/bash

echo "uninstalling bug-box-logs app"

sudo systemctl disable bug-box-logs
sudo systemctl stop bug-box-logs
sudo rm -rf /etc/systemd/system/bug-box-logs.service

echo "uninstall DONE..."

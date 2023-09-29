#!/bin/bash

echo "updating bug-box-logs apllication'"

. ./uninstall.sh

cd ../..
sudo cp installs/logs/bug-box-logs.service /etc/systemd/system/bug-box-logs.service

sudo systemctl daemon-reload

sudo systemctl enable bug-box-logs
sudo systemctl start bug-box-logs

echo "updating done"

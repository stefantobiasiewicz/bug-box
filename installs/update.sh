#!/bin/bash

echo "updating apllication'"

cd ..
chmod +x run.sh
sudo cp -r $(pwd) /opt/bug-box
sudo cp installs/bug-box.service /etc/systemd/system/bug-box.service

sudo systemctl daemon-reload
sudo systemctl enable bug-box

sudo systemctl start bug-box

echo "updating done"

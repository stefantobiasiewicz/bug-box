#!/bin/bash

echo "updating apllication'"

cp /opt/bug-box/set-env.sh /tmp/set-env.sh

. ./uninstall.sh

cd ..
chmod +x run.sh
chmod +x run-logshipping.sh
sudo cp -r $(pwd) /opt/bug-box

cp /opt/bug-box/set-env.sh /opt/bug-box/set-env-new.sh
cp /tmp/set-env.sh /opt/bug-box/set-env.sh
echo "new env stored with default variables jere: '/opt/bug-box/set-env-new.sh'"
echo "pls check if your configuration contain all needed variables"

sudo cp installs/bug-box.service /etc/systemd/system/bug-box.service

sudo systemctl daemon-reload
sudo systemctl enable bug-box
sudo systemctl start bug-box

echo "updating done"

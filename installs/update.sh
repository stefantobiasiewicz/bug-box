#!/bin/bash

echo "updating apllication'"

cp /opt/bug-box/set-env.sh /tmp/set-env.sh

. ./uninstall.sh

cd ..
chmod +x run.sh
chmod +x run-logshipping.sh
sudo cp -r $(pwd) /opt/bug-box
sudo cp installs/bug-box.service /etc/systemd/system/bug-box.service

echo "old env variables stored in '/opt/bug-box/set-env-old.sh'"
cp /tmp/set-env.sh /opt/bug-box/set-env-old.sh
echo "after update check new env data and fill necessary fields after update"

sudo systemctl daemon-reload
sudo systemctl enable bug-box
sudo systemctl start bug-box

echo "updating done"

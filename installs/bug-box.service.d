[Unit]
Description=Bug-box application

[Service]
User=pi
Type=simple
ExecStart=sudo python3 /opt/bug-box/main.py
EnvironmentFile=/opt/bug-box/bug-box.service.env.conf
WorkingDirectory=/opt/bug-box

Restart=always

[Install]
WantedBy=multi-user.target
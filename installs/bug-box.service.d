[Unit]
Description=Bug-box application

[Service]
User=pi
Type=simple
ExecStart=/opt/bug-box/run.sh
WorkingDirectory=/opt/bug-box

Restart=always

[Install]
WantedBy=multi-user.target
#!/bin/bash

echo "Starting bug box appliction"
echo "preparing enviroment variables"
. ./set-env.sh

echo "run"
python3 logshipping.py


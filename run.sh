#!/bin/bash

echo "Starting bug box appliction"
echo "preparing enviroment variables"
sh ./set-env.sh

echo "run"
python3 test/env-test.py


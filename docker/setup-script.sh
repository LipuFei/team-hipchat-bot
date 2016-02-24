#!/usr/bin/env bash
SCRIPT_DIR=$(cd $(dirname $0) && pwd)
BOT_DIR_NAME="team-hipchat-bot"
PROJECT_DIR="${SCRIPT_DIR}/src/${BOT_DIR_NAME}"

pushd ${SCRIPT_DIR} > /dev/null

# activate virtualenv
source bin/activate
pip install --upgrade pip setuptools

# install requirements
pushd ${PROJECT_DIR} > /dev/null
pip install -r requirements.txt

# set PYTHONPATH
export PYTHONPATH=${PROJECT_DIR}:.:${PYTHONPATH}

# run the configuration script
./configure.py

# start the bot
./bot.py

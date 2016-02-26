FROM ubuntu:15.10
MAINTAINER Lipu Fei <lipu.fei815@gmail.com>

# install packages
RUN apt-get update && \
    apt-get install -y python python-virtualenv cron \
    python-cffi python-characteristic python-cryptography python-dateutil python-openssl python-leveldb \
    python-pycparser python-idna python-service-identity python-six python-pyasn1 python-pyasn1-modules \
    python-decorator python-croniter python-ipaddr python-twisted python-twisted-words python-wokkel

# add files
ADD team-hipchat-bot /team-hipchat-bot

# set environment variables
ENV PYTHONPATH /team-hipchat-bot:.:${PYTHONPATH}

# working directory
WORKDIR /team-hipchat-bot
CMD ./bot.py

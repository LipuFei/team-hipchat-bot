FROM ubuntu:15.10
MAINTAINER Lipu Fei <lipu.fei815@gmail.com>
RUN apt-get update && \
    apt-get install -y python python-virtualenv \
    python-cffi python-characteristic python-cryptography python-dateutil python-openssl \
    python-pycparser python-idna python-service-identity python-six python-pyasn1 python-pyasn1-modules \
    python-decorator python-crontab python-ipaddr python-twisted python-twisted-words python-wokkel
RUN virtualenv --no-site-packages /team-hipchat-bot-venv
ADD setup-script.sh /team-hipchat-bot-venv/
RUN chown -R nobody:nogroup /team-hipchat-bot-venv
WORKDIR /team-hipchat-bot-venv
USER nobody
ENTRYPOINT /team-hipchat-bot-venv/setup-script.sh
CMD [""]

#!/usr/bin/env python
import getpass
import logging
import os

from bot.bot import Bot

logging.basicConfig(level=logging.DEBUG,
                    format=u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')

PASSWORD_ENV_NAME = u'HCBOT_HIPCHAT_PASSWORD'


if __name__ == '__main__':
    # init config
    config_file = u'config.ini'

    # get password if available
    password = os.getenv(PASSWORD_ENV_NAME, u'').strip().decode('utf-8')

    # get password if it's not passed through the environment variable
    if not password:
        print u"Please input your Hipchat password:"
        password = getpass.getpass().decode('utf-8')

    bot = Bot(config_file, password)
    bot.initialize()
    bot.start()

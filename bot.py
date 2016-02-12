#!/usr/bin/env python
from ConfigParser import ConfigParser
import logging
import getpass

from bot.bot import Bot

logging.basicConfig(level=logging.DEBUG,
                    format=u'%(asctime)s - %(name)s - %(levelname)s - %(message)s')


if __name__ == '__main__':
    config_file = u'config.ini'

    config = ConfigParser()
    config.read([config_file])

    # get password
    print u"Please input your Hipchat password:"
    password = getpass.getpass()

    bot = Bot(config_file, config, password)
    bot.start()

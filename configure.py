#!/usr/bin/env python
#
# This script checks for environment variables and use them to set the configuration file.
#
# Supported environment variables are:
#  - HCBOT_HIPPCHAT_JID:
#  - HCBOT_HIPPCHAT_AUTH_TOKEN:
#  - HCBOT_HIPPCHAT_ROOM_JID:
#  - HCBOT_HIPPCHAT_ROOM_SERVER:
#  - HCBOT_HIPPCHAT_API_SERVER:
#  - HCBOT_HIPPCHAT_NICKNAME:
#  - HCBOT_HIPPCHAT_STFU_MINUTES:
#  - HCBOT_HIPPCHAT_DB:
#
#  - HCBOT_HIPPCHAT_TEAM_MEMBERS:
#  - HCBOT_HIPPCHAT_DAYSOFF_FILE:
#  - HCBOT_HIPPCHAT_CACHE_FILE:
#  - HCBOT_HIPPCHAT_ROOM_NAME:
#  - HCBOT_HIPPCHAT_TOPIC_UPDATE_TIME:
#  - HCBOT_HIPPCHAT_TOPIC_TEMPLATE:
#
from ConfigParser import ConfigParser
import codecs
import os
import sys


# a map of environment variables and configurations (section, option, default value)
ENV_KEY_MAP = {u'HCBOT_HIPPCHAT_JID':          (str, u''),
               u'HCBOT_HIPPCHAT_AUTH_TOKEN':   (str, u''),
               u'HCBOT_HIPPCHAT_ROOM_JID':     (str, u''),
               u'HCBOT_HIPPCHAT_ROOM_SERVER':  (str, u''),
               u'HCBOT_HIPPCHAT_API_SERVER':   (str, u''),
               u'HCBOT_HIPPCHAT_NICKNAME':     (str, u''),
               u'HCBOT_HIPPCHAT_STFU_MINUTES': (int, 0),
               u'HCBOT_HIPPCHAT_DB':           (str, u'hipchat_db'),

               u'HCBOT_TEAM_MEMBERS':           (str, u''),
               u'HCBOT_TEAM_DAYSOFF_FILE':      (str, u'daysoff.txt'),
               u'HCBOT_TEAM_CACHE_FILE':        (str, u'cache.txt'),
               u'HCBOT_TEAM_ROOM_NAME':         (str, u''),
               u'HCBOT_TEAM_TOPIC_UPDATE_TIME': (str, u'0 9 * * MON-FRI *'),
               u'HCBOT_TEAM_TOPIC_TEMPLATE':    (str, u'Current person on-duty: <name>'),
               }


def set_default_config(config):
    """
    Sets the given config to default values if the they are not present.
    :param config: The given config.
    """
    for sec, opt, val in ENV_KEY_MAP.itervalues():
        if not config.has_option(sec, opt):
            config.set(sec, opt, val)


if __name__ == '__main__':
    config_file = u"config.ini"

    if os.path.exists(config_file) and not os.path.isfile(config_file):
        print >> sys.stderr, u"%s is not a file." % config_file
        sys.exit(1)

    # initialize config
    config_parser = ConfigParser()
    if os.path.exists(config_file):
        config_parser.read([config_file])
    else:
        set_default_config(config_parser)

    # check environment variables
    for env_name, item in ENV_KEY_MAP.iteritems():
        value = os.getenv(env_name, u'').strip()
        if value == u'':
            continue

        item_type = item[0]
        if item_type != str:
            value = item_type(value)

        section, option, _ = item
        config_parser.set(section, option, value)

    # save the config file
    with codecs.open(config_file, 'wb', encoding='utf-8') as f:
        config_parser.write(f)

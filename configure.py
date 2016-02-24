#!/usr/bin/env python
#
# This script checks for environment variables and use them to set the configuration file.
#
# Supported environment variables are:
#  - HCBOT_JID:
#  - HCBOT_AUTH_TOKEN:
#  - HCBOT_ROOM_JID:
#  - HCBOT_ROOM_SERVER:
#  - HCBOT_SERVER:
#  - HCBOT_NICKNAME:
#  - HCBOT_STFU_MINUTES:
#  - HCBOT_DB:
#
#  - HCBOT_TEAM_MEMBERS:
#  - HCBOT_DAYSOFF_FILE:
#  - HCBOT_CACHE_FILE:
#  - HCBOT_ROOM_NAME:
#  - HCBOT_TOPIC_UPDATE_TIME:
#  - HCBOT_TOPIC_TEMPLATE:
#
from ConfigParser import ConfigParser
import codecs
import os
import sys


# a map of environment variables and configurations (section, option, default value)
ENV_KEY_MAP = {u'HCBOT_JID':          (u'hipchat', u'jid',          u''),
               u'HCBOT_AUTH_TOKEN':   (u'hipchat', u'auth_token',   u''),
               u'HCBOT_ROOM_JID':     (u'hipchat', u'room_jid',     u''),
               u'HCBOT_ROOM_SERVER':  (u'hipchat', u'room_server',  u''),
               u'HCBOT_SERVER':       (u'hipchat', u'server',       u''),
               u'HCBOT_NICKNAME':     (u'hipchat', u'nickname',     u''),
               u'HCBOT_STFU_MINUTES': (u'hipchat', u'stfu_minutes', 0),
               u'HCBOT_DB':           (u'hipchat', u'db',           u'hipchat_db'),

               u'HCBOT_TEAM_MEMBERS':      (u'team', u'members',           u''),
               u'HCBOT_DAYSOFF_FILE':      (u'team', u'daysoff_file',      u'daysoff.txt'),
               u'HCBOT_CACHE_FILE':        (u'team', u'cache_file',        u'cache.txt'),
               u'HCBOT_ROOM_NAME':         (u'team', u'room_name',         u''),
               u'HCBOT_TOPIC_UPDATE_TIME': (u'team', u'topic_update_time', u'0 9 * * MON-FRI *'),
               u'HCBOT_TOPIC_TEMPLATE':    (u'team', u'topic_template',    u'Current person on-duty: <name>'),
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
        if value:
            continue

        if env_name == u"HCBOT_STFU_MINUTES":
            value = int(value)

        section, option, _ = item
        config_parser.set(section, option, value)

    # save the config file
    with codecs.open(config_file, 'wb', encoding='utf-8') as f:
        config_parser.write(f)

"""
Configuration related code.
"""
from ConfigParser import ConfigParser
import codecs
import os


# a map of environment variable names and default values
DEFAULT_DICT = {u'HCBOT_HIPCHAT_JID': u'',
                u'HCBOT_HIPCHAT_AUTH_TOKEN':   u'',
                u'HCBOT_HIPCHAT_ROOM_JID':     u'',
                u'HCBOT_HIPCHAT_ROOM_SERVER':  u'',
                u'HCBOT_HIPCHAT_API_SERVER':   u'',
                u'HCBOT_HIPCHAT_NICKNAME':     u'',
                u'HCBOT_HIPCHAT_STFU_MINUTES': u'0',
                u'HCBOT_HIPCHAT_DB':           u'hipchat_db',

                u'HCBOT_TEAM_MEMBERS':           u'',
                u'HCBOT_TEAM_DAYSOFF_FILE':      u'daysoff.txt',
                u'HCBOT_TEAM_CACHE_FILE':        u'cache.txt',
                u'HCBOT_TEAM_ROOM_NAME':         u'',
                u'HCBOT_TEAM_TOPIC_UPDATE_TIME': u'0 9 * * MON-FRI *',
                u'HCBOT_TEAM_TOPIC_TEMPLATE':    u'Current person on-duty: <name>',
                }


def set_default_config(config, set_all=False):
    """
    Sets the given config parser to the default settings.
    :param config: The given config parser.
    :param set_all: If True, all settings will be set to the default, otherwise,
                    only the missing settings will be set.
    """
    for env_name, value in DEFAULT_DICT.iteritems():
        section, option = get_config_name_from_env_name(env_name)

        if set_all or not config.has_option(section, option):
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, option, value)


def override_config_with_env(config):
    """
    Overrides the given config parser settings with the environment variables.
    :param config: The given config parser.
    """
    # override the config file values with environment variables (if present)
    for env_name, env_value in os.environ.iteritems():
        result = get_config_name_from_env_name(env_name)
        if result is None:
            continue
        section, option = result
        item_value = env_value.decode('utf-8')

        config.set(section, option, item_value)


def get_config_name_from_env_name(env_name):
    """
    Gets the corresponding config name from the given environment variable name.
    :param env_name: The given environment variable name.
    :return:  a tuple of section and option if the give name valid, otherwise None.
    """
    if env_name not in DEFAULT_DICT:
        return
    parts = env_name.split(u'_', 2)
    if len(parts) != 3:
        return
    if parts[0] != u'HCBOT':
        return
    section = parts[1].lower()
    option = parts[2].lower()
    return section, option


def init_config(config_file):
    """
    Initializes the configuration.
    :param config_file: The configuration file.
    :return: The initialized config parser.
    """
    config_parser = ConfigParser()

    # load config file if exists
    if os.path.exists(config_file):
        if os.path.isfile(config_file):
            read_config_file_utf8(config_parser, config_file)
        else:
            raise RuntimeError(u"%s is not a file." % config_file)

    # set the missing settings to the default values
    set_default_config(config_parser)

    # override the config file values with environment variables (if present)
    override_config_with_env(config_parser)
    return config_parser


def read_config_file_utf8(config, file_path):
    """
    Reads a config file with utf-8 encoding.
    :param config: The config parser.
    :param file_path: The config file path.
    """
    with codecs.open(file_path, 'r', 'utf-8') as f:
        config.readfp(f)


def write_config_file_utf8(config, file_path):
    """
    Writes a config file with utf-8 encoding.
    :param config: The config parser.
    :param file_path: The config file path.
    """
    with codecs.open(file_path, 'w', 'utf-8') as f:
        config.write(f)

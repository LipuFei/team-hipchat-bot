"""
Configuration related code.
"""
from ConfigParser import ConfigParser
import os


# a map of environment variable names and the key-values
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
    Sets the given config parser to the default settings.
    :param config: The given config parser.
    """
    for env_name, item in ENV_KEY_MAP.iteritems():
        section, option = get_config_name_from_env_name(env_name)
        item_value = item[1]
        config.set(section, option, item_value)


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

        # convert the value to the proper type
        item_type = ENV_KEY_MAP[env_name][0]
        if item_type == str:
            item_value = env_value.decode('utf-8')
        else:
            item_value = item_type(env_value)

        config.set(section, option, item_value)


def get_config_name_from_env_name(env_name):
    """
    Gets the corresponding config name from the given environment variable name.
    :param env_name: The given environment variable name.
    :return:  a tuple of section and option if the give name valid, otherwise None.
    """
    if env_name not in ENV_KEY_MAP:
        return
    parts = env_name.split(u'_', 3)
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
            config_parser.read([config_file])
        else:
            raise RuntimeError(u"%s is not a file." % config_file)
    else:
        # if not config file is present, use the default values
        set_default_config(config_parser)

    # override the config file values with environment variables (if present)
    override_config_with_env(config_parser)
    return config_parser

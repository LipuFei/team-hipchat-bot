def get_config_name_from_env_name(env_name):
    """
    Gets the corresponding config name from the given environment variable name.
    :param env_name: The given environment variable name.
    :return:  a tuple of section and option if the give name valid, otherwise None.
    """
    parts = env_name.split(u'_', 3)
    if len(parts) != 3:
        return
    if parts[0] != u'HCBOT':
        return
    section = parts[1].lower()
    option = parts[2].lower()
    return section, option

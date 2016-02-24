import logging

from twisted.web.client import getPage

from .util import get_config_name_from_env_name


class RestKvClient(object):
    """
    A client for retrieving key-values from a RESTful Key-Value service.
    """

    def __init__(self, bot, base_url, key_list, time_out=10):
        # pre-check
        if len(set(key_list)) != len(key_list):
            raise RuntimeError(u"You have duplicate keys in the key list: %s", key_list)

        self._logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.base_url = base_url
        self.key_list = key_list
        self.time_out = time_out

        self._remaining_key_list = []
        self._key_update_defer = None
        self._new_key_dict = None

    def update_all_keys(self):
        """
        Triggers a task that fetches all key-values and updates the config file.
        """
        self._logger.info(u"start updating keys...")
        self._remaining_key_list = self.key_list[:]
        self._new_key_dict = {}

        # fetch the keys one by one
        self._fetch_next_key()

    def _fetch_next_key(self):
        # fetches the next key in the remaining key list
        self._logger.debug(u"start fetching next key: %s", self._remaining_key_list[0])

        # TODO: set url
        headers = {'Content-Type': 'application/json',
                   'Accept': 'plain/text',
                   'Accept-Charset:': 'utf-8'}

        d = getPage(url, method='GET', headers=headers, timeout=self.time_out)
        d.addCallbacks(self._on_get_key_success, self._on_get_key_failure)
        self._key_update_defer = d

    def _on_get_key_success(self, data):
        # set key-value
        key = self._remaining_key_list[0]
        value = data.decode('utf-8')
        self._new_key_dict[key] = value

        self._logger.debug(u"successfully got key: %s = %s", key, value)

        # check if there are more keys to update
        self._remaining_key_list = self._remaining_key_list[1:]
        if self._remaining_key_list:
            self._fetch_next_key()
        else:
            # no more keys to fetch, update the config
            self._key_update_defer = None
            self._remaining_key_list = None
            self._update_config()

    def _on_get_key_failure(self, data):
        # if we failed to retrieve any of the keys, we abort the key update
        self._logger.error(u"failed to retrieve key '%s', abort key update.", self._remaining_key_list[0])
        self._logger.debug(u"failure data: %s", data)
        self._key_update_defer = None
        self._remaining_key_list = None
        self._new_key_dict = None

    def _update_config(self):
        self._logger.info(u"updating config...")
        new_key_dict = self._new_key_dict
        self._new_key_dict = None

        # make sure that all keys are valid
        for key, value in new_key_dict.items():
            if get_config_name_from_env_name(key) is None:
                self._logger.error(u"invalid key %s = %s, abort update.", key, value)
                return

        # set values
        for key, value in new_key_dict.items():
            # convert key name to section and option
            section, option = get_config_name_from_env_name(key)
            # try to figure out the value type (only string and int are supported)
            if value.isdigit():
                value = int(value)
            self.bot.config.set(section, option, value)
            self._logger.debug(u"new config values: [%s][%s] = %s", section, option, value)

        # save config file
        self.bot.save_config()
        self._logger.info(u"successfully updated config.")

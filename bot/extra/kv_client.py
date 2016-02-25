import logging

from twisted.web.client import getPage

from ..util.config import get_config_name_from_env_name


class RestKvClient(object):
    """
    A client for retrieving key-values from a RESTful Key-Value service.
    """

    def __init__(self, bot, url, key_list, time_out=10):
        # pre-check
        if len(set(key_list)) != len(key_list):
            raise RuntimeError(u"You have duplicate keys in the key list: %s", key_list)

        self._logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.url = url
        self.key_list = key_list
        self.time_out = time_out

        self._remaining_key_list = []
        self._key_update_defer = None
        self._new_key_dict = None

        self._update_in_progress = False

    def update_all_keys(self):
        """
        Triggers a task that fetches all key-values and updates the config file.
        """

        # don't do anything if there is already an update in progress
        if self._update_in_progress:
            self._logger.info(u"there is already a key update process running.")
            return
        self._update_in_progress = True
        self._logger.info(u"start fetching keys...")

        self._remaining_key_list = self.key_list[:]
        self._new_key_dict = {}

        # fetch all keys
        self._fetch_all_keys()

    def _clean_up_update_task_data(self):
        self._key_update_defer = None
        self._remaining_key_list = None
        self._new_key_dict = None
        self._update_in_progress = False

    def _fetch_all_keys(self):
        # TODO: check if there is an update in progress
        self._logger.info(u"start fetching all keys...")
        headers = {'Content-Type': 'application/json',
                   'Accept': 'plain/text',
                   'Accept-Charset:': 'utf-8'}

        d = getPage(self.url.encode('utf-8'), method='GET', headers=headers, timeout=self.time_out)
        d.addCallbacks(self._on_get_all_keys_success, self._on_get_all_keys_failure)

        self._update_in_progress = True

    def _on_get_all_keys_success(self, data):
        # assume that the data we receive is multiple lines of "key = value"
        self._logger.info(u"successfully retrieved all keys.")

        self._new_key_dict = {}
        has_errors = False
        for line in data.decode('utf-8').splitlines():
            line = line.strip()
            parts = line.split(u'=', 1)
            if len(parts) != 2:
                self._logger.error(u"invalid key-value pair in retrieved data: %s", line)
                has_errors = True
                break
            key, value = (p.strip() for p in parts)
            self._new_key_dict[key] = value

        # only update the config file if there is no errors
        if not has_errors:
            self._update_config()

        # clean up
        self._clean_up_update_task_data()

    def _on_get_all_keys_failure(self, data):
        # if we failed to retrieve the keys, we abort the key update
        self._logger.error(u"failed to retrieve all keys, abort key update.")
        self._logger.debug(u"failure data: %s", data)
        self._clean_up_update_task_data()

    def _fetch_next_key(self):
        # fetches the next key in the remaining key list
        self._logger.debug(u"start fetching next key: %s", self._remaining_key_list[0])

        # TODO: set url
        url = self.url.encode('utf-8')
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
            self._update_config()
            self._clean_up_update_task_data()

    def _on_get_key_failure(self, data):
        # if we failed to retrieve any of the keys, we abort the key update
        self._logger.error(u"failed to retrieve key '%s', abort key update.", self._remaining_key_list[0])
        self._logger.debug(u"failure data: %s", data)
        self._clean_up_update_task_data()

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

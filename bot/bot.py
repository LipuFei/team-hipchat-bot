import logging

import os
from twisted.internet import reactor

from .extra.kv_client import KvClient
from .hipchat_api import HipChatApi
from .hipchat_db import HipchatUserDb
from .hipchat_xmpp import make_client
from .schedule import Schedule
from .util.config import init_config, write_config_file_utf8
from .util.daysoff_parser import DaysOffParser


class Bot(object):

    def __init__(self, config_file, password):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.password = password
        self.config = None

        self.days_off_file = None
        self.days_off_parser = None

        self.hipchat_db = None
        self.hipchat_api = None
        self.sheriff_schedule = None
        self.hipchat_xmpp = None

        self.kv_client = None

    def initialize(self):
        self.config = init_config(self.config_file)

        self.days_off_file = self.config.get(u'team', u'daysoff_file')
        self.days_off_parser = DaysOffParser(self.days_off_file)
        self.days_off_parser.load()

        self.hipchat_db = HipchatUserDb(self,
                                        self.config.get(u'hipchat', u'api_server'),
                                        self.config.get(u'hipchat', u'auth_token'),
                                        self.config.get(u'hipchat', u'db'))

        self.hipchat_api = HipChatApi(self,
                                      self.config.get(u'hipchat', u'api_server'),
                                      self.config.get(u'hipchat', u'auth_token'))

        self.sheriff_schedule = Schedule(self)

        self.hipchat_xmpp = make_client(self, self.config, self.password)

    def start(self):
        # start the kv client to update if specified
        init_from_url = os.getenv(u'HCBOT_INIT_FROM_URL', u'').decode('utf-8').strip()
        if init_from_url:
            def check_kv_result(result):
                if not result:
                    self._logger.critical(u"failed to update config from URL, stopping...")
                    reactor.stop()
                else:
                    self._start_all()

            self._logger.info(u"Fetching configuration from URL...")
            client = KvClient(self, init_from_url, [], callback=check_kv_result)
            client.update_all_keys()
        else:
            self._start_all()

        reactor.run()

    def _start_all(self):
        self._logger.info(u"start hipchat user database...")
        self.hipchat_db.populate_user_db()

        self._logger.info(u"starting sheriff schedule...")
        self.sheriff_schedule.start()
        self._logger.info(u"starting hipchat xmpp client...")
        self.hipchat_xmpp.startService()

    def save_config(self):
        self._logger.info(u"saving config file...")
        write_config_file_utf8(self.config, self.config_file)

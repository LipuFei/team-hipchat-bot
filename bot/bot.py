import logging
import os
import sys

from twisted.internet import reactor

from .daysoff_parser import DaysOffParser
from .hipchat_api import HipChatApi
from .hipchat_db import HipchatUserDb
from .hipchat_xmpp import make_client
from .schedule import Schedule
from .extra.kv_client import RestKvClient


class Bot(object):

    def __init__(self, config_file, config, password):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.config = config
        self.password = password

        team_members = [n.strip() for n in config.get('team', 'members').decode('utf-8').strip().split(u',')]

        self.kv_client = None

        self.days_off_file = self.config.get('team', 'daysoff_file')
        self.days_off_parser = DaysOffParser(team_members, self.days_off_file)
        self.days_off_parser.load()

        self.hipchat_db = HipchatUserDb(self,
                                        self.config.get('hipchat', 'api_server'),
                                        self.config.get('hipchat', 'auth_token'),
                                        self.config.get('hipchat', 'db'))

        self.hipchat_api = HipChatApi(self,
                                      self.config.get('hipchat', 'api_server'),
                                      self.config.get('hipchat', 'auth_token'))

        # start the sheriff scheduling bot
        self.sheriff_schedule = Schedule(self, config)

        # start the XMPP bot
        self.hipchat_xmpp = make_client(self, config, self.password)

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
            client = RestKvClient(self, init_from_url, [], callback=check_kv_result)
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
        with open(self.config_file, 'wb') as f:
            self.config.write(f)

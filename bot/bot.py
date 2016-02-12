import logging

from twisted.internet import reactor

from .daysoff_parser import DaysOffParser
from .hipchat_api import HipChatApi
from .hipchat_xmpp import make_client
from .schedule import Schedule


class Bot(object):

    def __init__(self, config_file, config, password):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.config_file = config_file
        self.config = config
        self.password = password

        team_members = [n.strip() for n in config.get('team', 'members').decode('utf-8').strip().split(u',')]

        self.days_off_file = self.config.get('team', 'daysoff_file')
        self.days_off_parser = DaysOffParser(team_members, self.days_off_file)
        self.days_off_parser.load()

        self.hipchat_api = HipChatApi(self.config.get('hipchat', 'server'),
                                      self.config.get('hipchat', 'auth_token'))

        # start the sheriff scheduling bot
        self.sheriff_schedule = Schedule(self, config)

        # start the XMPP bot
        self.hipchat_xmpp = make_client(self, config, self.password)
        self.hipchat_xmpp.startService()

    def start(self):
        self._logger.info(u"starting sheriff schedule...")
        self.sheriff_schedule.start()
        self._logger.info(u"starting hipchat xmpp client...")
        self.hipchat_xmpp.startService()
        reactor.run()

    def save_config(self):
        self._logger.info(u"saving config file...")
        with open(self.config_file, 'wb') as f:
            self.config.write(f)

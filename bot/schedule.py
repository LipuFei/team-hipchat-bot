from ConfigParser import ConfigParser
import datetime
import json
import logging
import time

from crontab import CronTab
from dateutil.relativedelta import relativedelta
from twisted.internet import reactor


class Schedule(object):

    def __init__(self, bot, config):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.config = config
        self.team_members = [n.strip() for n in config.get('team', 'members').decode('utf-8').strip().split(u',')]

        self.cache_file = config.get('team', 'cache_file').decode('utf-8')
        self.cache_config = ConfigParser()
        self.cache_config.read([self.cache_file])
        if not self.cache_config.has_section('schedule'):
            self.cache_config.add_section('schedule')
        if not self.cache_config.has_option('schedule', 'last_idx'):
            self.cache_config.set('schedule', 'last_idx', 0)

        self.current_idx = self.cache_config.getint('schedule', 'last_idx')

        self.crontab = CronTab(config.get('team', 'topic_update_time'))
        self.next_scheduled_defer = None

    def start(self):
        next_time = self.crontab.next()
        self._logger.info(u"next update will be after %s", to_human_readable_time(next_time))

        self.next_scheduled_defer = reactor.callLater(next_time, self._regular_task)

    def _regular_task(self):
        # switch to the next person
        self.switch_to_next_person()

        next_time = self.crontab.next()
        self._logger.info(u"next update will be after %s", to_human_readable_time(next_time))

        self.next_scheduled_defer = reactor.callLater(next_time, self._regular_task)

    def _update_cache(self):
        self.cache_config.set('schedule', 'last_idx', self.current_idx)
        with open(self.cache_file, 'wb') as f:
            self.cache_config.write(f)

    def switch_to_next_person(self):
        current_date = datetime.date.fromtimestamp(time.time())
        next_idx, next_person_name = self.bot.days_off_parser.get_next_available_person(self.current_idx,
                                                                                        current_date)
        self._logger.info(u"today's sheriff is %s, index: %s", next_person_name, next_idx)
        self.current_idx = next_idx
        self._update_cache()

        # set room topic
        room_name = self.config.get('team', 'room_name').decode('utf-8')
        topic = self.config.get('team', 'topic_template').replace('<name>', next_person_name).decode('utf-8')
        self.bot.hipchat_api.set_room_topic(room_name, topic)

        # try to get mention name
        msg = u" >>> Today's sheriff is %s" % next_person_name
        data = None
        if self.bot.hipchat_db.has(next_person_name):
            data = json.loads(self.bot.hipchat_db.get(next_person_name), encoding='utf-8')
            mention_name = data[u'mention_name']
            msg += u" @%s" % mention_name

        # send room message
        self.bot.hipchat_api.send_room_notification(room_name, u'bot', msg,
                                                    notify=True, color='green')

        # also send private message if data is available
        if data is not None:
            user_id = data[u'id']
            msg = u"Hi %(name)s, you are the sheriff of room %(room)s today." % {u'name': data[u'name'],
                                                                                 u'room': room_name}
            msg += u"\nAll potential questions will be forwarded to you."
            self.bot.hipchat_api.send_private_message(user_id, msg)

    def get_current_person(self):
        return self.bot.days_off_parser._people_list[self.current_idx][u'name']

    def get_next_available_person(self):
        current_date = datetime.date.fromtimestamp(time.time())
        next_idx, next_person_name = self.bot.days_off_parser.get_next_available_person(self.current_idx,
                                                                                        current_date)
        return next_idx, next_person_name


def to_human_readable_time(seconds):
    attrs = [u'years', u'months', u'days', u'hours', u'minutes', u'seconds']
    delta = relativedelta(seconds=seconds)
    human_readable = [u'%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
                      for attr in attrs if getattr(delta, attr)]
    return ' '.join(human_readable)

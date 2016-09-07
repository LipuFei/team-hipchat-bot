from ConfigParser import ConfigParser
import codecs
import datetime
import json
import logging
import os
import time

from croniter import croniter
from twisted.internet import reactor

from .util.date import to_human_readable_time
from .util.team_scheduler import TeamRoundRobinScheduler


class Schedule(object):

    def __init__(self, bot):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.config = bot.config

        # team members are sorted alphabetically
        team_members = [n.strip() for n in self.config.get(u'team', u'members').strip().split(u',')]
        self.team_members = sorted(team_members)

        self._team_scheduler = TeamRoundRobinScheduler(team_members, bot.days_off_parser)

        # load cache file
        self.cache_file = self.config.get(u'team', u'cache_file')
        self.cache_config = ConfigParser()
        if os.path.exists(self.cache_config):
            with codecs.open(self.cache_file, 'r', 'utf-8') as f:
                self.cache_config.readfp(f)

        if not self.cache_config.has_section(u'schedule'):
            self.cache_config.add_section(u'schedule')
        if not self.cache_config.has_option(u'schedule', u'last_idx'):
            self.cache_config.set(u'schedule', u'last_idx', 0)

        current_idx = self.cache_config.getint(u'schedule', u'last_idx')
        self._team_scheduler.set_current_person_idx(current_idx)

        self.crontab = croniter(self.config.get(u'team', u'topic_update_time'))

        self.next_scheduled_defer = None

    def start(self):
        next_time = self.crontab.get_next() - time.time()
        self._logger.info(u"next update will be after %s", to_human_readable_time(next_time))
        self.next_scheduled_defer = reactor.callLater(next_time, self._regular_task)

    def _regular_task(self):
        # switch to the next person
        self.switch_to_next_person()

        next_time = self.crontab.get_next() - time.time()
        self._logger.info(u"next update will be after %s", to_human_readable_time(next_time))
        self.next_scheduled_defer = reactor.callLater(next_time, self._regular_task)

    def _update_cache(self):
        self.cache_config.set(u'schedule', u'last_idx', self.get_current_person()[1])
        with codecs.open(self.cache_file, 'w', 'utf-8') as f:
            self.cache_config.write(f)

    def switch_to_next_person(self):
        current_date = datetime.date.fromtimestamp(time.time())
        self._team_scheduler.switch_to_next_person(current_date)
        self._update_cache()
        self._update_hipchat_info()

    def _update_hipchat_info(self):
        current_person, person_idx = self.get_current_person()

        self._logger.info(u"today's person-on-duty is %s, index: %s", current_person, person_idx)

        # set room topic
        room_name = self.config.get(u'team', u'room_name')
        topic = self.config.get(u'team', u'topic_template').replace(u'<name>', current_person)
        self.bot.hipchat_api.set_room_topic(room_name, topic)

        # try to get mention name
        msg = u" >>> Today's person-on-duty is %s" % current_person
        data = None
        if self.bot.hipchat_db.has(current_person):
            data = json.loads(self.bot.hipchat_db.get(current_person), encoding='utf-8')
            mention_name = data[u'mention_name']
            msg += u" @%s" % mention_name

        # send room message
        self.bot.hipchat_api.send_room_notification(room_name, u'bot', msg,
                                                    notify=True, color='green')

        # also send private message if data is available
        if data is not None:
            user_id = data[u'id']
            msg = u"Hi %(name)s, you are the person-on-duty of room %(room)s today." % {u'name': data[u'name'],
                                                                                        u'room': room_name}
            msg += u"\nAll potential questions will be forwarded to you."
            self.bot.hipchat_api.send_private_message(user_id, msg)

    def get_current_person(self):
        return self._team_scheduler.get_current_person()

    def get_next_available_person(self):
        current_date = datetime.date.fromtimestamp(time.time())
        next_person_name, next_idx = self._team_scheduler.get_next_person(current_date)
        return next_idx, next_person_name

    def set_current_person(self, name):
        result = self._team_scheduler.set_current_person(name)
        if result is not None:
            self._update_cache()
            self._update_hipchat_info()
        return result

#
# Originally from https://github.com/mahmoudimus/ircer
# Modified by Lipu Fei <lipu.fei815@gmail.com>
#
import datetime
import json
import logging
import time

from twisted.internet import task
from twisted.python import log
from twisted.words.protocols.jabber import jid
from wokkel import muc
from wokkel.client import XMPPClient
from wokkel.subprotocols import XMPPHandler

from .algorithm.context import is_question_msg
from .util.daysoff_parser import sanitize_dates


class KeepAlive(XMPPHandler):
    interval = 300
    lc = None

    def connectionInitialized(self):
        self.lc = task.LoopingCall(self.ping)
        self.lc.start(self.interval)

    def connectionLost(self, *args):
        if self.lc:
            self.lc.stop()

    def ping(self):
        log.msg(u"Staying alive")
        self.send(u" ")


class HipchatBot(muc.MUCClient):

    def __init__(self, bot, server, room, room_name, nickname, stfu_minutes, team_members):
        super(HipchatBot, self).__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.connected = False
        self.server = server
        self.room = room
        self.room_name = room_name
        self.nickname = nickname
        self.stfu_minutes = int(stfu_minutes) if stfu_minutes else 0
        self.room_jid = jid.internJID(
            u'{room}@{server}/{nickname}'.format(room=self.room,
                                                 server=self.server,
                                                 nickname=self.nickname))
        self.last_spoke = None
        self.team_members = team_members

        self.last_question_time = 0.0
        self.question_rely_interval = 10.0  # one notification for questions within 10 secs

    def connectionInitialized(self):
        """The bot has connected to the xmpp server, now try to join the room.
        """
        super(HipchatBot, self).connectionInitialized()
        self.join(self.room_jid, self.nickname)
        self.connected = True

    def _stfu(self, user_nick=None):
        """Returns True if we don't want to prefix the message with @all which
        will stop the bot from push notifying HipChat users
        """
        right_now = datetime.datetime.now()
        last_spoke = self.last_spoke
        self.last_spoke = right_now
        threshold = right_now - datetime.timedelta(minutes=int(self.stfu_minutes))
        if last_spoke and last_spoke > threshold:
            return True
        return False

    def relay(self, msg, user_nick=None, quietly=False):
        muc.Room(self.room_jid, self.nickname)

        if not quietly and not self._stfu(user_nick):
            msg = u'@all ' + msg

        if not self.connected:
            log.msg(u'Not connected yet, ignoring msg: %s' % msg)
        self.groupChat(self.room_jid, msg.decode('utf-8'))

    def userJoinedRoom(self, room, user):
        pass

    def userLeftRoom(self, room, user):
        pass

    def receivedGroupChat(self, room, user, message):
        CMDS = [u'!HELP', u'!IM_BACK', u'!IM_OFF', u'!SHOW_DAYS',
                u'!SHOW_SHERIFF', u'!SHOW_NEXT_SHERIFF', u'!NEXT_SHERIFF']
        # value error means it was a one word body
        msg = message.body
        if not msg:
            return
        msg = msg.decode('utf-8').strip()

        if user is None:
            return

        cmd = msg.split(u' ')[0]
        if cmd in CMDS:
            # ignore the commands from non-members
            if user.nick not in self.team_members:
                self._logger.info(u"ignore command from non-team-member '%s'", user.nick)
            else:
                cmd_name = cmd[1:].lower()
                self._logger.info(u"try to handle command '%s' from member '%s'", cmd_name, user.nick)
                method = getattr(self, u'cmd_' + cmd[1:].lower(), None)
                if method:
                    method(room, user.nick, message)
        else:
            if user.nick in self.team_members:
                return

    def cmd_help(self, room, user_nick, message):
        msg = u"""
Available commands (all commands start with '!'):
  !HELP: show this message.
  !IM_OFF  [@someone] <args> : add your (or someone's) days off.
           - @someone : (optional) if specified, the days will be added for that person instead of you.
           - Format   : yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
  !IM_BACK [@someone] <args> : remove your (or someone's) days off.
           - @someone : (optional) if specified, the days will be removed for that person instead of you.
           - Format   : yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
  !SHOW_DAYS [@someone] : show a list of your (or someone's) days-off.
           - @someone : (optional) if specified, i will show that person's days off instead of yours.
  !SHOW_POD           : show the current person-on-duty.
  !SHOW_NEXT_POD      : show the next person-on-duty.
  !NEXT_POD           : switch to the next person-on-duty.
"""
        self.groupChat(self.room_jid, "/code " + msg.encode('utf-8'))

    def _check_at_user(self, args, default_user):
        # check if there is a '@'
        someone = None
        found_name = None
        for arg in args:
            arg = arg.strip()
            if arg.startswith(u'@'):
                found_name = arg[1:]
                arg = found_name.lower()
                for member in self.bot.sheriff_schedule.team_members:
                    if member.lower().startswith(arg):
                        someone = member
                        found_name = None
                        break
                break
        user = default_user if someone is None else someone
        return user, found_name

    def cmd_im_back(self, room, user_nick, message):
        args = message.body.decode('utf-8').split(u' ')
        valid_args, invalid_args = sanitize_dates([a.strip() for a in args[1:]] if len(args) > 1 else [])
        # check if there is a '@'
        user, found_name = self._check_at_user(invalid_args, user_nick)
        if found_name is not None:
            msg = u"could not find team member with name '%s'" % found_name
            self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))
            return

        self.bot.days_off_parser.remove(user, valid_args)
        self.bot.days_off_parser.save()

        date_list = self.bot.days_off_parser.get_my_days_off(user)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = u"%s has the following days off: [%s]" % (user, u", ".join(days))
        else:
            msg = u"%s doesn't have any days off registered" % user

        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

    def cmd_im_off(self, room, user_nick, message):
        args = message.body.decode('utf-8').split(u' ')
        valid_args, invalid_args = sanitize_dates([a.strip() for a in args[1:]] if len(args) > 1 else [])
        # check if there is a '@'
        user, found_name = self._check_at_user(invalid_args, user_nick)
        if found_name is not None:
            msg = u"could not find team member with name '%s'" % found_name
            self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))
            return

        self.bot.days_off_parser.add(user, valid_args)
        self.bot.days_off_parser.save()

        date_list = self.bot.days_off_parser.get_my_days_off(user)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = u"%s has the following days off: [%s]" % (user, u", ".join(days))
        else:
            msg = u"%s doesn't have any days off registered" % user

        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

    def cmd_show_days(self, room, user_nick, message):
        # check if there is a '@'
        args = message.body.decode('utf-8').split(u' ')
        user, found_name = self._check_at_user(args, user_nick)
        if found_name is not None:
            msg = u"could not find team member with name '%s'" % found_name
            self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))
            return

        date_list = self.bot.days_off_parser.get_my_days_off(user)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = u"%s has the following days off: [%s]" % (user, u", ".join(days))
        else:
            msg = u"%s doesn't have any days off registered" % user

        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

    def cmd_show_sheriff(self, room, user_nick, message):
        msg = u"The current person-on-duty is: %s" % self.bot.sheriff_schedule.get_current_person()[1]
        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

    def cmd_show_next_sheriff(self, room, user_nick, message):
        msg = u"Next person-on-duty is: %s" % self.bot.sheriff_schedule.get_next_available_person()[1]
        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

    def cmd_next_sheriff(self, room, user_nick, message):
        msg = u"Switching to the next person-on-duty: %s" % self.bot.sheriff_schedule.get_next_available_person()[1]
        self.groupChat(self.room_jid, "/code > " + msg.encode('utf-8'))

        self.bot.sheriff_schedule.switch_to_next_person()

    def cmd_set_sheriff(self, room, user_nick, message):
        args = message.body.decode('utf-8').split(u' ')
        if len(args) != 2:
            self.groupChat(self.room_jid, "/code > ERROR: Invalid command: " + message.body.encode('utf-8'))
            return

        name = args[1].strip()
        current_sheriff = self.bot.sheriff_schedule.set_current_person(name)
        if current_sheriff is None:
            self.groupChat(self.room_jid, "/code > ERROR: name '%s' not found" + name.encode('utf-8'))


def convert_date_list_to_strings(date_list):
    days = []
    for d in date_list:
        if isinstance(d, datetime.date):
            days.append(d.strftime('%Y-%m-%d'))
        else:
            days.append(d)
    return days


def make_client(bot, config, password):
    keepalive = KeepAlive()
    keepalive.interval = 30
    xmppclient = XMPPClient(jid.internJID(config.get('hipchat', 'jid')), password)
    xmppclient.logTraffic = True

    team_members = [n.strip() for n in config.get('team', 'members').decode('utf-8').strip().split(u',')]

    mucbot = HipchatBot(bot,
                        config.get('hipchat', 'room_server'),
                        config.get('hipchat', 'room_jid'),
                        config.get('team', 'room_name'),
                        config.get('hipchat', 'nickname'),
                        config.get('hipchat', 'stfu_minutes'),
                        team_members)
    mucbot.setHandlerParent(xmppclient)
    keepalive.setHandlerParent(xmppclient)

    return xmppclient

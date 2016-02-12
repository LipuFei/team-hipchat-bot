#
# Originally from https://github.com/mahmoudimus/ircer
# Modified by Lipu Fei <lipu.fei815@gmail.com>
#
import datetime
import re

from twisted.internet import task
from twisted.python import log
from twisted.words.protocols.jabber import jid
from wokkel import muc
from wokkel.client import XMPPClient
from wokkel.subprotocols import XMPPHandler

from .daysoff_parser import WEEKDAYS

RE_DATE = re.compile("^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$")


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

    def __init__(self, bot, server, room, nickname, stfu_minutes, team_members):
        super(HipchatBot, self).__init__()
        self.bot = bot
        self.connected = False
        self.server = server
        self.room = room
        self.nickname = nickname
        self.stfu_minutes = int(stfu_minutes) if stfu_minutes else 0
        self.room_jid = jid.internJID(
            u'{room}@{server}/{nickname}'.format(room=self.room,
                                                 server=self.server,
                                                 nickname=self.nickname))
        self.last_spoke = None
        self.team_members = team_members

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
            msg = '@all ' + msg

        if not self.connected:
            log.msg(u'Not connected yet, ignoring msg: %s' % msg)
        self.groupChat(self.room_jid, msg)

    def userJoinedRoom(self, room, user):
        pass

    def userLeftRoom(self, room, user):
        pass

    def receivedGroupChat(self, room, user, message):
        CMDS = ['!HELP', '!IM_BACK', '!IM_OFF', '!SHOW_MY_DAYS', '!SHOW_NEXT_SHERIFF', '!NEXT_SHERIFF']
        # value error means it was a one word body
        msg = message.body
        if not msg:
            return

        cmd = msg.split(' ')[0]
        if cmd in CMDS and user.nick in self.team_members:
            method = getattr(self, 'cmd_' + cmd[1:].lower(), None)
            if method:
                method(room, user.nick, message)

    def cmd_help(self, room, user_nick, message):
        msg = """
Available commands (all commands start with '!'):
  !HELP: show this message.
  !IM_OFF  <args> : add your days off. Format: yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
  !IM_BACK <args> : remove your days off. Format: yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
  !SHOW_MY_DAYS   : show a list of your days-off.
  !SHOW_NEXT_SHERIFF : show the next sheriff.
  !NEXT_SHERIFF   : switch to the next sheriff. (in case that the current sheriff is not correct)
"""
        self.groupChat(self.room_jid, "/code " + msg)

    def cmd_im_back(self, room, user_nick, message):
        args = message.body.split(' ')
        valid_args, _ = sanitize_dates([a.strip() for a in args[1:]] if len(args) > 1 else [])

        self.bot.days_off_parser.remove(user_nick, valid_args)
        self.bot.days_off_parser.save()

        date_list = self.bot.days_off_parser.get_my_days_off(user_nick)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = "%s has the following days off: [%s]" % (user_nick, ", ".join(days))
        else:
            msg = "%s doesn't have any days off registered" % user_nick

        self.groupChat(self.room_jid, '/code > ' + msg)

    def cmd_im_off(self, room, user_nick, message):
        args = message.body.split(' ')
        valid_args, _ = sanitize_dates([a.strip() for a in args[1:]] if len(args) > 1 else [])

        self.bot.days_off_parser.add(user_nick, valid_args)
        self.bot.days_off_parser.save()

        date_list = self.bot.days_off_parser.get_my_days_off(user_nick)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = "%s has the following days off: [%s]" % (user_nick, ", ".join(days))
        else:
            msg = "%s doesn't have any days off registered" % user_nick

        self.groupChat(self.room_jid, '/code > ' + msg)

    def cmd_show_my_days(self, room, user_nick, message):
        date_list = self.bot.days_off_parser.get_my_days_off(user_nick)
        if date_list:
            days = convert_date_list_to_strings(date_list)
            msg = "%s has the following days off: [%s]" % (user_nick, ", ".join(days))
        else:
            msg = "%s doesn't have any days off registered" % user_nick

        self.groupChat(self.room_jid, '/code > ' + msg)

    def cmd_show_next_sheriff(self, room, user_nick, message):
        msg = "Next sheriff is: %s" % self.bot.sheriff_schedule.get_next_available_person()[1]
        self.groupChat(self.room_jid, '/code > ' + msg)

    def cmd_next_sheriff(self, room, user_nick, message):
        msg = "Switching to the next sheriff: %s" % self.bot.sheriff_schedule.get_next_available_person()[1]
        self.groupChat(self.room_jid, '/code > ' + msg)

        self.bot.sheriff_schedule.switch_to_next_person()


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
                        config.get('hipchat', 'nickname'),
                        config.get('hipchat', 'stfu_minutes'),
                        team_members)
    mucbot.setHandlerParent(xmppclient)
    keepalive.setHandlerParent(xmppclient)

    return xmppclient


def sanitize_dates(date_string_list):
    """
    Sanitizes a given list of date strings and returns a list of valid ones
    and another list of invalid ones.
    :param date_string_list: The given date string list.
    :return: A list of valid ones and another list of invalid ones.
    """
    valid_args = []
    invalid_args = []

    for d in date_string_list:
        d = d.strip().upper()
        if len(d) == 0:
            continue
        if RE_DATE.match(d):
            try:
                year, month, day = [int(v) for v in d.split('-')]
                valid_args.append(datetime.date(year, month, day))
            except:
                invalid_args.append(d)
        elif d in WEEKDAYS:
            valid_args.append(d)
        else:
            invalid_args.append(d)

    return valid_args, invalid_args

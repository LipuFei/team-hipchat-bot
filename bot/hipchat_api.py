import cgi
import json
import logging
import time
from urllib import quote

from twisted.internet import reactor
from twisted.web.client import getPage


CHECK_HISTORY_INTERVAL = 2.0


class HipChatApi(object):
    ROOM_NOTIFICATION_URL = u"v2/room/%(room_id_or_name)s/notification"
    ROOM_TOPIC_URL = u"v2/room/%(room_id_or_name)s/topic"
    ROOM_HISTORY_URL = u"v2/room/%(room_id_or_name)s/history"
    ROOM_REPLY_URL = u"v2/room/%(room_id_or_name)s/reply"
    PRIVATE_MESSAGE_URL = u"v2/user/{id_or_email}/message"

    def __init__(self, bot, server, token):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.bot = bot
        self.server = server
        self.token = token
        self._callback = None

        self._api_interval = 4.0
        self._last_time = 0.0

    def _get_later(self):
        current_time = time.time()
        later = self._last_time + self._api_interval - current_time
        if later < 0.0:
            later = 0.0

        self._last_time = current_time + later
        return later

    def _send_request(self, method, url, payload=None, success_callback=None, failure_callback=None):
        final_url = u"https://%(server)s/%(url)s?auth_token=%(token)s" % {u"server": self.server,
                                                                          u"url": quote(url),
                                                                          u"token": self.token}
        self._logger.debug(u"sending request to url %s", final_url)
        headers = {'Content-Type': 'application/json',
                   'Accept': 'plain/text',
                   'Accept-Charset:': 'utf-8'}

        method = method.encode('utf-8')
        final_url = final_url.encode('utf-8')
        payload = payload.encode('utf-8') if payload is not None else None

        def get_page(u, m, h, p, t, c1, c2):
            d = getPage(u, method=m, headers=h, postdata=p, timeout=t)
            if c1 is not None:
                d.addCallback(c1)
            if c2 is not None:
                d.addErrback(c2)

        later = self._get_later()
        reactor.callLater(later, get_page, final_url, method, headers, payload, 10.0,
                          success_callback, failure_callback)

    def send_room_notification(self, room_name, username, message, is_html=False, notify=False, color=u"yellow"):
        url = self.ROOM_NOTIFICATION_URL % {u"room_id_or_name": room_name}
        data = {u'from': username,
                u'message_format': u'html' if is_html else u'text',
                u'color': color,
                u'notify': notify,
                u'message': cgi.escape(message) if is_html else message,
                }
        self._send_request(u'POST', url, payload=json.dumps(data))

    def set_room_topic(self, room_name, topic):
        url = self.ROOM_TOPIC_URL % {u"room_id_or_name": room_name}
        data = {u'topic': topic}
        self._send_request(u'PUT', url, payload=json.dumps(data))

    def view_room_history(self, room_name, max_results=100, recent=True, include_deleted=False,
                          not_before=None, timezone="UTZ", callback=None):
        url = self.ROOM_HISTORY_URL % {u"room_id_or_name": room_name}
        if recent:
            url += u"/latest"
        data = {u'max-results': max_results,
                u'timezone': timezone,
                u'include_deleted': include_deleted,
                }
        if not_before is not None:
            data[u'not-before'] = not_before
        self._callback = callback
        self._send_request(u'GET', url, payload=json.dumps(data),
                           success_callback=self._on_view_room_history_success,
                           failure_callback=self._on_view_room_history_failed)

    def _on_view_room_history_success(self, data):
        self._logger.info(u"successfully retrieved history")
        self._callback(data)

    def _on_view_room_history_failed(self, response):
        self._logger.error(u"failed to retrieve history: %s", response)

    def reply_to_message(self, room_name, parent_message_id, message):
        url = self.ROOM_REPLY_URL % {u'room_id_or_name': room_name}
        data = {u'parentMessageId': parent_message_id,
                u'message': message,
                }
        self._send_request(u'POST', url, payload=json.dumps(data))

    def send_private_message(self, id_or_email, message, notify=False, is_html=False):
        url = self.PRIVATE_MESSAGE_URL % {u'id_or_email': id_or_email}
        data = {u'message': cgi.escape(message) if is_html else message,
                u'notify': notify,
                u'message_format': u'html' if is_html else u'text'
                }
        self._send_request(u'POST', url, payload=json.dumps(data))

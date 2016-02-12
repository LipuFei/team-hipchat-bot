import cgi
import json
import logging
from urllib import quote

from twisted.web.client import getPage


CHECK_HISTORY_INTERVAL = 2.0


class HipChatApi(object):
    ROOM_NOTIFICATION_URL = u"v2/room/%(room_id_or_name)s/notification"
    ROOM_TOPIC_URL = u"v2/room/%(room_id_or_name)s/topic"
    ROOM_HISTORY_URL = u"v2/room/%(room_id_or_name)s/history"
    ROOM_REPLY_URL = u"v2/room/%(room_id_or_name)s/reply"

    def __init__(self, server, token):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.server = server
        self.token = token
        self._callback = None

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
        d = getPage(final_url, method=method, headers=headers, postdata=payload, timeout=10)
        if success_callback is not None:
            d.addCallback(success_callback)
        if failure_callback is not None:
            d.addErrback(failure_callback)

    def send_room_notification(self, room_name, username, message, is_html=False, notify=False, color="yellow"):
        url = self.ROOM_NOTIFICATION_URL % {"room_id_or_name": room_name}
        data = {'from': username,
                'message_format': 'html' if is_html else 'text',
                'color': color,
                'notify': notify,
                'message': cgi.escape(message),
                }
        self._send_request('POST', url, payload=json.dumps(data))

    def set_room_topic(self, room_name, topic):
        url = self.ROOM_TOPIC_URL % {"room_id_or_name": room_name}
        data = {'topic': topic}
        self._send_request('PUT', url, payload=json.dumps(data))

    def view_room_history(self, room_name, max_results=100, recent=True, include_deleted=False,
                          not_before=None, timezone="UTZ", callback=None):
        url = self.ROOM_HISTORY_URL % {"room_id_or_name": room_name}
        if recent:
            url += "/latest"
        data = {'max-results': max_results,
                'timezone': timezone,
                'include_deleted': include_deleted,
                }
        if not_before is not None:
            data['not-before'] = not_before
        self._callback = callback
        self._send_request('GET', url, payload=json.dumps(data),
                           success_callback=self._on_view_room_history_success,
                           failure_callback=self._on_view_room_history_failed)

    def _on_view_room_history_success(self, data):
        self._logger.info("successfully retrieved history")
        self._callback(data)

    def _on_view_room_history_failed(self, response):
        self._logger.error("failed to retrieve history: %s", response)

    def reply_to_message(self, room_name, parent_message_id, message):
        url = self.ROOM_REPLY_URL % {"room_id_or_name": room_name}
        data = {'parentMessageId': parent_message_id,
                'message': message,
                }
        self._send_request('POST', url, payload=json.dumps(data))

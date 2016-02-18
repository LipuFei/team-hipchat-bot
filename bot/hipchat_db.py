import json
import logging
import time

import leveldb
from twisted.internet import reactor
from twisted.web.client import getPage


class HipchatUserDb(object):

    def __init__(self, bot, server, token, db_path):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.bot = bot
        self.server = server
        self.token = token

        self._db = leveldb.LevelDB(db_path)
        self._update_interval = 60.0 * 60.0 * 24.0 * 5.0  # every 5 days

        self._fetch_interval = 5.0
        self._last_time = 0.0

    def set(self, name, mention_name):
        self._db.Put(name.encode('utf-8'), mention_name.encode('utf-8'))

    def get(self, name):
        return self._db.Get(name.encode('utf-8'))

    def has(self, name):
        result = True
        try:
            self._db.Get(name.encode('utf-8'))
        except KeyError:
            result = False
        return result

    def _append_auth_token(self, url):
        final_url = url + (u'?auth_token=%s' if url.find(u'?') == -1 else u'&auth_token=%s')
        final_url = final_url % self.token
        return final_url

    def _get_later(self):
        current_time = time.time()
        later = self._last_time + self._fetch_interval - current_time
        if later < 0.0:
            later = 0.0

        self._last_time = current_time + later
        return later

    def populate_user_db(self):
        self._logger.info(u"starting fetching users...")
        final_url = u"https://%(server)s/v2/user" % {u"server": self.server}
        final_url = self._append_auth_token(final_url)

        later = self._get_later()
        reactor.callLater(later, self._get_page, final_url,
                          self._got_user_list_success, self._got_user_list_failure)

    def _get_page(self, url, callback1, callback2):
        getPage(url.encode('utf-8')).addCallbacks(callback1, callback2)

    def _got_user_list_success(self, data):
        result_dict = json.loads(data, encoding='utf-8')
        # get user details
        for user in result_dict.get(u'items', []):
            if u'name' in user and u'mention_name' in user:
                link = user.get(u'links', {}).get(u'self')
                if link is not None:
                    # get full info
                    final_url = self._append_auth_token(link)
                    later = self._get_later()
                    reactor.callLater(later, self._get_page, final_url,
                                      self._got_user_success, self._got_user_failure)

        # get next page
        next_link = result_dict.get(u'links', {}).get(u'next')
        if next_link is not None:
            final_url = self._append_auth_token(next_link)
            later = self._get_later()
            reactor.callLater(later, self._get_page, final_url,
                              self._got_user_list_success, self._got_user_list_failure)

    def _got_user_list_failure(self, result):
        self._logger.error(u"failed to get user list: %s", repr(result))

    def _got_user_success(self, data):
        user = json.loads(data, encoding='utf-8')
        self.set(user[u'name'], data.encode('utf-8'))
        self._logger.info(u"user details updated.")

    def _got_user_failure(self, result):
        self._logger.error(u"failed to get user details: %s", repr(result))

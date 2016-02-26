import codecs
import datetime
import logging
import os
import re
import time

WEEKDAYS = [u"MON", u"TUE", u"WED", u"THU", u"FRI"]

RE_DATE = re.compile("^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$")


class DaysOffParser(object):
    """
    This parser manages a list of people and their days-off lists.
    """

    def __init__(self, file_name=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._file_name = file_name
        self._data_dict = {}

    def load(self, file_name=None):
        """
        Loads the people availability list from the given file.
        :param file_name: The file name.
        """
        file_name = file_name if file_name is not None else self._file_name

        self._logger.debug(u"loading people availability list from %s", file_name)
        lines = []
        if os.path.exists(file_name):
            with codecs.open(file_name, 'r', 'utf-8') as f:
                lines = [l.strip() for l in f.readlines()]

        data_dict = {}
        person_name = None
        date_string_list = None
        for l in lines:
            if l.startswith(u'[') and l.endswith(u']'):
                if person_name is not None:
                    data_dict[person_name] = sanitize_dates(date_string_list)[0]
                person_name = l.strip(u'[]')
                date_string_list = []
            elif l.startswith(u'#') or len(l) == 0:
                continue
            else:
                date_string_list.append(l)
        if person_name is not None:
            data_dict[person_name] = sanitize_dates(date_string_list)[0]

        self._data_dict = data_dict
        self.save(file_name)

    def save(self, file_name=None):
        """
        Saves the people availability list to the given file.
        :param file_name: The file name.
        """
        self._automatic_clean()

        file_name = file_name if file_name is not None else self._file_name
        if file_name is None:
            return

        # sort the people list
        people_list = [{u'name': name, u'date_list': date_list} for name, date_list in self._data_dict.iteritems()]
        people_list = sorted(people_list, key=lambda p: p[u'name'])

        self._logger.debug(u"saving people availability list to %s", file_name)
        lines = []
        for person in people_list:
            lines.append(u"[%s]" % person[u'name'])
            for d in person[u'date_list']:
                if isinstance(d, basestring):
                    lines.append(d.upper())
                else:
                    lines.append(d.strftime(u"%Y-%m-%d"))
            lines.append(u"")

        lines = [l + os.linesep for l in lines]
        with codecs.open(file_name, 'w', 'utf-8') as f:
            f.writelines(lines)

    def _automatic_clean(self):
        """
        Automatically cleans up the past dates.
        """
        current_date = datetime.date.fromtimestamp(time.time())
        for name, date_list in self._data_dict.iteritems():
            new_list = []
            for d in date_list:
                if isinstance(d, datetime.date) and d < current_date:
                    continue
                new_list.append(d)
            self._data_dict[name] = new_list

    def add(self, name, date_string_list):
        """
        Adds the given list of not-available dates for the given person.
        :param name: The person's name.
        :param date_string_list: The not-available date strings to add.
        :return: True or False indicating if there is any change being made.
        """
        new_person = name not in self._data_dict
        has_change = False

        person_date_list = self._data_dict.get(name, [])

        # add dates
        valid_date_list, _ = sanitize_dates(date_string_list)
        for nd in valid_date_list:
            if nd not in person_date_list:
                person_date_list.append(nd)
                has_change = True

        # add to list if it's a new person and there is any valid change
        if new_person and has_change:
            self._data_dict[name] = person_date_list

        return has_change

    def remove(self, name, date_string_list):
        """
        Removes the given list of not-available dates for the given person.
        :param name: The person's name.
        :param date_string_list: The not-available dates to remove.
        :return: True or False indicating if there is any change being made.
        """
        if name not in self._data_dict:
            return False
        person_data_list = self._data_dict[name]

        # remove
        has_change = False
        valid_data_list, _ = sanitize_dates(date_string_list)
        for nd in valid_data_list:
            if nd in person_data_list:
                person_data_list.remove(nd)
                has_change = True
                # remove this person if the date list becomes empty
                if not person_data_list:
                    del self._data_dict[name]
                    break

        return has_change

    def get_my_days_off(self, name):
        """
        Gets the given person's days-off list.
        :param name: The given person's name.
        :return: The list if the person exists, otherwise None.
        """
        return self._data_dict.get(name)

    def check_availability(self, name, date):
        """
        Checks if the given person is available at the given date.
        :param name: The given person's name.
        :param date: The given date string.
        :return: True or False.
        """
        # saving does the automatic cleanup
        self.save()

        if name not in self._data_dict:
            return True

        is_available = True
        for d in self._data_dict[name]:
            # convert weekday to date
            if isinstance(d, basestring):
                is_available = WEEKDAYS.index(d) != date.weekday()
                if not is_available:
                    break
            elif date == d:
                is_available = False
                break

        return is_available


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
                year, month, day = [int(v) for v in d.split(u'-')]
                valid_args.append(datetime.date(year, month, day))
            except:
                invalid_args.append(d)
        elif d in WEEKDAYS:
            valid_args.append(d)
        else:
            invalid_args.append(d)

    return valid_args, invalid_args


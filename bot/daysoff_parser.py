import datetime
import logging
import os
import time

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI"]


class DaysOffParser(object):

    def __init__(self, team_member_list, file_name=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._people_list = []
        self._team_member_list = team_member_list
        self._file_name = file_name

    def load(self, file_name=None):
        """
        Loads the people availability list from the given file.
        :param file_name: The file name.
        """
        file_name = file_name if file_name is not None else self._file_name

        self._logger.debug("loading people availability list from %s", file_name)
        lines = []
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                lines = [l.decode('utf-8') for l in f.readlines()]

        people_list = []
        person = None
        for l in lines:
            l = l.strip()
            if l.startswith('[') and l.endswith(']'):
                if person is not None:
                    people_list.append(person)
                person = {'name': l.strip('[]'),
                          'not_available_dates': []}
            elif l.startswith('#') or len(l) == 0:
                continue
            else:
                if l.upper() in WEEKDAYS:
                    person['not_available_dates'].append(l.upper())
                else:
                    year, month, day = [int(v) for v in l.split('-')]
                    person['not_available_dates'].append(datetime.date(year, month, day))

        if person is not None:
            people_list.append(person)

        got_names = [p['name'] for p in people_list]
        non_existing_names = [n for n in self._team_member_list if n not in got_names]
        for name in non_existing_names:
            people_list.append({'name': name,
                                'not_available_dates': []})

        self._people_list = people_list
        self.save(file_name)

    def save(self, file_name=None):
        """
        Saves the people availability list to the given file.
        :param file_name: The file name.
        """
        self._automatic_clean()

        file_name = file_name if file_name is not None else self._file_name

        self._logger.debug("saving people availability list to %s", file_name)
        lines = []
        for person in self._people_list:
            lines.append("[%s]" % person['name'])
            for d in person['not_available_dates']:
                if isinstance(d, basestring):
                    lines.append(d.upper())
                else:
                    lines.append(d.strftime("%Y-%m-%d"))
            lines.append("")

        lines = [(l + os.linesep).encode('utf-8') for l in lines]
        with open(file_name, 'wb') as f:
            f.writelines(lines)

    def _automatic_clean(self):
        """
        Automatically cleans up the past dates.
        """
        current_date = datetime.date.fromtimestamp(time.time())
        for person in self._people_list:
            new_list = []
            for d in person['not_available_dates']:
                if isinstance(d, datetime.date) and d < current_date:
                    continue
                new_list.append(d)
            person['not_available_dates'] = new_list

    def add(self, name, date_list):
        """
        Adds the given list of not-available dates for the given person.
        :param name: The person's name.
        :param date_list: The not-available dates to add.
        :return: True or False indicating if there is any change being made.
        """
        has_change = False
        found_person = False
        for person in self._people_list:
            if person['name'] == name:
                for nd in date_list:
                    if isinstance(nd, basestring):
                        nd = nd.upper()
                    if nd not in person['not_available_dates']:
                        person['not_available_dates'].append(nd)
                        has_change = True
                found_person = True
                break

        # append if this person doesn't exist
        if not found_person:
            person = {'name': name, 'not_available_dates': date_list}
            self._people_list.append(person)
            has_change = True

        return has_change

    def remove(self, name, date_list):
        """
        Removes the given list of not-available dates for the given person.
        :param name: The person's name.
        :param date_list: The not-available dates to remove.
        :return: True or False indicating if there is any change being made.
        """
        has_change = False
        for person in self._people_list:
            if person['name'] == name:
                for nd in date_list:
                    if isinstance(nd, basestring):
                        nd = nd.upper()
                    if nd in person['not_available_dates']:
                        person['not_available_dates'].remove(nd)
                        has_change = True
        return has_change

    def get_my_days_off(self, name):
        """
        Gets the given person's days-off list.
        :param name: The given person's name.
        :return: The list if the person exists, otherwise None.
        """
        days_off = None
        for person in self._people_list:
            if person['name'] == name:
                days_off = person['not_available_dates']
        return days_off

    def get_next_available_person(self, current_idx, date):
        idx = (current_idx + 1) % len(self._people_list)
        while idx != current_idx:
            person = self._people_list[idx]
            if self.check_availability(person['name'], date):
                return idx, person['name']
            idx = (current_idx + 1) % len(self._people_list)

        idx = (current_idx + 1) % len(self._people_list)
        return idx, self._people_list[idx]['name']

    def check_availability(self, name, date):
        """
        Checks if the given person is available at the given date.
        :param name: The given person's name.
        :param date: The given date.
        :return: True or False.
        """
        self.save()

        is_available = None
        for person in self._people_list:
            if person['name'] == name:
                is_available = True
                for d in person['not_available_dates']:
                    # convert weekday to date
                    if isinstance(d, basestring):
                        is_available = WEEKDAYS.index(d) != date.weekday()
                        if not is_available:
                            break
                    elif date == d:
                        is_available = False
                        break
                break
        if is_available is None:
            raise RuntimeError("name[%s] not found" % name)

        return is_available

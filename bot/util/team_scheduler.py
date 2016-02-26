class TeamRoundRobinScheduler(object):
    """
    A round robin scheduler for switching man on duty in a team on a daily basis.
    """

    def __init__(self, teammate_list, daysoff_parser):
        self._teammate_list = teammate_list
        self._daysoff_parser = daysoff_parser
        self._idx = 0

    @property
    def teammate_list(self):
        return self._teammate_list

    def get_current_person(self):
        """
        Gets the current person's name and index.
        :return: The current person's name and index.
        """
        return self._teammate_list[self._idx], self._idx

    def set_current_person(self, name):
        """
        Sets the current person to the given one.
        :param name: The name of the person to set to.
        :return: The person's name if successful, otherwise None.
        """
        person_idx = None
        for idx in xrange(len(self._teammate_list)):
            if self._teammate_list[idx].lower().startswith(name.lower()):
                person_idx = idx
                break
        if person_idx is None:
            return
        self._idx = person_idx
        return self._teammate_list[person_idx]

    def set_current_person_idx(self, idx):
        """
        Sets the current person index.
        :param idx: The index (will be set to 'idx mod len(teammate_list)').
        """
        self._idx = idx % len(self._teammate_list)

    def check_availability(self, name, check_date):
        """
        Checks if a person is available on the given date.
        :param name: Team member name.
        :param check_date: The given date.
        :return: True or False.
        """
        if name not in self._teammate_list:
            return True
        return self._daysoff_parser.check_availability(name, check_date)

    def get_next_person(self, check_date=None):
        """
        Gets the next man on duty.
        If a date in given, people's availabilities on that day will be taken into account.
        :param check_date: The given date.
        :return: The next person and the index.
        """
        idx = (self._idx + 1) % len(self._teammate_list)

        if check_date is not None:
            while idx != self._idx:
                if self.check_availability(self._teammate_list[idx], check_date):
                    break
                idx = (idx + 1) % len(self._teammate_list)
            # if nobody is available on that day, just switch to the next one in the list
            if idx == self._idx and not self.check_availability(self._teammate_list[idx], check_date):
                idx = (idx + 1) % len(self._teammate_list)

        return self._teammate_list[idx], idx

    def switch_to_next_person(self, check_date=None):
        """
        Switches to the next person.
        If a date in given, people's availabilities on that day will be taken into account.
        :param check_date: The given date.
        :return: The next person and the index.
        """
        person, idx = self.get_next_person(check_date)
        self._idx = idx
        return self.get_current_person()

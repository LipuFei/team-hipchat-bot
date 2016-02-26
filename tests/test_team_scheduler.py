import datetime
import time
import unittest

from bot.util.daysoff_parser import DaysOffParser
from bot.util.team_scheduler import TeamRoundRobinScheduler


class TeamRoundRobinSchedulerTest(unittest.TestCase):
    """
    Tests for TeamRoundRobinScheduler.
    """

    def test_check_availability(self):
        """
        Tests check_availability().
        """
        team_list = [u'alice', u'bob']
        parser = DaysOffParser()
        scheduler = TeamRoundRobinScheduler(team_list, parser)

        self.assertTrue(scheduler.check_availability(u'alice', datetime.date.fromtimestamp(time.time())),
                        u"alice should be available today.")

        # 2016-02-22 is a Monday
        parser.add(u'alice', [u'MON'])
        self.assertFalse(scheduler.check_availability(u'alice', datetime.date(2016, 2, 22)),
                         u"alice should not be available on 2016-02-22.")

        self.assertTrue(scheduler.check_availability(u'charley', datetime.date(2016, 2, 22)),
                        u"alice should not be available on 2016-02-22.")

    def test_set_get_current_person(self):
        """
        Tests setting and getting the current person.
        """
        team_list = [u'alice', u'bob']
        parser = DaysOffParser()
        scheduler = TeamRoundRobinScheduler(team_list, parser)

        self.assertEqual((u'alice', 0), scheduler.get_current_person(),
                         u"The current person should be alice.")
        self.assertEqual((u'bob', 1), scheduler.get_next_person(),
                         u"The next person should be bob.")

        scheduler.set_current_person_idx(1)
        self.assertEqual((u'bob', 1), scheduler.get_current_person(),
                         u"The current person should be bob.")
        self.assertEqual((u'alice', 0), scheduler.get_next_person(),
                         u"The next person should be alice.")

        self.assertEqual((u'alice', 0), scheduler.switch_to_next_person(),
                         u"The current person should be alice.")

    def test_switch_with_availability(self):
        """
        Tests switching person with availability check.
        """
        team_list = [u'alice', u'bob']
        parser = DaysOffParser()
        scheduler = TeamRoundRobinScheduler(team_list, parser)

        # 2016-02-22 is a Monday
        parser.add(u'alice', [u'MON'])
        monday = datetime.date(2016, 2, 22)

        self.assertEqual((u'bob', 1), scheduler.switch_to_next_person(monday),
                         u"The current person should be bob.")

        self.assertEqual((u'bob', 1), scheduler.switch_to_next_person(monday),
                         u"The current person should be bob.")

        parser.remove(u'alice', [u'MON'])
        self.assertEqual((u'alice', 0), scheduler.switch_to_next_person(monday),
                         u"The current person should be alice.")

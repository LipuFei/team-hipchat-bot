import datetime
import tempfile
import time
import unittest

import codecs
import os

from bot.util.daysoff_parser import DaysOffParser, sanitize_dates

BASE_DIR = os.path.dirname(os.path.realpath(__file__)).decode('utf-8')


class DaysOffParserTest(unittest.TestCase):
    """
    Tests for the DaysOffParser.
    """

    def setUp(self):
        fd, self.temp_file = tempfile.mkstemp()
        os.close(fd)

    def tearDown(self):
        os.remove(self.temp_file)
        self.temp_file = None

    def test_read_file_empty(self):
        """
        Tests reading an empty file.
        """
        parser = DaysOffParser()
        parser.load(self.temp_file)

        # people list should be sorted
        self.assertEqual(0, len(parser._data_dict),
                         u"_data_dict should be empty.")

    def test_read_file_with_expired_dates(self):
        """
        Tests reading a days-off file with expired dates.
        """
        # copy data to a temporary file
        src_file_path = os.path.join(BASE_DIR, u'data', u'days-off-with-expired-dates.txt')
        with codecs.open(src_file_path, 'r', 'utf-8') as f1:
            data = f1.read()
            with codecs.open(self.temp_file, 'w', 'utf-8') as f2:
                f2.write(data)

        parser = DaysOffParser()
        parser.load(self.temp_file)

        alice_days_off = parser.get_my_days_off(u'alice')
        self.assertNotIn(u'2016-01-02', alice_days_off,
                         u"'2016-01-02' should NOT be in alice's days-off list.")
        self.assertIn(u'MON', alice_days_off,
                      u"'MON' should be in alice's days-off list.")

        bob_days_off = parser.get_my_days_off(u'bob')
        self.assertNotIn(u'2016-01-01', bob_days_off,
                         u"'2016-01-01' should NOT be in bob's days-off list.")
        self.assertIn(u'TUE', bob_days_off,
                      u"'TUE' should be in bob's days-off list.")

        # check the written file
        with codecs.open(self.temp_file, 'r', 'utf-8') as f:
            lines = [l.strip() for l in f.readlines() if len(l.strip()) > 0]
        self.assertEqual(len(lines), 4,
                         u"should have 4 non-empty lines in the updated days-off file (got %s)." % repr(lines))
        self.assertEqual(u'[alice]', lines[0],
                         u"line '[alice]' not found in the updated days-off file.")
        self.assertEqual(u'MON', lines[1],
                         u"line 'MON' not found in the updated days-off file.")
        self.assertEqual(u'[bob]', lines[2],
                         u"line '[bob]' not found in the updated days-off file.")
        self.assertEqual(u'TUE', lines[3],
                         u"line 'TUE' not found in the updated days-off file.")

    def test_add_remove_dates(self):
        """
        Tests adding and removing dates.
        """
        # copy data to a temporary file
        src_file_path = os.path.join(BASE_DIR, u'data', u'days-off-with-expired-dates.txt')
        with codecs.open(src_file_path, 'r', 'utf-8') as f1:
            data = f1.read()
            with codecs.open(self.temp_file, 'w', 'utf-8') as f2:
                f2.write(data)

        parser = DaysOffParser()
        parser.load(self.temp_file)

        self.assertIn(u'MON', parser.get_my_days_off(u'alice'),
                      u"'MON' should be in alice's days-off list.")
        # remove
        parser.remove(u'alice', [u'MON'])
        self.assertIsNone(parser.get_my_days_off(u'alice'),
                          u"alice's days-off list should be empty after removal.")

        # add
        parser.add(u'alice', [u'WED'])
        self.assertIn(u'WED', parser.get_my_days_off(u'alice'),
                      u"'WED' should be in alice's days-off list after addition: %s")
        self.assertEqual(len(parser.get_my_days_off(u'alice')), 1,
                         u"'alice' should have only one day-off.")

        # add for a new person
        parser.add(u'charley', [u'MON'])
        self.assertIn(u'MON', parser.get_my_days_off(u'charley'),
                      u"'MON' should be in charley's days-off list after addition.")

    def test_availability(self):
        """
        Tests check_availability().
        """
        # copy data to a temporary file
        src_file_path = os.path.join(BASE_DIR, u'data', u'days-off-with-expired-dates.txt')
        with codecs.open(src_file_path, 'r', 'utf-8') as f1:
            data = f1.read()
            with codecs.open(self.temp_file, 'w', 'utf-8') as f2:
                f2.write(data)

        parser = DaysOffParser()
        parser.load(self.temp_file)

        # 2016-02-22 is a Monday
        self.assertFalse(parser.check_availability(u'alice', datetime.date(2016, 2, 22)),
                         u"'alice' should NOT be available on Monday 2016-2-22.")
        # 2016-02-23 is a Tuesday
        self.assertTrue(parser.check_availability(u'alice', datetime.date(2016, 2, 23)),
                        u"'alice' should be available on Tuesday 2016-2-23.")

        parser.remove(u'alice', u'mon')

        # add today
        today_date = datetime.date.fromtimestamp(time.time())
        today_string = today_date.strftime(u"%Y-%m-%d")
        parser.add(u'alice', [today_string])
        self.assertFalse(parser.check_availability(u'alice', today_date),
                         u"'alice' should NOT be available today after addition.")

    def test_sanitize_dates(self):
        """
        Tests sanitize_dates().
        """
        valid, invalid = sanitize_dates([u'mon', u'1234', u'vsdf', u'2015-01-01'])
        self.assertEquals([u'MON', datetime.date(2015, 1, 1)], valid,
                          u"'MON' and 2015-01-01 should be in valid_list.")
        self.assertEquals([u'1234', u'VSDF'], invalid,
                          u"'1234' and 'VSDF' should be in invalid_list.")

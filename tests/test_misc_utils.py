import unittest

from bot.util.date import to_human_readable_time


class DaysOffParserTest(unittest.TestCase):
    """
    Tests for miscellaneous util functions.
    """
    def test_to_human_readable_time(self):
        """
        Tests to_human_readable_time().
        """
        time_string = to_human_readable_time(3599.0)
        self.assertEqual(u"59 minutes 59 seconds", time_string,
                         u"should get '59 minutes 59 seconds'.")

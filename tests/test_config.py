import os
import tempfile
import unittest

from bot.util import config

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class TestConfig(unittest.TestCase):
    """
    Tests for configuration code.
    """

    def setUp(self):
        fd, self.temp_config_file = tempfile.mkstemp()
        os.close(fd)

    def tearDown(self):
        os.remove(self.temp_config_file)
        self.temp_config_file = None

    def test_init_config_empty(self):
        """
        Tests initialization with an empty config file.
        """
        config_parser = config.init_config(self.temp_config_file)
        self.assertTrue(config_parser.has_option(u'team', u'topic_update_time'),
                        u"[team][topic_update_time] not found")
        self.assertEqual(config_parser.get(u'team', u'topic_update_time'), u'0 9 * * MON-FRI *',
                         u"[team][topic_update_time] mismatch")

    def test_init_config_not_a_file(self):
        """
        Tests initialization with a path that's not pointing to a file.
        """
        self.assertRaises(RuntimeError, config.init_config, u'/etc')

    def test_init_config(self):
        """
        Tests initialization with a non-empty config file.
        """
        # copy example-config.ini
        with open(os.path.join(BASE_DIR, u'data', u'example-config.ini'), 'rb') as ef:
            data = ef.read()
        with open(self.temp_config_file, 'wb') as f:
            f.write(data)

        config_parser = config.init_config(self.temp_config_file)
        self.assertTrue(config_parser.has_option(u'team', u'topic_update_time'),
                        u"[team][topic_update_time] not found: %s" % repr(config_parser.items(u'team')))
        self.assertEqual(config_parser.get(u'team', u'topic_update_time'), u'0 8 * * MON-FRI *',
                         u"[team][topic_update_time] mismatch")

    def test_set_default_all(self):
        """
        Tests set_default_config() with set_all=True.
        """
        # copy example-config.ini
        with open(os.path.join(BASE_DIR, u'data', u'example-config.ini'), 'rb') as ef:
            data = ef.read()
        with open(self.temp_config_file, 'wb') as f:
            f.write(data)

        config_parser = config.init_config(self.temp_config_file)
        config.set_default_config(config_parser, set_all=True)
        self.assertEqual(config_parser.get(u'team', u'topic_update_time'), u'0 9 * * MON-FRI *',
                         u"[team][topic_update_time] mismatch")

    def test_get_config_name_from_env(self):
        """
        Tests get_config_name_from_env_name().
        """
        env_name = u'HCBOT_HIPCHAT_JID'
        sec, opt = config.get_config_name_from_env_name(env_name)
        self.assertEqual((u'hipchat', u'jid'), (sec, opt),
                         u"config names mismatch: %s %s" % (sec, opt))

        env_name = u'HCBOT_HIPCHAT_JID123'
        result = config.get_config_name_from_env_name(env_name)
        self.assertIsNone(result, u"should not find a matching config name")

        # not starts with HCBOT
        env_name = u'HCBOT1_HIPCHAT_JID'
        result = config.get_config_name_from_env_name(env_name)
        self.assertIsNone(result, u"should not find a matching config name")

        # has less separators
        env_name = u'HCBOT_HIPCHAT'
        result = config.get_config_name_from_env_name(env_name)
        self.assertIsNone(result, u"should not find a matching config name")

    def test_override_config_with_env(self):
        """
        Tests override_config_with_env().
        """
        config_parser = config.init_config(self.temp_config_file)
        config.set_default_config(config_parser, set_all=True)

        os.environ['HCBOT_HIPCHAT_JID'] = '123'
        config.override_config_with_env(config_parser)
        self.assertEqual(config_parser.get(u'hipchat', u'jid'), u'123',
                         u"[hipchat][jid] mismatch")

        # test integer
        os.environ['HCBOT_HIPCHAT_STFU_MINUTES'] = u'2'
        config.override_config_with_env(config_parser)
        self.assertIs(config_parser.getint(u'hipchat', u'stfu_minutes'), 2,
                      u"[hipchat][stfu_minutes] mismatch")

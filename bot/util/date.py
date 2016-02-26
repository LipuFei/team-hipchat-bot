from dateutil.relativedelta import relativedelta


def to_human_readable_time(seconds):
    """
    Convert the given timestamp (in seconds) to a human-readable string.
    :param seconds: The given timestamp (in seconds)
    :return: A human-readable string.
    """
    attrs = [u'years', u'months', u'days', u'hours', u'minutes', u'seconds']
    delta = relativedelta(seconds=seconds)
    human_readable = [u'%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
                      for attr in attrs if getattr(delta, attr)]
    return ' '.join(human_readable)

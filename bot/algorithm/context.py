def is_question_msg(message):
    """
    Checks if the given message is a question.
    :param message: The given message.
    :return: True or False.
    """
    result = False
    msg = message.strip().lower()
    if msg.endswith(u'?'):
        result = True

    return result

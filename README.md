# A simple Hipchat bot

Some team may have support rooms on Hipchat, and the teammates may take turn to be the man-on-duty each day
who is responsible for providing support on that day.
This bot helps to automate this process. According to the time you set, it will update the room topic to show
"who's the man-on-duty today" and sends a notification as well.

You need to provide a list of team members, from which the bot will select the man-on-duty in a round-robin fashion.
Each team member's availability is also taken into account so that the bot can skip the ones that are on holiday on
a specific day.

To change your availability, the following commands are supported:
```
!HELP: show this message.
!IM_OFF  <args> : add your days off. Format: yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
!IM_BACK <args> : remove your days off. Format: yyyy-mm-dd (2016-01-31) or "mon", "tue", etc. (non-case-sensitive)
!SHOW_MY_DAYS   : show a list of your days-off.
!SHOW_NEXT_SHERIFF : show the next sheriff.
!NEXT_SHERIFF   : switch to the next sheriff. (in case that the current sheriff is not correct)
```
Because the bot monitors the Hipchat room through XMPP, you can simply change your availability by typing the
commands in the room. Only the commands from the team members will be processed, other people's commands will
simply be ignored.


## How to run
First set `PYTHONPATH` correctly and then run `bot.py`. A `config.ini` is required. Please see the next
section for details.


## Configuration

Most configuration options can be found in `example-config.ini`. Please take a look.

Here is an example of the configuration files:

```
# example-config.txt
[hipchat]
...

[team]
members = user1, user2, user3
daysoff_file = daysoff.txt
cache_file = cache.txt
room_name = Team Support Room
# every work day morning at 08:00, the bot will select the next available person as the man-on-duty
topic_update_time = 0 8 * * MON-FRI *
topic_template = Current man on-duty: <name>


# daysoff.txt - This file stores all the holidays (non-available days) of each team member
#               (you don't need to create this file)
[user1]
# a specific date (yyyy-mm-dd)
2016-01-31
# a regular day off (MON, TUE, ...)
MON

[user2]
# no non-available days for user2

[user3]
# no non-available days for user3
```

## License

This project is licensed under MIT. See [LICENSE](LICENSE).

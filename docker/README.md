# Docker image for team-hipchat-bot

### Build

You can run the `build.sh` script in this directory to build your team-hipchat-bot docker image.
The newly built image will be tagged as team-hipchat-bot:latest

## How to use

To run the bot in a docker container, you need to specify the following environment variables.
For more details, please check [README.md](../README.md) and [example-config.ini](../example-config.ini).

```
HCBOT_HIPCHAT_JID           : your full hipchat JID
HCBOT_HIPCHAT_AUTH_TOKEN    : your hipchat API v2 token
HCBOT_HIPCHAT_ROOM_JID      : room JID
HCBOT_HIPCHAT_ROOM_SERVER   : room XMPP server
HCBOT_HIPCHAT_API_SERVER    : API server
HCBOT_HIPCHAT_NICKNAME      : Your nick name on hipchat

HCBOT_TEAM_MEMBERS            : a full list of nicknames of your teammates'
HCBOT_TEAM_ROOM_NAME          : the hipchat room name
HCBOT_TEAM_TOPIC_UPDATE_TIME  : the topic update time in the cron format
HCBOT_TEAM_TOPIC_TEMPLATE     : A string represents the template for the topic. "<name>" will be set to the man on duty.

HCBOT_HIPCHAT_PASSWORD : your hipchat password
```

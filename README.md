# INFN Jobs Telegram Bot

A telegram bot to download job offers from INFN website (https://jobs.dsi.infn.it/data.php) and send them as telegram messages to selected users.

## How to use

Create a `data` folder, with a `users.json` file. This file is just a dictionary with the telegram IDs of the users whom to send the messages. Example:

```
{
    "user1": 12345678,
    "user2": 87654321
}
```

Then create a bot with @BotFather, paste the token to the ``docker-compose`` file and finally run ``docker-compose up -d``.

## INFN Telegram Channel

If you just want to receive job offers notifications, there is an official INFN telegram channel: https://t.me/infn_jobs.

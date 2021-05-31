#Overview

**Currently in development**

This project contains a Discord bot to help run and manage tournaments within a server
The current intended usecase is in the Marchesa cEDH tournament, which is a free-for-all style tournament with fluid, single-elemination rounds and a cut to finals.
This bot handles all major logistics of a tournament, including:
 - Managing player deck lists
 - Pairing players
 - Creating private voice channels and roles for a match
 - Notifing players about the end of time in round
 - Recording result of a match and confirmation from the other players
 - Tracks the standings of players
 - And more

There is also a full suite of tools that tounaments admin can use to manage issues that arise over the course of a tournament.
These tools also allow tournament admin to changes various aspects of a tournament, such as time in round.
Note, more popular styles of tournaments, like Swiss-style, are not easily ran with the current state of this bot.
With future developement, various types of tournaments will be fully supported, including league and ladder play.
Moreover, combining these styles in layers will also be allowed.
This is something most commonly done with the Mythic Qualifiers that WotC hosts (Day 1 get a 7-2 or better record, Day 2 Swiss).


# Setup

To get this bot working on your server, you to only do a few things.
First, add the bot to your server [here]("https://discord.com/api/oauth2/authorize?client_id=784967512106074183&permissions=268634192&scope=bot").
This will get the bot all necessary permissions, namely:
 - Manage roles and channels
 - Send messages
 - Read message history
 - Mention Everyone
 - Add Reactions

Notably, the bot will never use the "@everyone" mention, but giving it this permission allows it to mention any arbitary role.

Next, two roles with identical permissions need to be added, "Tournament Admin" and "Tournament Judge" (both case insensitive).
These roles will be given the people that will run and judge your tournaments.
There is a whole series of commands the are only usable by people with these roles (i.e. creating tournaments, creating pairings, etc.).
Similar to the bot, these roles need the permision to mention everyone so they can free mention any role created by the bot.

Lastly, a category and a text channel are needed.
The category needs to be named "Matches".
This is were the voice channels for each match will be created.
The text channel needs to be called "Match-pairings".
Any time a match is paired, the bot will send a message letting those players know that they've been paired.
This is also were the bot will send end of round messages.
Because of this, its generally recommended that only this bot and anyone with either role be allowed to send messages here.
It is also generally recommended to have a channel where players' bot commands can be directed as well as a tournament official version of this channel.

A file called .env should be created that includes the follwing tags:
```yaml
DISCORD_TOKEN=
MAX_COIN_FLIPS=
TRICE_BOT_AUTH_TOKEN=tricebot auth token, same as in config.conf for tricebot
API_URL=tricebot api url (LAN address) i.e: https://0.0.0.0:8000
EXTERN_URL=tricebot WAN address
```
You should set each tag to the value that you want.

## Trice Bot Setup
Go to https://github.com/djpiper28/CockatriceTournamentBot for the README to setup the tricebot.
The auth token for the trice bot should be put into .env under the `TRICE_BOT_AUTH_TOKEN` tag,
the trice bot should be ran on the same machine on `https://127.0.0.1:8000` with SSL enabled.
It is recommended to use nginx to expose the tricebot replay downloads to the WAN (proxy http 
to API_URL).

# Additional Resources


# Future Plans






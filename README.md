# Overview

SquireBot is a Discord bot designed to run and manage tournaments entirely within a server.

The current intended usecase is Magic: the Gathering tournaments.

SquireBot centralizes the tournament management experience entirely within Discord. Due to it's base, it can be interfaced on both mobile and desktop platforms. Users are able to interface with the tournament they're playing in from the table they sit at, outside the venue, or digitally around the globe.

# Features

This bot handles all major logistics of a tournament, including:
 - Managing player deck lists
 - Pairing players
 - Creating private voice channels and roles for a match
 - Notifing players about the end of time in round
 - Recording result of a match and confirmation from the other players
 - Reporting the standings of players
 - And more!

# Setup

To get this bot working on your server, you need to follow the **TODO** guide!

# Setup

To get this bot working on your server, you to only do a few things.
First, add the bot to your server [here]("https://discord.com/api/oauth2/authorize?client_id=784967512106074183&permissions=268634192&scope=bot").
This will get the bot all necessary permissions, namely:
 - Manage roles and channels
 - Send messages
 - Read message history
 - Mention Everyone
 - Add Reactions

# Additional Resources

### User Commands - LINK TODO

### Judge Commands - LINK TODO

### Admin Commands - LINK TODO

# Developing SquireBot
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



# Future Plans






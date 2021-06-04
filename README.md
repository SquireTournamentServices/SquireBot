# Overview

SquireBot is a Discord bot designed to run and manage tournaments entirely within a Discord.

The current intended usecase is Magic: the Gathering tournaments, though it can be used outside that context.

Since SquireBot centralizes the tournament management experience completely inside Discord, tournaments can be interfaced with on both mobile and desktop platforms. This allows players to interact with the tournament from the table they are sit at, outside the venue, or digitally around the globe. This makes SquireBot ideal for both in-person and digital events.


## Features

There are many new tournament softwares becoming available, and SquireBot aims to be an alterative to them. From the tournament organizer's perspective, SquireBot handles all major tournament logistics, including:
 - Managing player deck lists
 - Pairing players
 - Creating private voice channels and roles for a match
 - Notifing players about the end of time in round
 - Recording result of a match and confirmation from the other players
 - Reporting the standings of players
 - And more!

SquireBot is also flexible. It is a central goal to allow TOs to organize tournaments as they wish and for SquireBot to help them do so. If SquireBot doesn't have a feature, it will be taken into consideration.

From the player's perspective, SquireBot allows them to interact with a tournament from a service that they likely already have.


## Setup

To get SquireBot working on your server, you need to do the following. First, add the default roles and channels that SquireBot will be using
	1. Create a "Tournament Admin" Discord Role.
	2. Create a "Tournament Judge" Discord Role.
	3. Create a channel titled "match-pairings"
	4. Create two channel category titled "Matches" and "More Matches".

# Setup

To get this bot working on your server, you to only do a few things.
First, add the bot to your server [here]("https://discord.com/api/oauth2/authorize?client_id=784967512106074183&permissions=268634192&scope=bot").
This will get the bot all necessary permissions, namely:
 - Manage roles and channels
 - Send messages
 - Read message history
 - Mention Everyone
 - Add Reactions

Note, SquireBot will **never** use `@everyone` but needs that permission so it can mention arbitary roles. SquireBot makes roles for each tournament and each match in a tournament and uses these roles to alert players about the status of their match (such as the recording of a result, result confirmation, and time in round).


# Using SquireBot

SquireBot's commands are broken into three categories, player, judge, and admin commands. Each category is protected by the judge and admin roles. This prevents players from using judge commands and judges from using admin commands; however, admin can still use any command and judges can still use player commands. Since tournament admin are pinged when a player tries to use a command that they do not have permission to, the help message that SquireBot gives is catered to that user's role.

To see SquireBot's help message, use the command `!squirebot-help`. In that message will be the below links, which go into more depth about each command. There are two other links which are crash courses for new tournament admin and players. These are also linked in the help message.

 - [Player Commands](https://github.com/TylerBloom/SquireBot/blob/master/docs/PlayerCommands.md)
 - [Judge Commands](https://github.com/TylerBloom/SquireBot/blob/master/docs/JudgeCommands.md)
 - [Admin Commands](https://github.com/TylerBloom/SquireBot/blob/master/docs/AdminCommands.md)
 - [Player Crash Course](https://github.com/TylerBloom/SquireBot/blob/master/docs/CrashCourse.md)
 - **Admin Crash Course - LINK TODO**

# Development
To run a new instance of SquireBot, you will need its prerequistes and dependencies. SquireBot is written in python3 (and run/tested in python3.8). Its only non-standard dependencies are the Discord API library and the python-dotenv library. Both are available via pip3.

Once its libraries are installed, you need an `.env` file. This is where you'll specify your Discord Auth token for the bot. If you only intend to run SquireBot, you'll need the following:
```yaml
DISCORD_TOKEN=<your Discord Auth token>
MAX_COIN_FLIPS=<some number, at most 250,000>
```

If you want to work on SquireBot and add features too, you'll want to add a value for the testing bot's token. While this could be the same token as SquireBot's, adding a bot account is free of charge and the added compartmentalization does not hurt.
```yaml
TESTING_TOKEN=<your Discord Auth token>
```


## Trice Bot Setup
SquireBot has integration with [TriceBot](https://github.com/djpiper28/CockatriceTournamentBot), which helps organize players in Cockatrice as well as provides a single location to pull replay from. Follow the intrustion in its README to set it up. TriceBot should be ran on the same machine as SquireBot on `https://127.0.0.1:8000` with SSL enabled. It is recommended to use nginx to expose the tricebot replay downloads to the WAN (reverse proxy https to API_URL) you can you nginx to hide the /api/\* endpoints as well.

The auth token for TriceBot should be put into the `.env` file with:
```yaml
TRICE_BOT_AUTH_TOKEN=<tricebot auth token, same as in config.conf for TriceBot>
API_URL=<TriceBot API URL (LAN address), i.e: https://127.0.0.1:8000>
EXTERN_URL=<TriceBot WAN address>




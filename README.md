# Overview

SquireBot is a Discord bot designed to run and manage tournaments entirely within Discord.

The current intended use case is Magic: the Gathering tournaments, though it can be used outside that context.

Since SquireBot centralizes the tournament management experience completely inside Discord, tournaments can be interfaced with on both mobile and desktop platforms. This allows players to interact with the tournament from the table they are sit at, outside the venue, or digitally around the globe. This makes SquireBot ideal for both in-person and digital events.


## Features

There are many tournament softwares becoming available, and SquireBot aims to be an alterative to them. From the tournament organizer's perspective, SquireBot handles all major tournament logistics, including:
<ul>
 <li>Managing player deck lists</li>
 <li>Pairing players</li>
 <li>Creating private voice channels and roles for each match</li>
 <li>Notifying players about the end of time in round</li>
 <li>Recording result of a match and confirmation from the other
 players</li>
 <li>Reporting the standings of players</li>
 <li>And more!</li>
</ul>

SquireBot is also flexible. It is a central goal to allow TOs to organize tournaments as they wish and for SquireBot to help them do so. If SquireBot doesn't have a feature that you need, request it and it will be taken into consideration.

From the player's perspective, SquireBot allows them to interact with a tournament from a service that they likely already have. This avoids the classic addage, "I don't want to get *another* app..."


## Setup

To get SquireBot working on your server, you need to first add it to your server, [here](https://discord.com/api/oauth2/authorize?client_id=784967512106074183&permissions=8&scope=bot).
Note, SquireBot will **never** use `@everyone` but needs that permission so it can mention arbitrary roles. SquireBot makes roles for each tournament and each match and uses these roles to alert players about the status of their match (such as the recording of a result, result confirmation, and time in round).

Second, SquireBot has several requirement to properly run tournaments, to set
everything up, simply run the `!setup` command. If you'd like to see
what all it sets up, see the documentation for the commands [here](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/SetupCommands.md).
To get SquireBot working on your server, you need to do the following. First, add the default roles and channels that SquireBot will be using
<ol>
	<li>Create a "Tournament Admin" Discord Role.</li>
	<li>Create a "Tournament Judge" Discord Role.</li>
	<li>Create a channel titled "match-pairings"</li>
	<li>Create two channel category titled "Matches" and "More
	Matches".</li>
</ol>


# Using SquireBot

SquireBot's commands are broken into three categories, setup, tournament, and misc. Within each group, there might be role-protected command, which can only be used by a member that has the `Tournament Admin` and/or `Judge` role in that server. This prevents regular players from using that they shouldn't have access to, like overwriting the results of matches. Moreover, there are some commands that only tournament admin can use but that judges can't use.

To see SquireBot's help message, use the command `!squirebot-help`. In that message will be the below links, which go into more depth about each command. There are two other links which are crash courses for new tournament admin and players. These are also linked in the help message.
<ul>
 <li> [Player Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/PlayerCommands.md) </li>
 <li> [Judge Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/JudgeCommands.md) </li>
 <li> [Admin Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/AdminCommands.md) </li>
 <li> [Player Crash Course](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/CrashCourse.md) </li>
 <li> [Admin Crash Course](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/AdminCrashCourse.md) </li>
</ul>


# Development

SquireBot is written in Rust, so some version of rustc in a requirement. All stable version after 1.56.0 have been used and tested to some degree.

Once you have a working rustc, you will need a `.env` file. This is where you'll specify your Discord Auth token for the bot. If you only intend to run SquireBot, you'll need the following:
```yaml
DISCORD_TOKEN=<your Discord Auth token>
```

Lastly, if you'd like error messages logged in Discord, you can specify the IDs to a Discord guild and text channel where errors will be logged.
```yaml
DEV_SERVER_ID=<your Discord server ID>
ERROR_LOG_CHANNEL_ID=<your Discord logging channel ID>
```


## Trice Bot Setup

SquireBot has integration with [TriceBot](https://github.com/djpiper28/CockatriceTournamentBot), which helps organize players in Cockatrice as well as provides a single location to pull replay from. Follow the intrustion in its README to set it up. TriceBot should be ran on the same machine as SquireBot on `https://127.0.0.1:8000` with SSL enabled. It is recommended to use nginx to expose the tricebot replay downloads to the WAN (reverse proxy https to API_URL) you can you nginx to hide the /api/\* endpoints as well.

The auth token for TriceBot should be put into the `.env` file with:
```yaml
TRICE_BOT_AUTH_TOKEN=<tricebot auth token, same as in config.conf for TriceBot>
API_URL=<TriceBot API URL (LAN address), i.e: https://127.0.0.1:8000>
EXTERN_URL=<TriceBot WAN address>
```


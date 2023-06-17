# Overview

SquireBot is a Discord bot designed to run and manage tournaments entirely within Discord.

The current intended use case is Magic: the Gathering tournaments, though it can be used outside that context.

Since SquireBot centralizes the tournament management experience completely inside Discord, tournaments can be interfaced with on both mobile and desktop platforms. This allows players to interact with the tournament from the table they sit at, outside the venue, or digitally around the globe. This makes SquireBot ideal for both in-person and digital events.


## Features

There are many tournament softwares becoming available, and SquireBot aims to be an alternative to them. From the tournament organizer's perspective, SquireBot handles all major tournament logistics, including:
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

From the player's perspective, SquireBot allows them to interact with a tournament from a service that they likely already have. This avoids the classic adage, "I don't want to get *another* app..."


## Setup

To get SquireBot working on your server, you need to first add it to your server, [here](https://discord.com/api/oauth2/authorize?client_id=784967512106074183&permissions=8&scope=bot).
Note, SquireBot will **never** use `@everyone` but needs that permission so it can mention arbitrary roles. SquireBot makes roles for each tournament and each match and uses these roles to alert players about the status of their match (such as the recording of a result, result confirmation, and time in the round).

Second, SquireBot has several requirements to properly run tournaments, to set
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

SquireBot's commands are broken into three categories, setup, tournament, and misc. Within each group, there might be role-protected commands, which can only be used by a member that has the `Tournament Admin` and/or `Judge` role in that server. This prevents regular players from using that they shouldn't have access to, like overwriting the results of matches. Moreover, there are some commands that only tournament admins can use but that judges can't use.

To see SquireBot's help message, use the command `!sb-help`. In that message will be the below links, which go into more depth about each command. There are two other links which are crash courses for new tournament admin and players. These are also linked in the help message.
<ul>
 <li> [Player Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/PlayerCommands.md) </li>
 <li> [Judge Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/JudgeCommands.md) </li>
 <li> [Admin Commands](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/AdminCommands.md) </li>
 <li> [Player Crash Course](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/CrashCourse.md) </li>
 <li> [Admin Crash Course](https://github.com/MonarchDevelopment/SquireBot/tree/rust-port/docs/AdminCrashCourse.md) </li>
</ul>


# Development

SquireBot is written in Rust, so some version of rustc is a requirement. All stable versions after 1.56.0 have been used and tested to some degree.

Once you have a working rustc, you will need a `.env` file. This is where you'll specify your Discord Auth token for the bot. If you only intend to run SquireBot, you'll need the following:
```yaml
TOKEN=<your Discord Auth token>
```

Then, you should specify the IDs to Discord channels where issues and telemetry will be logged.
```yaml
ISSUE_CHANNEL_ID=<your Discord channel ID for issues>
TELEMETRY_CHANNEL_ID=<your Discord channel ID for telemetry>
```

If it is your first time working with Discord bots, [this](https://www.pythondiscord.com/pages/guides/pydis-guides/contributing/setting-test-server-and-bot-account/) can be helpful. It will take you through the steps of creating a Discord bot and setting up your Discord account for developer mode. Don't forget to give the bot all three _Privileged Gateway Intents_.

In order to run SquireBot, you will also need to create an empty `tournaments.json` file in the project.

Once the bot is up and running in the server, you can run `!sb-help` and `!setup test` to check if everything is alright.

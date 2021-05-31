# SquireBot Crash Course
## Overview
This bot is used to run a tournament from start to finish. It works similarly to options like MTGMelee or Challonge, however this bot interfaces entirely within Discord. This bot handles registration, decklist management, pairings, match results, and leaderboards. This document will give a broad overview of the functionalities.

**Tournament day can be stressful.** There are a couple of things we’re doing to minimize that stress.

1. __First, the bot should always give you feedback when you run a command.__ If you don’t get a message back, either the command was typed incorrectly, or an error occurred. While this shouldn’t happen often, ping @Tournament Admin if something goes wrong. 
1. **Second, read this document completely.** This document, as well as the bot command document will set your expectations appropriately.

## Registration
The command “!register” enrolls you in a tournament on the current server. If there are more than one open tournaments, you will need to specify which tournament you want to register for. Use the “!list-tournaments” command to find the correct one.

When a tournament starts, registration will close. If this happens and you are unable to register on the day of the event, ask an @Tournament Admin if you can still join. They may choose to add you to the tournament at their discretion.

Since Marchesa 2021 takes place on Cocktrice, it will be helpful to add your Cockatrice username to your player profile. Simply use the “!cocktrice-name” command followed by your name on Cocktrice.

## Deck Management
### Deck Cap
The bot supports the ability to register any number of decks. The tournament administrators will assign a maximum number of decks you can have registered at any one time (usually one or two).

Once a tournament starts, the tournament admins will remove any decks that go beyond the set limit. **Only your most recently submitted decks are kept.** You’ll be notified when a deck is removed during this process. 

For example, you submit Deck A, followed by Deck B and then Deck C. The maximum deck count is set to two. When the tournament begins, you will **only** have access to Deck B and Deck C. **You will not be allowed to play Deck A as it is the oldest deck you have registered.**

### Adding Decks

The “!add-deck” command takes three required inputs:

Tournament Name

Decklist Name

Decklist in Cockatrice formatting (both annotated and not annotated are supported)

“Tournament Name” is a required input so that you can register for the tournament via Direct Message. This is to prevent other players from having access to your decklist. **This is one of the only commands that works via Direct Message.**

Once you submit a decklist, the bot will reply with the Cockatrice decklist hash. **Make sure this matches your hash in Cocktrice.** Deck checks rely on the hashes matching. Mismatched hashes may result in a game loss.

An example add-deck command is as follows:
!add-deck Marchesa “Chulane Combo”
“// 99 Maindeck
// 5 Artifact
1 Cloudstone Curio
1 Jeweled Lotus
…

…
// 1 Sideboard
// 1 Creature
SB: 1 Chulane, Teller of Tales”

### Changing and Removing Decklists

If you register a deck name that you have already registered, you will overwrite the old decklist. This is the best way to update your decklist.

If you would like to remove a deck entirely, you can use the “!remove-deck” command, followed by either the deck title or the deck hash.

## Playing the Game
Once you have registered and then submitted your decks, you’re ready for the main event.

For each match, you must run two commands. The first is to find a match, and the second is to confirm a match result.

To be placed in the match queue, type “!lfg” in the matchmaking channel. Wait for the bot to assign you to a match. You will be tagged when a match is found. This command is case sensitive. **You cannot type “!LFG”**

The bot will release deck hashes, Discord usernames, and Cockatrice usernames.

It will create a voice channel that is only visible to players in your matches, judges, and tournament administrators.

After the match is over, each player must confirm the match.

**Please do not leave the server without confirming a match.**

The match winner will use the command “!match-result” followed by “winner”, or “win.”

Each other player must type “!confirm result” to affirm that the first player won the match. If the incorrect player has typed “!match-result winner”, please ping @Tourmanet Admin

**You will not be allowed to join the queue until match results have been confirmed.**

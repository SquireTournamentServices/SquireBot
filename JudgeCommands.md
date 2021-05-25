# SquireBot Judge Commands
## Intro:
Unlike user commands, the bot will not automatically interpet what tournament you want. You must always specify a tournament’s name. Explicatively when managing a tournament is important. As such, optional arguments to commands are very few and far between. Similar to the user commands, none of these commands will work via direct message. If sensitive information, such as a deck list, would be given as either an input or an output of a command, make sure you are in a channel that regular users can not access.

These commands can, roughly, be split into two categories. 
1. First, there are the upgraded versions of most user commands. These commands supersede most of the checks done for user commands and are prefixed with the work “admin”. For example, a player can’t normally register or submit a deck if registration is closed (commonly done when the tournament starts). The admin-register and admin-add-deck command ignore this check. In many ways, this set of commands exists to help clean up the messes that players inevitably make.
1. Second, there are commands that do things that player’s can’t normally do, like give time extensions.

Lastly, all of these commands are role-protected. The only people that can use these commands are people that have either the “tournament admin” or “judge” role. Should someone without this role try to use one of these commands, they will be denied and these roles will be notified that they tried to interfere with the tournament. **Such attempts, even if they seem benign, should not be taken lightly.**

## Commands:

A couple of notes about arguments to commands. First and just like the user commands, anything with a space or new line needs to be surrounded in quotation marks. Second, any command that requires you to specify a player can handle either their nickname on the server for their mention (their “@”). If using someone’s mention, you do **not** need to surround it with quotes even if it looks like there’s spaces.

### admin-register (tournament) (player)

Registers a player for the named tournament on their behalf. The player will be privately messaged that this has occurred.

- Ex. !admin-register “Marchesa 2021” @Tylord2894

### admin-add-deck (tournament) (player) (deck name) (decklist)

Adds a deck to a player’s profile. The player will be privately messaged that this has occurred.

- Ex. !admin-add-deck “Marchesa 2021” @Tylord2894 “More Izzet Charms” “4x Izzet Charm”

### admin-remove-deck (tournament) (player) (deck name/hash)

Removes a deck from the player’s profile. You can give either the deck’s name or hash. The player will be privately messaged that this has occurred.

- Ex. !admin-remove-deck “Marchesa 2021” @Tylord2894 “More Simic Charms”

### list-players (tournament) [number]

Lists the names of all players in the tournament. Optionally, if “number” is given, the number of registered players is given instead.

- Ex. !admin-list-players “Marchesa 2021” number

### player-profile (tournament) (player)

Prints out a player’s profile. This includes their name, Cocktrice name, deck names and hashes, and match record. This does not print out their decklists.

- Ex. !admin-player-profile “Marchesa 2021” @Tylord2894

### admin-match-result (tournament) (player) (match #) (win/loss/draw)

Records the result of a match for a player. This command has two major uses. First, it can be used to change the results of a confirmed match. This should be used sparingly as Eol points can not be retroactively redistributed. If the match is already certified, this does not uncertify the match; however, each player will be privately messaged that this happened. If the match isn’t certified, any players that confirmed the result will need to reconfirm. The player that was specified will be privately messaged that this happened and the whole pod will be messaged that the result of their match has changed. They will be asked to reconfirm

- Ex. !admin-match-result “Marchesa 2021” @Tylord2894 1 draw

### admin-confirm-result (tournament) (player) (match #)

Confirms the result of the match on the player’s behalf.

- Ex. !admin-confirm-result “Marchesa 2021” @Tylord2894 1

### admin-decklist (tournament) (player) (deck name/hash)

Prints out a player’s deck list.

- Ex. !admin-decklist “Marchesa 2021” @Tylord2894 “Izzet Ponza”

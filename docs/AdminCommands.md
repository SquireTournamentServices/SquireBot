# SquireBot Admin Commands
## Intro
Unlike user commands, the bot will not automatically interpet what tournament you want. You must always specify a tournament’s name. Explicatively when managing a tournament is important. As such, optional arguments to commands are very few and far between. Similar to the user commands, none of these commands will work via direct message. If sensitive information, such as a deck list, would be given as either an input or an output of a command, make sure you are in a channel that regular users can not access.

These commands can, roughly, be split into two categories. 
1. First, there are the tournament-management commands which are used to create, run, and manage various aspects of the tournament. Second, there are the admin versions of most user commands. These commands supersede most of the checks done for user commands. For example, a player can’t normally register or submit a deck if registration is closed (commonly done when the tournament starts). The admin-register and admin-add-deck command ignore this check. In many ways, this set of commands exists to help clean up the messes that players inevitably make.
1. Lastly, all of these commands are role-protected. The only people that can use these commands are people that have the “tournament admin” role (case insensitive). Should someone without this role try to use one of these commands, they will be denied and this role will be notified that they tried to interfere with the tournament. Such attempts, even if they seem benign, should not be taken lightly.

## Commands:
A couple of notes about arguments to commands. First and just like the user commands, anything with a space or new line needs to be surrounded in quotation marks. Second, any command that requires you to specify a player can handle either their nickname on the server for their mention (their “@”). If using someone’s mention, you do not need to surround it with quotes even if it looks like there’s spaces.


### create-tournament (tournament)

Simply creates a tournament by the given name. 

- Ex. !create-tournament “Marchesa 2021”

### update-reg (tournament) (open/closed or true/false)

Simply opens or closes registration for the given tournament. true = open and false = closed

- Ex. !update-reg open

### start-tournament (tournament)

Starts the named tournament. This means that the tournament is live and running. This command also closes registration, but it can be reopened.

- !start-tournament “Marchesa 2021”

### end-tournament (tournament)

Ends the named tournament. This requires the tournament to have started. After this command runs, no further actions can be taken with the tournament, and it can be considered dead.

- Ex. !end-tournament “Marchesa 2021”

### cancel-tournament (tournament)

Cancels the named tournament. This works much like end-tournament, but without any timing restrictions.

- Ex. !cancel-tournament “Marchesa 2021”

### set-deck-count (tournament) (amount)

Sets the allowed deck count for the named tournament. This command is used in tandem with admin-prune-decks. The default is one. The number needs to be given in digits, not in words. 

- Ex. !set-deck-count “Marchesa 2021” 7

### prune-decks (tournament)

Removes decks from each player’s profile until they have the allowed number. Decks are removed in (rough) chronological order. Each time a player has a deck removed this way, they are privately messaged and @Tournament Admin is notified.

- Ex. !admin-prune-decks “Marchesa 2021”

### set-match-size (tournament) (number)

Sets the number of players per match for all future matches. The number needs to be specified with digests and words.

- Ex. !players-per-match “Marchesa 2021” 4

### set-match-length (tournament) (time in minutes)

Sets the length of a match for all future matches. Warning messages about the end of the round are given at 5 and 1 minutes.

- Ex. !set-match-length “Marchesa 2021” 80

### create-match (tournament) (players)

Creates a match between the specified players. The names of players needs to be space-separated. You have to specify a number of players equal to exactly the number of allowed players per match.

- Ex. !admin-create-pairing “Marchesa 2021” @Tylord2894 @Joking101

### create-pairings-list (tournament)

Creates a list of possible match pairings using the list of active players. This is meant to inform the use of the admin-create-pairing command as an early version of swiss-style Commander tournaments.

- Ex. !admin-pairings-list “Marchesa 2021”

### admin-drop (tournament) (player)

Removes the player from the tournament. This acts as the admin’s way of removing them from the tournament, similar to how a play can drop from the tournament.

- Ex. !admin-kick-player “Marchesa 2021” Tylord2894

### give-bye (tournament) (player)

Creates a match for the player that includes only that player. This match is considered a win for calculating match points and match-win percentage, but isn’t considered when calculating opponent match-win percentage. Also, no role or voice channel is created.

- Ex. !admin-give-bye “Marchesa 2021” Tylord2894

### remove-match (tournament) (match number)

Removes all information surrounding a match. Any result is discarded. All players have their list of past opponents updated. Lastly, the role and voice channel (if they exist) are removed. Notably, this doesn’t change any existing (or future) match numbers. If two matches exists and match #1 is removed, the next match will be match #3 and match #1 will be unchanged.

- Ex. !admin-remove-match “Marchesa 2021” 2 

### tricebot-kick-player (tournament) (match number) (cockatrice player name)

Kicks a player who has joined a tricebot game that should not be in the game. The Player name is case sensitive.

- Ex. !tricebot-kick-player "Marchesa 2021" 1 HackerMan232

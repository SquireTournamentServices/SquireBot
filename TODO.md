Overview:
This document details what the bot does not how it does things. As such, the focus will be how to use the commands and what to expect when using them. This will be fairly dry and technical, so grab some coffee.

All the commands the bot currently has or will have are broken into two categories, “player” and “admin.” Naturally, only users with the appropriate role can use the admin commands while anyone can use the player commands. Moreover, the tournament admins will be pinged if a non-tournament admin tries to use a tournament admin command. The bot always returns some kind of message to help the user. If there isn’t a message returned, either the command name is wrong or an error occurred.

For each command, the command’s name and the information that it needs is listed. An argument in brackets (“[ ]”) is optional. Conversely, an argument in braces (“{ }”) are non optional. If a command is run without that piece of info, the bot informs you that you need to provide more information. As a safety feature, there are no optional arguments for admin commands. Command arguments are space-delimited, so arguments with spaces in them need to be in quotes. Notably: decklists need to be in quotes.

With one exception, these commands cannot be sent via private message. The “add-deck” command can be sent via private message. This allows players to maintain secrecy of their decklists. However, if you wish to submit your decklist via PM, you must also specify which tournament you are registering for.

With that out of the way, let’s get into what the bot can do now and will be able to do soon!

Assumptions/Prerequisites
There must be a role in the Discord server titled “Tournament Admin”. This role is the only role with access to administrative bot commands.
Locked channel for exclusively pairing messages.

Current commands:
Player commands:
list-tournaments
Lists the tournaments that are planned for the server the message was sent from
Helpful for players getting the name of the tournament if needed

register [tournament name]
Adds a player to the specified tournament.
Tournament name becomes optional only if one tournament is present in that server.

add-deck [tournament name] {deck identifier} {decklist}
Adds a deck to the player
The identifier and decklist are roughly interchangeable as there is a check to make sure that the decklist is longer than the identifier.
If successfully added, the bot will respond with a deckhash for the player to verify.
Should the hash be incorrect or they wish to change the deck, they can re-enter a deck with the same identifier to overwrite the deck.

remove-deck [tournament name] {deck identifier or deck hash}
Removes the deck with the given identifier/hash

list-decks [tournament name]
Lists the deck hash and and deck identifier of each deck the player has registered.

Admin commands:
create-tournament {tournament name}
Creates a tournament
The new tournament will have registration open and has not started

update-reg {tournament name} {true/false}
Opens or closes registration of the specified tournament
True = opens registration
False = closes registration

start-tournament {tournament name}
Starts the specified tournament
This allows players to !queue and such
This also closes registration but does not prevent it from being re-opened

end-tournament {tournament name}
Ends the specified tournament
Stops players from using !queue
Stops the tournament from being loaded when the bot starts up, but files are saved

cancel-tournament {tournament name}
Cancels the specified tournament
Acts much like !end-tournament, but doesn’t require the tournament to have started

admin-register {tournament name} {player name}
Adds a player to the tournament
This supersedes the registration status of the tournament
Currently, you can mention a player (i.e. not @s). I hope to change this


Near-future commands:
Player commands:
LFG [tournament name]
Adds a player to the pairings queue of the tournament
Requires the player isn’t in an unresolved match
Requires the tournament to be started

cockatrice-name [tournament name] {Cocktrice name}
Adds the player’s name on Trice to their player profile 
One’s Trice name will be printed off when a pairing message is sent

drop-tournament [tournament name]

match-result [tournament name] {winner/draw/loser}

confirm-result [tournament name]

standings [tournament name]


Admin commands:
admin-add-deck  {tournament name} {player name} {deck identifier} {deck list}
Adds a deck to the player
This supersedes registration
Sends a message to the affected player stating that a deck was added on their behalf
Much like !add-deck, if an identifier that matches an existing deck identifier, the deck is overwritten

admin-remove-deck {tournament name} {player name} {deck identifier or hash}
Removes the deck from a specified player with the matching identifier or hash
Sends a message to the affected player stating that a deck was removed on their behalf

set-deck-count {tournament name} {max deck count}
Changes the maximum number of decks someone can keep have pruning

admin-prune-decks {tournament name}
For each player, it removes the oldest deck they have until they have the max deck count
This count is changed by !set-deck-count
If a player is affected by this, they are messaged saying which decks were removed on their behalf.

admin-drop-match {tournament name} {match number}

admin-list-players {tournament name} [“number”]
Lists the names of all players in the specified tournament
If the word “number” is added, it lists the number of active players instead of all player names

admin-player-profile 
Looks up name, decks, hashes, Trice name, and other stuff

admin-match-result [tournament name] [player] [winner/draw/loser]

admin-confirm-result [tournament name] [player]

admin-drop-tournament [tournament name] [player]



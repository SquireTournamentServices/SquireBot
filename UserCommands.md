# SquireBot User Commands
## Intro:
Before using the user commands of this bot, there are several things that need to be kept in mind. 
- The bot will not perform most actions in a tournament when you send commands via private message. There is a sole exception to this with the “add-deck” command, which will be covered later.
- If the server you’re on is holding multiple tournaments, you must specify the name of the tournament for all commands. If there is only one tournament held on the server, the bot will apply your command to that tournament.
- Finally, the bot will always respond to a **correctly spelled** command. If you receive no feedback from the bot, check your spelling. If it doesn’t respond to a correctly spelled command, something has gone wrong. Please contact the tournament admins immediately if this occurs.

Below, you’ll find the name and arguments of each command. **Arguments must be specified in the order that they are listed.** If an argument has a space or new line in it (such as a username on Cockatrice), **you must surround that argument with quotation marks.** Bear in mind, the name of the tournament is only required some of the time.
## Commands:
### register: (tournament name)

Adds you to the specified tournament.
- Ex: !register

### add-deck: (tournament name) (deck name) (decklist)

Adds a decklist to your player profile under the name you give it. The bot supports the “Save deck to clipboard” option in Cocktrice. Since your deck will need to be in Cockatrice to play in Marchesa, this is the best way to register your decklist.

We don’t want you to have to post your decklist publicly; this is one of the few commands that you may use via private message. If you need to resubmit a decklist, adding a deck with the same name will overwrite the prior deck.

- Ex: !add-deck Marchesa “The big, bad Storm” “1 Izzet Charm”

### cockatrice-name: (tournament name) (Cockatrice username)

Adds your username on Cockatrice to your player profile. This does not cross-check with Cockatrice, so make sure you have it correct. This is how other players will identify you in Cockatrice.

- Ex: !cockatrice-name “Jace the Mind Sculptor”

### lfg: (tournament name)

Adds you to the matchmaking queue.

- Ex: !lfg

### match-result: (tournament name) (result)

Record the result of your match. There are three options for the result, “win”, “draw”, and “loss”.

The first two options will record you as the winner and request confirmation from the other active players. If you use the match-result command, you do not need to use confirm-result. The “loss” option records you as a loser in the match. This means that you don’t have to confirm the result of the match; however, this does not allow you to rejoin the matchmaking queue.

If there is a typo, or the wrong player claims victory, this command can be re-ran. Players that confirmed the prior result will need to reconfirm. 

- Ex !match-result win

### confirm-result: (tournament name)

Confirms that you agree with the recorded result of your match. Again, if you use the match-result command, you do not need to use confirm-result.

- Ex: !confirm-result

### decklist [tournament] (deck name/hash)

Sends a message containing one of your deck lists. Note that your whole decklist will be made available to the current channel. If this command isn’t sent via DM, you will be asked to confirm that you want to publish your list.

- Ex. !decklist “Izzet Ponza”

### list-decks: (tournament name)

List the names of your decks and their hashes. This command does not post your decklist.

- Ex: !list-decks

### flip-coins [number]

In case you need to flip a lot of coins, the bot can help you out

- Ex. !flip-coins 1000

### misfortune (number)*

Wheel of Misfortune is a tricky card to resolve on Cockatrice. This command will help you resolve it. First, one player will use “!misfortune” to start everything. Then, each player in the match will need to DM the bot “!misfortune (number)”. Once everyone has responded, the bot will post the results of your misfortune.

- Ex. !misfortune 17

### standings: (No arguments)

This command lists the current standings as of the moment you send the command. By default, only the people around you will be shown. To see the full standings, add the word “all” to your command. Due to its length, the full standings can only be requested in the “standings” channel.

- Ex: !standings
- Ex: !standings all

### remove-deck: (tournament name) (deck identifier)

Removes your registered deck with the specified identifier. The deck identifier can either be a deck name or a deck’s Cocktrice hash. Since the bot can’t recover a deck that’s been deleted, you will be asked for confirmation. Use the “!yes” or “!no” commands for this.

- Ex: !remove-deck “The Brothers’ War”
- Ex: !remove-deck i9qp2cd3

### drop: (tournament name)

Drops you from a tournament. Due to the difficulty in reentering a tournament, you will be asked for confirmation. Use the “!yes” or “!no” commands for this.

- Ex: !drop-tournament

### list-tournaments: (No arguments)

This command lists the name of each tournament the server is having.

- Ex: !list-tournament

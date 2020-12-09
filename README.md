Things that the a server needs to do in order for the bot to work:
	- 1) There needs to be a role named "tournament admin" (case insesitive).



Things that ought to be done:
	- 1) The match object should contain minimal data, icluding only a player's name (not the entire player object).
	- 2) Each player should have a copy of their matches.
	- 3) Parts of the match registeration logic needs to be reworked with the above point in mind.


Below is a running list of assumptions that are made about how the bot will be used.
  - 1) There is only one tournament being actively ran per guild (server) at once. A guild can set up any number of tournaments, but they can only be actively running one at a time.
	- 2) A player can only be registered in, at most, one active tournament at a time regardless of the guild that tournament is happening in. They can be registered in any number of tournaments across any number of guilds.
	- 3) A player can only be in, at most, one active or uncertified match. That is, if a player is currently in a match, they can join an new match. Moreover, if they are in a match that still needs to be verified, they can't join a new match.

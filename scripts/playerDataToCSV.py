import sys
import os

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert(0, projectBaseDir + "Tournament")
sys.path.insert(0, projectBaseDir)

from Tournament import *


tourn = tournamentSelector("PWPAugust21/tournamentType.xml", "PWPAugust21", "PWP")
tourn.loadTournament("PWPAugust21")
print(tourn.players)


decks = []

with open("PWP_August21_PlayerData.csv", "w") as output:
    activePlayers = [plyr for plyr in tourn.players.values() if plyr.isActive()]
    output.write(", ".join([plyr.name for plyr in activePlayers]))
    output.write("\n")
    for plyr in activePlayers:
        decks.append([])
        decks[-1].append(list(plyr.decks.values())[-1].ident.replace(",", "") + ":")
        for card in list(plyr.decks.values())[-1].cards:
            card = card.replace("SB:", "").replace(",", "")
            card = card.strip()
            if card == "":
                continue
            card = card.split(" ", 1)
            decks[-1].append(card[-1])
    longest_deck = max([len(d) for d in decks])
    for d in decks:
        while len(d) < longest_deck:
            d.append("")
    for i in range(longest_deck):
        print(f"{d[i]!r}")
        output.write(", ".join([d[i] for d in decks]))
        output.write("\n")

with open("PWP_August21_MatchData.csv", "w") as output:
    output.write(
        "Match Number:, Winner:, Player #1, Player #2, Player #3:, Player #4:\n"
    )
    for mtch in tourn.matches:
        digest = f"{mtch.matchNumber}, "
        if isinstance(mtch.winner, int):
            digest += f'{tourn.players[mtch.winner].name.replace(",", "")}, '
        else:
            digest += f"{mtch.winner}, "
        digest += ", ".join(
            tourn.players[plyr].name.replace(",", "") for plyr in mtch.activePlayers
        )
        output.write(f"{digest}\n")


print("Done")
exit()

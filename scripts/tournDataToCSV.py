import sys
import os

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert(0, projectBaseDir + "Tournament")
sys.path.insert(0, projectBaseDir)

from Tournament import *


tournDir = sys.argv[1]

tourn = tournamentSelector(f"{tournDir}/tournamentType.xml", f"{tournDir}", "PWP")
tourn.loadTournament(f"{tournDir}")
print(tourn.playerReg.getPlayers())


with open(f"{tournDir}_PlayerData.csv", "w") as output:
    cols = []
    activePlayers = tourn.playerReg.getPlayers()
    for plyr in activePlayers:
        cols.append([plyr.name.replace(",", "")])
        for name, dck in plyr.decks.items():
            cols[-1].append(name.replace(",", "") + ":")
            for i in range(100):
                if i >= len(dck.cards):
                    cols[-1].append("")
                    continue
                card = dck.cards[i].replace("SB:", "").replace(",", "")
                card = card.strip()
                if card == "":
                    continue
                cols[-1].append(card)
            cols[-1].append("")
    longest_col = max([len(d) for d in cols])
    for d in cols:
        while len(d) < longest_col:
            d.append("")
    for i in range(longest_col):
        output.write(", ".join([d[i] for d in cols]))
        output.write("\n")

with open(f"{tournDir}_MatchData.csv", "w") as output:
    output.write(
        "Match Number:, Winner:, Player #1, Player #2, Player #3:, Player #4:\n"
    )
    for mtch in tourn.matchReg.getMatches():
        digest = f"{mtch.matchNumber}, "
        if isinstance(mtch.winner, player):
            digest += f'{mtch.winner.name.replace(",", "")}, '
        else:
            digest += f"{mtch.winner}, "
        digest += ", ".join(plyr.name.replace(",", "") for plyr in mtch.activePlayers)
        output.write(f"{digest}\n")


print("Done")
exit()

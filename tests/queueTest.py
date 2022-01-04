from Tournament import *
from test import *


class QueueTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/pairingQueue.py"

    def test(self):
        PLAYERS = 50
        THRESHOLD = 4

        queue = pairingQueue()
        print(len(queue.queue))
        assert len(queue.queue) == 1

        players = dict()
        for i in range(PLAYERS):
            p = player(f"{i}", None)
            players[p.uuid] = p

        for p in players.values():
            queue.addPlayer(p)

        print(queue)
        assert len(queue.queue[0]) == PLAYERS

        pairings = queue.createPairings(THRESHOLD)

        for pairing in pairings:
            for plyr in pairing:
                queue.removePlayer(players[plyr])

        print(queue)
        assert len(queue.queue[0]) == PLAYERS % THRESHOLD

        queue.bump()
        assert len(queue.queue[1]) == PLAYERS % THRESHOLD

        print(queue)

        return True

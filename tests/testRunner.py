import os
import sys

projectBaseDir = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path.insert( 0, projectBaseDir + 'Tournament')
sys.path.insert( 0, projectBaseDir )

from cardDBTest import *
from queueTest import *
from deckTest import *
from tournamentTest import *
from test import *

def runTests():
    testCases = []
    testCases.append(CardDBTest())
    testCases.append(QueueTest())
    testCases.append(DeckTests())
    testCases.append(TournamentTest())
    
    
    tests = TestRunner(testCases)
    print("[TEST RUNNER]: Running tests...")
    status = tests.executeTests()
    
    print(f"[TEST RESULTS]: {len(tests.passedTests)}/{len(testCases)} test cases are passing.")
    
    return status

if __name__ == '__main__':
    if runTests():
        os._exit(0)
    else:        
        os._exit(13)

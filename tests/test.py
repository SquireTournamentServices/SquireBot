import traceback

# This is a junit inspired test module that I slapped together in about 10 minutes
# it is probably quite bad but does the job :) - Danny

# This is the test class that all tests should inherit from.
class TestCase:
    testName = None
    
    def __init__(self):
        pass
    
    def test(self) -> bool:
        raise TestNotImplementedException()

# This is used to run all of the tests and get the successes and the failures reported back
class TestRunner:
    def __init__(self, testCases: list):
        self.testCases = testCases
        self.passedTests = []
        self.failedTests = []
    
    # Returns true if all the tests passed
    def executeTests(self) -> bool:
        self.passedTests = []
        self.failedTests = []
                
        for test in self.testCases:
            testSuccess = True
            if test.testName is None:
                print(f"[Error]: A test has no name. ({str(test)})")
                testSuccess = False
            else:
                try:
                    print(f"[TEST]: {test.testName}")
                    testSuccess = test.test()
                except Exception as e:
                    print(f"[Error]: An exception ({e}) occurred when executing test")
                    traceback.print_exc()
                    testSuccess = False
            
            # If the test failed then add it to the list of failing tests
            if testSuccess:
                self.passedTests.append(test)
                print(f"[PASSING]: {test.testName}")
            else:
                self.failedTests.append(test)
                print(f"[FAILING]: {test.testName}")
                    
        return len(self.failedTests) == 0

# This is thrown when a TestCase.test() method has not been implemented
class TestNotImplementedException(Exception):
    pass

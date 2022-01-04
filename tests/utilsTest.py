from Tournament import *
from test import *

class UtilsTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py"

    def test(self):
        subTests = []
        
        subTests.append(StrToBoolTest())
        subTests.append(TrunkTest())
        subTests.append(UnionTest())
        subTests.append(IntersectionTest())
        subTests.append(GetIDFromMentionTest())
        subTests.append(GetPrimaryTypeTest())
        
        testRunner = TestRunner(subTests)
        
        print("[DECK TEST]: Running sub tests...")
        return testRunner.executeTests()

class StrToBoolTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py str_to_bool(str)"

    def test(self):
        assert(str_to_bool("T"))
        assert(str_to_bool("t"))
        assert(str_to_bool("TRUE"))
        assert(str_to_bool("true"))
        assert(str_to_bool("1"))
                
        assert(not str_to_bool("F"))
        assert(not str_to_bool("f"))
        assert(not str_to_bool("FALSE"))
        assert(not str_to_bool("f"))
        assert(not str_to_bool("0"))
        
        assert(str_to_bool("NOT T OR F OR TRUE OR FALSE OR 1 OR 0") is None)
        return True
    
class TrunkTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py trunk(score)"
    
    def test(self):
        assert(trunk(1.12345) == 1.12)
        assert(trunk("a.bcdef") == "a.bc")
        return True

class UnionTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py union(vals)"
    
    def test(self):
        assert(Union([True, True]))
        assert(Union([True, False]))
        assert(Union([False, True]))
        assert(not Union([False, False]))
        return True

class IntersectionTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py intersection(vals)"
    
    def test(self):
        assert(Intersection([True, True]))
        assert(not Intersection([False, True]))
        assert(not Intersection([True, False]))
        assert(not Intersection([False, False]))
        return True

class GetIDFromMentionTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py get_ID_from_mention(mention)"
    
    def test(self):
        id = 80085537
        assert(get_ID_from_mention(f"<@{id}>") == id)
        assert(get_ID_from_mention(f"<@!{id}>") == id)
        assert(get_ID_from_mention(None) is None)
        return True

class GetPrimaryTypeTest(TestCase):
    def __init__(self):
        self.testName = "Tournament/utils.py getPrimaryType(types)"
        
    def test(self):
        types = ["Creature", "Land", "Artifact", "Enchantment", "Instant", "Sorcery", "Planeswalker"]
        for i in range(0, len(types)):
            for j in range(1, 20):
                testTypes = types[i::len(types) - 1].shuffle()
                if GetPrimaryTypeTest(testTypes) != types[i]:
                    print(f"Test with data {testTypes} failed")
                    return False
        return True

class SafeXMLFuncsTest(TestCase):   
    def __init__(self):
        self.testName = "Tournament/utils.py toSafeXML(str) and fromXML(str)"
        
    def test(self):
        for c in PROBLEM_XML_CHARS:
            assert(toSafeXML(c) == PROBLEM_XML_CHARS[c])            
            assert(c == fromXML(PROBLEM_XML_CHARS[c]))
        return True

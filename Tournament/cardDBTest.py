import cardDB
import time

#@profile
def test():
    c = cardDB.card("a // b", "flip")
    print(c.name)
    assert(c.name == "a")
    
    c = cardDB.card("a // b", "modal_dfc")
    print(c.name)
    assert(c.name == "a")
        
    c = cardDB.card("a // b", "transform")
    print(c.name)
    assert(c.name == "a")
    
    print("Testing card database")
    cards = cardDB.cardDB()
    print(f'{len(cards.cards)} cards were found. Running tests...')
    
    max = 5
    for i in range(max):
        print(f"Testing update cards method {i + 1}/{max}")
        time.sleep(1)
        cards.updateCards()

    print("Finished.")

if __name__ == '__main__':
    test()

import cardDB
import time

@profile
def test():
    print("Testing card database")
    cards = cardDB.cardDB()
    print(f'{len(cards.cards)} cards were found. Running tests...')
    
    # Basic tests
    for card in cards.cards.values():
        assert(card.equals(card.name + "      "))
        assert(card.compare(card.name) == 0)
    
    max = 5
    for i in range(max):
        print(f"Testing update cards method {i + 1}/{max}")
        time.sleep(1)
        cards.updateCards()

    print("Finished.")

if __name__ == '__main__':
    test()

import re
import requests
import json
import tempfile
import zipfile
import os.path
from typing import List

# Helps with memory being consumed
import gc
import ctypes

from time import time, sleep
from threading import Thread

from .exceptions import *


class card:
    def __init__(self, name: str, layout: str, types: List[str]):
        self.name = name.strip()
        if layout in ["modal_dfc", "transform", "flip"]:
            self.name = self.name.split("//")[0].strip()
        self.types: list = types

    def __str__(self):
        return f"{self.name}"

    def getName(self) -> str:
        return self.name

    def hasType(self, t: str) -> bool:
        return t in self.types

    def getTypes(self) -> List[str]:
        return self.types


class cardsDBLoadingError(Exception):
    pass


class cardDB:
    def __init__(
        self,
        updateTime: int = 24 * 60 * 60,
        mtgjsonURL: str = "https://www.mtgjson.com/api/v5/AllPrintings.json.zip",
    ):
        self.lastUpdate = 0
        self.updateTime = updateTime
        self.cards = dict()
        self.url = mtgjsonURL
        self.normaliseRegex = re.compile(",|\.|-|'")
        self.spacesRegex = re.compile(" +")
        self.cacheName = "AllPrintings.json"

        if self.isCacheIsUpToDate():
            # Allow for invalid cache
            updatedFromCache = self.updateFromCache()
            if not updatedFromCache:
                print("Updating CardsDB from cache")
                if not self.updateFromCache():
                    print("Error loading CardsDB from cache")
                    self.updateCards()
            else:
                print("CardsDB was loaded from cache")
        else:
            print("CardsDB cache was not up to date")
            self.updateCards()

        if len(self.cards) == 0:
            raise cardsDBLoadingError("Error loading CardsDB")

    # Makes two strings easier to compare by removing excess whitespace,
    # commas, hyphens, apostrophes and full stops.
    def normaliseCardName(self, string: str):
        return (
            re.sub(self.spacesRegex, " ", re.sub(self.normaliseRegex, "", string))
            .split("//")[0]
            .lower()
            .strip()
            .replace("û", "u")
        )
        # heck Lim-Dûl's Vault, it is the bane of my existence

    def needsUpdate(self) -> bool:
        return int(time()) - self.lastUpdate > self.updateTime

    # @profile
    def updateCardsFromJson(self, cardsJson: str) -> bool:
        tempCards = dict()
        parseSuccess = True

        # Try parse, if it goes wrong cry
        cardsJson = json.loads(cardsJson)
        try:
            data = cardsJson["data"]
            for Set in data:
                for card_ in data[Set]["cards"]:
                    # Check for reprint (also stops the back of a mdfc from being added)
                    # i hate mdfcs as they make this harder than it has to be
                    name = self.normaliseCardName(card_["name"])

                    if not name in tempCards:
                        cardObject = card(
                            card_["name"], card_["layout"], card_["types"]
                        )
                        if ("face" in card_) and (card_["face"] != "a"):
                            continue  # Rear of the card is ignored

                        tempCards[name] = cardObject

        except Exception as e:
            parseSuccess = False
            print(e)

        del cardsJson

        if parseSuccess:
            self.cards = tempCards
            self.lastUpdate = int(time())
        return parseSuccess

    def isCacheIsUpToDate(self) -> bool:
        if os.path.exists(self.cacheName):
            return int(time()) - getFileLastModified(self.cacheName) < self.updateTime
        return False

    def updateFromCache(self) -> bool:
        if os.path.exists(self.cacheName):
            status = False

            with open(self.cacheName, "r") as f:
                json = f.read()
                status: bool = self.updateCardsFromJson(json)

            return status
        else:
            return False

    # @profile
    def updateCards(self) -> bool:
        compressedCacheName = self.cacheName + ".zip"
        resp = requests.get(self.url, timeout=7.0, data="", verify=False)

        # Save zip file
        tmpFile = tmpFile = tempfile.TemporaryFile(
            mode="wb+", suffix="cardDB.py", prefix=compressedCacheName
        )
        for chunk in resp.iter_content(chunk_size=512 * 1024):
            if chunk:  # filter out keep-alive new chunks
                tmpFile.write(chunk)

        # Go to the start of the file before unzipping
        tmpFile.seek(0)

        # Decompress the file
        zip = zipfile.ZipFile(tmpFile, "r")
        zip.extract(self.cacheName, "./")

        # Close file
        zip.close()
        tmpFile.close()

        return self.updateFromCache()

    # Returns a cockatrice card name from the database, failing that the input
    # is returned. This is for turning cards into the format that cockatrice uses
    # for deck hashing, in future this method may be changed to return card objects.
    def getCard(self, cardName: str) -> card:
        name = ""
        nameNormal = self.normaliseCardName(cardName)

        if nameNormal in self.cards:
            return self.cards[nameNormal]
        else:
            raise CardNotFoundError(
                f"{cardName} could not be found in the card database."
            )


# Util methods for starting this db
def getFileLastModified(file_name: str) -> int:
    try:
        mtime = os.path.getmtime(file_name)
    except OSError:
        mtime = 0
    return mtime


def updateDB(db):
    while True:
        sleep(db.updateTime)
        while db.needsUpdate():
            db.updateCards()


def initCardDB():
    print("Creating card database...")
    db = cardDB()
    print(f"Created card database with {len(db.cards)} cards.")

    cardUpdateThread = Thread(target=updateDB, args=(db,))
    cardUpdateThread.start()

    return db

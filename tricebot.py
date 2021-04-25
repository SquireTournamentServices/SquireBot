import requests

class GameMade:
    def __init__(self, success: str, gameID: int, replayName: str):
        self.success = success
        self.gameID = gameID
        self.replayName = replayName

class TriceBot:    
    #Set externURL to the domain address and apiURL to the loopback address in LAN configs
    def __init__(self, authToken: str, apiURL: str="https://0.0.0.0:8000", externURL: str=""):
        self.authToken = authToken
        self.apiURL = apiURL
        
        if (externURL == ""):
            self.externURL = self.apiURL
        else:
            self.externURL = externURL
        
    # verify = false as self signed ssl certificates will cause errors here
    def req(self, urlpostfix: str, data: str):
        return requests.get(self.apiURL + "/" + urlpostfix, timeout=7.0, data=data,  verify=False).text
        
    def checkauthkey(self):
        return self.req("api/checkauthkey", self.authToken) == "1"
    
    def getDownloadLink(self, replayName):
        return self.externURL + "/" + replayName
            
    #  1 if success
    #  0 auth token is bad or error404 or network issue
    # -1 if player not found
    # -2 if an unknown error occurred
    def kickPlayer(self, gameID: int, name: str) -> int:
        body = "authtoken=" + self.authToken + "\n"
        body += "gameid=" + str(gameID) + "\n"
        body += "target=" + name        
        
        try:
            message = self.req("api/kickplayer", body)   
            print(message)
        except OSError as exc:
            #Network issues
            print("[TRICEBOT ERROR]: Netty error")
            return 0
        
        #Check for server error
        if (message == "timeout error" or message == "error 404" or message == "invalid auth token"):
            #Server issues         
            print("[TRICEBOT ERROR]: " + message)
            return 0
        
        if (message == "success"):
            return 1
        elif (message == "error not found"):
            return -1
        
        return -2
    
    def createGame(self, gamename: str, password: str, playercount: int, spectatorsallowed: bool, spectatorsneedpassword: bool, spectatorscanchat: bool, spectatorscanseehands: bool, onlyregistered: bool):
        body = "authtoken=" + self.authToken + "\n"
        body += "gamename=" + gamename + "\n"
        body += "password=" + password + "\n"
        body += "playerCount=" + str(playercount) + "\n"
        
        body += "spectatorsAllowed="
        if spectatorsallowed:
            body += "1"
        else:
            body +="0"
        body += "\n"
            
        body += "spectatorsNeedPassword="
        if spectatorsneedpassword:
            body += "1"
        else:
            body += "0"
        body += "\n"
        
        body += "spectatorsCanChat="
        if spectatorscanchat:
            body += "1"
        else:
            body +="0"
        body += "\n"
        
        body += "spectatorsCanSeeHands="
        if spectatorscanseehands:
            body += "1"
        else:
            body +="0"
        body += "\n"
        
        body += "onlyRegistered="
        if onlyregistered:
            body += "1"
        else:
            body +="0"
            
        try:
            message = self.req("api/creategame", body)   
            print(message)
        except OSError as exc:
            #Network issues
            print("[TRICEBOT ERROR]: Netty error")
            return GameMade(False, -1, "")
            
        #Check for server error
        if (message == "timeout error" or message == "error 404" or message == "invalid auth token"):
            #Server issues         
            print("[TRICEBOT ERROR]: " + message)
            return GameMade(False, -1, "")
        
        #Try to parse the message
        lines = message.split("\n")
        gameID: int = -1
        replayName: str = ""
        
        #Parse line for line
        for line in lines:
            parts = line.split("=")
            
            #Check length
            if (len(parts) >= 2):            
                tag = parts[0]
                value = ""
                
                i = 1
                while i < len(parts):
                    value += parts[i]
                    #readd equal signs in the gamename
                    if (i > 1):
                        value += "="
                    i+=1
                    
                if (tag == "gameid"):
                    #There has to be a better way to do this
                    try:
                        gameID = int(value)
                    except:
                        #Error checked at end
                        pass
                elif (tag == "replayName"):
                    replayName = value.replace(" ", "%20")
                #Ignore other tags
            #Ignores lines that have no equals in them
        
        #Check if there was an error
        success = gameID != -1 and replayName != ""
        return GameMade(success, gameID, replayName)

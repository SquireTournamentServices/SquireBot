import requests

class TriceBot:    
    def __init__(self, authToken, apiURL="https://0.0.0.0:8000"):
        self.authToken = authToken
        self.apiURL = apiURL
        
    # verify = false as self signed ssl certificates will cause errors here
    def req(self, urlpostfix, data):
        return requests.get(self.apiURL + "/" + urlpostfix, timeout=7.0, data=data,  verify=False).text
        
    def checkauthkey(self):
        return self.req("api/checkauthkey", self.authToken) == "1"
    
    def createGame(self, gamename, password, playercount, spectatorsallowed, spectatorsneedpassword, spectatorscanchat, spectatorscanseehands, onlyregistered):
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
            status = self.req("api/creategame/", body)     
        except OSError as exc:
            # logging.error(f"exception while requesting create game with body:\n{body}", exc_info=exc)
            return False

        if (status == "timeout error" or status == "error 404" or status == "invalid auth token"):
            return False
        
        return True

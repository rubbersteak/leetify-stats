from steamMapping import steamMapping
import re
import csv
import requests
import sys

class Match:
    apiPath = "https://api.cs-prod.leetify.com/api/games"

    def __init__(self, gameId):
        def getPlayers(self):
            playerList = {}
            for playerData in self.data["playerStats"]:
                playerList.update({int(playerData["steam64Id"]): Player(playerData)})
            return playerList
        self.id = gameId
        apiUrl = f"{self.apiPath}/{gameId}"
        r = requests.get(apiUrl)
        self.data = r.json()
        Player.getClutchData(apiUrl)
        self.players = getPlayers(self)
    
    def getUrl(self):
        prefix = "https://leetify.com/public/match-details"
        path = "overview"
        return f"{prefix}/{self.id}/{path}"

    def mapName(self):
        return self.data["mapName"]
    
    def getWinner(self):
        scores = enumerate(self.data["teamScores"])
        return (max(scores, key=lambda x: x[1])[0])
    
    def getScore(self, teamNum):
        return self.data["teamScores"][teamNum]
    
    def getMVP(self):
        mvp = max(self.players.values(), key=lambda x: x.leetify())
        return mvp

    def getPlayerStats(self, playerMapping):
        gameIds = self.players.keys()
        statList = []
        for steamId in playerMapping.values():
            if steamId in gameIds:
                statList.extend(list(self.players[steamId].stats().values()))
            else:
                statList.extend(list(Player(None).stats().values()))
        return statList
    
    def getStats(self):
        format = {
            "link": self.getUrl(),
            "team0": None,
            "team1": None,
            "map": self.mapName(),
            "winner": self.getWinner(),
            "mapChoice": None,
            "score0": self.getScore(0),
            "score1": self.getScore(1),
            "startingSide0": None,
            "startingSide1": None,
            "MVPLeetifyScore": self.getMVP().leetify(),
            "hidden0": None,
            "MVPName": self.getMVP().getName(),
            "scoreFirstHalf0": None,
            "scoreFirstHalf1": None,
            "scoreSecondHalf0": None,
            "scoreSecondHalf1": None,
            "overtime1-0": None,
            "overtime1-1": None,
            "overtime2-0": None,
            "overtime2-1": None,
            "players": self.getPlayerStats(steamMapping)
        }
        row = []
        for x in format.values():
            if not isinstance(x, list):
                row.append(x)
            else:
                row.extend(x)
        return row


class Player(dict):
    clutchData = None

    @classmethod
    def getClutchData(cls, url):
        if cls.clutchData is None:
            cls.clutchData = requests.get(f"{url}/clutches").json()

    def __init__(self, data):
        if data is not None:
            super().__init__(data)

    def getName(self):
        return self.get("name")
    
    def getId(self):
        if self.get("steam64Id"):
            return int(self["steam64Id"])
        return None

    def getKills(self):
        return self.get("totalKills")
    
    def getAssists(self):
        return self.get("totalAssists")
    
    def getDeaths(self):
        return self.get("totalDeaths")
    
    def leetify(self):
        if self.get("leetifyRating"):
            return self["leetifyRating"] * 100
        return None
    
    def totalDamage(self):
        return self.get("totalDamage")
    
    def utility(self):
        if not self.get("name"):
            return None
        heDamage = float(self["heFoesDamageAvg"] or 0) * float(self["heThrown"] or 0)
        molotovDamage = float(self["molotovFoesDamageAvg"] or 0) * float(self["molotovThrown"] or 0)
        return round(heDamage + molotovDamage)

    def enemiesFlashed(self):
        return self.get("flashbangHitFoe")
    
    def clutchesWon(self):
        if not self.getId():
            return None
        num = [[(x["steam64Id"] == self["steam64Id"] and x["clutchesWon"] > 0) for x in self.clutchData]][0]
        return sum(num)
    
    def stats(self):
        playerStats = {
            "kills" : self.getKills(),
            "assists": self.getAssists(),
            "deaths": self.getDeaths(),
            "leetify": self.leetify(),
            "totalDamage": self.totalDamage(),
            "utility": self.utility(),
            "enemiesFlashed": self.enemiesFlashed(),
            "clutchesWon": self.clutchesWon(),
        }
        return playerStats

def usage():
    print(f"Usage: {sys.argv[0]} <leetify-link>")
    print(f"Writes to out.csv in the current folder.")

def main():
    if len(sys.argv) != 2:
        usage()
        exit()

    url = sys.argv[1]
    
    m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', url)
    if not m:
        print("Error: no match id found from given URL.")
        usage()
        exit()

    gameId = m.group(0)
    game = Match(gameId)
    file = "out.csv"
    print(f"Writing file to {file}")
    with open(file, 'w') as csvfile:
        dataWriter = csv.writer(csvfile)
        dataWriter.writerow(game.getStats())


if __name__ == "__main__":
    main()
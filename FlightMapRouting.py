import csv
import heapq
from queue import PriorityQueue
import sys
import random
from collections import defaultdict

import geopy.distance


class Airport:

    def __init__(self, airportId, name, city, country, IATA, ICAO, latitude, longitude, altitude, timezone, DST, type,
                 source):
        self.airportId = airportId
        self.name = name
        self.city = city
        self.country = country
        self.IATA = IATA
        self.ICAO = ICAO
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.timezone = timezone
        self.DST = DST
        self.type = type
        self.source = source

    def __repr__(self) -> str:
        return f"\nairportId: {self.airportId}\nname: {self.name}\ncity: {self.city}\ncountry: {self.country}\nIATA: {self.IATA}\nICAO: {self.ICAO}\nlatitude: {self.latitude}\nlongitude: {self.longitude}\naltitude: {self.altitude}\ntimezone: {self.timezone}\nDST: {self.DST}\ntype: {self.type}" 


class Route:

    # https://www.statista.com/statistics/978646/cost-per-available-seat-mile-united-airlines/
    def __init__(self, srcId, dstId):
        self.srcId = srcId
        self.dstId = dstId
        self.cost = None
        self.duration = None
        self.distance = None

class SearchParameter:

    def __init__(self, dist, cost):
        self.dist = dist
        self.cost = cost

class FlightPathing:

    def __init__(self, airportsFile, routesFile):
        self.totalAirports = 0
        self.airportToIdMap = {}
        self.idToAirportMap = {}  # id to airport
        self.routeIdMap = defaultdict(dict)  # id to id
        self.parse_airports(airportsFile)
        self.parse_routes(routesFile)
        self.searchParameter = None
        


    def parse_airports(self, fileLocation: str):

        file = open(fileLocation, "r", encoding="utf8")
        airports = list(csv.reader(file, delimiter=","))
        file.close()
        for airport in airports:
            if airport[9] == "\\N":
                continue
            ap = Airport(int(airport[0]), airport[1], airport[2],
                              airport[3], airport[4], airport[5],
                              float(airport[6]), float(airport[7]), float(airport[8]),
                              float(airport[9]), airport[11], airport[12],
                              airport[13])
            self.idToAirportMap[int(airport[0])] = ap
            self.airportToIdMap[airport[1]] = ap
            self.totalAirports = max(int(airport[0]), self.totalAirports)

    def parse_routes(self, fileLocation: str):

        file = open(fileLocation, "r", encoding="utf8")
        routes = list(csv.reader(file, delimiter=","))
        file.close()

        for route in routes:
            if route[3] == "\\N":
                continue
            if route[5] == "\\N":
                continue
            if self.idToAirportMap.get(int(route[3])) == None:
                continue
            if self.idToAirportMap.get(int(route[5])) == None:
                continue
            self.routeIdMap[int(route[3])][int(route[5])] = Route(int(route[3]), int(route[5]))
        for routes in self.routeIdMap.values():
            for route in routes.values():
                route.cost = self.getCost(route.srcId, route.dstId)


    def getDist(self, srcId: int, dstId: int) -> float:
        src_airport = self.idToAirportMap.get(srcId)
        dst_airport = self.idToAirportMap.get(dstId)
        src_coord = (src_airport.latitude, src_airport.longitude)
        dst_coord = (dst_airport.latitude, dst_airport.longitude)
        return geopy.distance.distance(src_coord, dst_coord).km
    
    def getCost(self, srcId, dstId):
        baseFare = round(random.uniform(100, 200), 2)
        fuelCost = round(random.uniform(12.7 * 1.60934, 17.68 * 1.60934), 2) * self.getDist(srcId, dstId)
        return baseFare + fuelCost
    

    def createSearchParameter(self, dist: float, cost: float) -> SearchParameter:
        return SearchParameter(dist, cost)


    def getWeight(self, srcId: int, dstId: int, searchParameter: SearchParameter) :
        weight = getDist(srcId, dstId) * searchParameter.dist + getCost(srcId, dstId) * searchParameter.cost
        return weight

    
    def getTotalAirports(self):
        return self.totalAirports

    def _dijkstra(self, srcId: int, dstId: int) -> list[int]:
        weights = [sys.maxsize for i in range(self.getTotalAirports())]
        shortestPathTree = []
        pq = [(0.0, srcId)]
        while pq:
            currWeight, currId = heapq.heappop(pq)
            if currWeight >= weights[currId]:
                continue
            weights[currId] = currWeight
            shortestPathTree.append(currId)
            if currId == dstId:
                return self._traverseToSource(shortestPathTree)
            for nextRoute in self.routeIdMap.get(currId, {}).values():
                nextId = nextRoute.dstId
                print(nextId)
                nextWeight = currWeight + self.getDist(currId, nextId)
                heapq.heappush(pq, (nextWeight, nextId))
        return None
    
    def _traverseToSource(self, shortestPathTree: list[int]) -> list[int]:
        if len(shortestPathTree) < 2:
            return []
        dstId = shortestPathTree[-1]
        shortestPath = []
        for i in range(len(shortestPathTree) - 1, -1, -1):
            routes = self.routeIdMap.get(shortestPathTree[i])
            # if shortestPathTree[i] in routes
            for route in routes:
                if shortestPathTree[i] != route.srcId and dstId != route.dstId:
                    continue
                dstId = route.srcId
                shortestPath.append(route.srcId)
        shortestPath.reverse()
        return shortestPath
    
    def _idPathToAirport(self, shortestPath: list[int]) -> list[str]:
        if shortestPath == None:
            return None
        airports = []
        for id in shortestPath:
            airports.append(self.idToAirportMap.get(id).name)
        return airports
    
    def _airportPathToId(self, shortestPath: list[str]) -> list[int]:
        if shortestPath == None:
            return None
        airports = []
        for airport in shortestPath:
            airports.append(self.airportToIdMap.get(airport).airportId)
        return airports
    
    def getShortestPath(self, srcAirport: str, dstAirport: str) -> list[str]:
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        # get shortest path
        shortestPathId = self._dijkstra(srcId, dstId)
        shortestPathString = self._idPathToAirport(shortestPathId)
        return shortestPathString
    
    def existsByAirportName(self, airportName: str) -> bool:
        if airportName is None:
            raise TypeError("Method existByAirportName(): Airport name cannot be None")
        return airportName in self.airportToIdMap
    
    def getTotalCost(self, srcAirport: str, dstAirport: str) -> float:
        shortestPath = self.getShortestPath(srcAirport, dstAirport)



def main():
    airport_fileLocation = r"C:\Users\ambel\IdeaProjects\FlightPathing-main\venv\data\airports.dat"
    routes_fileLocation = r"C:\Users\ambel\IdeaProjects\FlightPathing-main\venv\data\routes.dat"
    flight_pathing = FlightPathing(airport_fileLocation, routes_fileLocation)
    searchParameter = flight_pathing.createSearchParameter(0.4,0.6)
    print(flight_pathing.getShortestPath("Goroka Airport", "Wagga Wagga City Airport")) # 1, 3363


main()

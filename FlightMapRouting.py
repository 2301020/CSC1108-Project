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
        self.routeIdMap = defaultdict(dict)  # id to route
        self.parse_airports(airportsFile)
        self.parse_routes(routesFile)
        self.searchParameter = None
        self.medianCost = self.getMedianCost()
        self.medianDist = self.getMedianDist()
        


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
        weight = (self.getDist(srcId, dstId) / self.medianDist ) * searchParameter.dist + (self.getCost(srcId, dstId) / self.medianCost) * searchParameter.cost
        return weight

    
    def getTotalAirports(self):
        return self.totalAirports

    class Vertex:
        def __init__(self, currId, prevId , weight):
            self.currId = currId
            self.prevId = prevId
            self.weight = weight
            
        
        def __eq__(self, other):
            return self.currId == other.currId
        
        def __lt__(self, other):
            return self.weight < other.weight

    def _dijkstra(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> list[int]:
        weights = [sys.maxsize for i in range(self.getTotalAirports())]
        edgeTo = {}
        pq = [self.Vertex(srcId, -1 ,0.0)]
        while pq:
            currVertex = heapq.heappop(pq)
            currId, currWeight = currVertex.currId, currVertex.weight
            if currWeight >= weights[currId]:
                continue
            weights[currId] = currWeight
            edgeTo[currId] = currVertex.prevId
            if currId == dstId:
                return self._traverseToSrc(edgeTo, dstId)
            for nextRoute in self.routeIdMap.get(currId, {}).values():
                nextId = nextRoute.dstId
                nextWeight = currWeight + self.getWeight(currId, nextId, searchParameter)
                heapq.heappush(pq, self.Vertex(nextId, currId, nextWeight))
        return None
    
    def _traverseToSrc(self, spTree: dict, dstId: int) -> list[int]:
        res = []
        currId = dstId
        while currId != -1:
            res.append(currId)
            currId = spTree.get(currId)
        res.reverse()
        return res

    
    def _idPathToAirport(self, shortestPath: list[int]) -> list[str]:
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
    
    def getShortestPath(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter) -> list[str]:
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        # get shortest path
        shortestPathId = self._dijkstra(srcId, dstId, searchParameter)
        shortestPathString = self._idPathToAirport(shortestPathId)
        return shortestPathString
    
    def existsByAirportName(self, airportName: str) -> bool:
        if airportName is None:
            raise TypeError("Method existByAirportName(): Airport name cannot be None")
        return airportName in self.airportToIdMap
    
    def getTotalCost(self, srcAirport: str, dstAirport: str) -> float:
        shortestPath = self.getShortestPath(srcAirport, dstAirport)

    def getMedianCost(self) -> float:
        costs = []
        route: Route
        for routes in self.routeIdMap.values():
            for route in routes.values():
                costs.append(route.cost)
        return self.getMedian(costs)
    
    def getMedianDist(self) -> float:
        dists = []
        route: Route
        for routes in self.routeIdMap.values():
            for route in routes.values():
                dist = self.getDist(route.srcId, route.dstId)
                dists.append(dist)
        return self.getMedian(dists)
        
    def getMedian(self, arr: list) -> list:
        arr.sort()
        if len(arr) // 2 == 0: # 0 - 6, median is 3.
            return arr[len(arr) // 2]
        else:
            return (arr[len(arr) // 2 + 1] + arr[len(arr) // 2]) / 2

def main():
    airport_fileLocation = r"C:\Users\ambel\IdeaProjects\FlightPathing-main\venv\data\airports.dat"
    routes_fileLocation = r"C:\Users\ambel\IdeaProjects\FlightPathing-main\venv\data\routes.dat"
    flight_pathing = FlightPathing(airport_fileLocation, routes_fileLocation)
    searchParameter = flight_pathing.createSearchParameter(0.2,0.8)
    # print(flight_pathing.getMedianDist())
    print(flight_pathing.getShortestPath("Goroka Airport", "Wagga Wagga City Airport", searchParameter)) # 1, 3363


main()

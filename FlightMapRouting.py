import csv
import heapq
import os
from queue import PriorityQueue
import sys
import random
from collections import defaultdict

import geopy.distance

AIRCRAFT_SPEED = 860
PASSENGER_SIZE_747 = 440

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
        self.time = None
        self.distance = None

class SearchParameter:

    def __init__(self, cost, time):
        self.cost = cost
        self.time = time

    def __eq__(self, other: object):
        if not isinstance(other, SearchParameter):
            return False
        return True if self.cost == other.cost and self.time == other.time else False
    
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, SearchParameter):
            return True
        return False if self.cost == other.cost and self.time == other.time else True

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
        self.medianTime = self.getMedianTime()
        self.dijkstra = Dijkstra(self.routeIdMap, self.medianCost, self.medianTime, self.getTotalAirports())
        


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
                route.dist = self._setDist(route.srcId, route.dstId)
                route.cost = self._setCost(route.srcId, route.dstId)
                route.time = self._setTime(route.srcId, route.dstId)

    def _setDist(self, srcId: int, dstId: int) -> float:
        src_airport = self.idToAirportMap.get(srcId)
        dst_airport = self.idToAirportMap.get(dstId)
        src_coord = (src_airport.latitude, src_airport.longitude)
        dst_coord = (dst_airport.latitude, dst_airport.longitude)
        return geopy.distance.distance(src_coord, dst_coord).km
    
    def _setTime(self, srcId, dstId):
        route = self.routeIdMap.get(srcId).get(dstId)
        waitingTime = round(random.uniform(0.5, 4), 2)
        travellingTime = route.dist / AIRCRAFT_SPEED
        return waitingTime + travellingTime
    
    def _setCost(self, srcId, dstId):
        route = self.routeIdMap.get(srcId).get(dstId)
        baseFare = round(random.uniform(100, 200), 2)
        fuelCost = round(random.uniform(12.7, 17.68), 2) / PASSENGER_SIZE_747 * route.dist * 0.621371
        return baseFare + fuelCost
    
    def getTotalAirports(self):
        return self.totalAirports
    
    def createSearchParameter(self, dist: float, cost: float) -> SearchParameter:
        return SearchParameter(dist, cost)

    def _idPathToAirport(self, shortestPath: list[int]) -> list[Airport]:
        airports = []
        if shortestPath is not None: 
            for id in shortestPath:
                airports.append(self.idToAirportMap.get(id).name)
        return airports
    
    # returns airport objects in a list
    def _idPathtoAirportObjects(self, shortestPath: list[int]) -> list[Airport]:
        airports = []
        if shortestPath is not None: 
            for id in shortestPath:
                airports.append(self.idToAirportMap.get(id))
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
        shortestPathId = self.dijkstra.getShortestPath(srcId, dstId, searchParameter)
        shortestPathString = self._idPathToAirport(shortestPathId)
        return shortestPathString
    
    # returns airport objects in a list
    def getShortestPathWithObjects(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter) -> list[Airport]:
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        # get shortest path
        shortestPathId = self.dijkstra.getShortestPath(srcId, dstId, searchParameter)
        shortestPathString = self._idPathtoAirportObjects(shortestPathId)
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
    
    def getMedianTime(self) -> float:
        dists = []
        route: Route
        for routes in self.routeIdMap.values():
            for route in routes.values():
                dists.append(route.time)
        return self.getMedian(dists)
        
    def getMedian(self, arr: list) -> list:
        arr.sort()
        if len(arr) // 2 == 0: # 0 - 6, median is 3.
            return arr[len(arr) // 2]
        else:
            return (arr[len(arr) // 2 + 1] + arr[len(arr) // 2]) / 2
        
    def getTotalCost(self, srcAirport: int, dstAirport: int, searchParameter: SearchParameter) -> float:
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId
        
        return self.dijkstra.getTotalCost(srcId, dstId, searchParameter)
    
    def getTotalTime(self, srcAirport: int, dstAirport: int, searchParameter: SearchParameter) -> float:
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId
        
        return self.dijkstra.getTotalTime(srcId, dstId, searchParameter)

class Dijkstra:

    def __init__(self, routeIdMap, medianCost, medianTime, totalAirports):
        self.routeIdMap = routeIdMap
        self.srcId = None
        self.dstId = None
        self.medianCost = medianCost
        self.medianTime = medianTime
        self.totalAirport = totalAirports
        self.shortestPath = []
        self.searchParameter = None

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
        self._setSearchParameters(srcId, dstId, searchParameter)
        weights = [sys.maxsize for i in range(self.totalAirport)]
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
            nextRoute: Route
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
    
    def _setSearchParameters(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        self.srcId = srcId
        self.dstId = dstId
        self.searchParameter = searchParameter
    
    def getShortestPath(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> list[str]:
        # get airport id
        if srcId != self.srcId or dstId != self.dstId or searchParameter != self.searchParameter:
            self.shortestPath = self._dijkstra(srcId, dstId, searchParameter)

        # get shortest path
        return self.shortestPath
    
    def getWeight(self, srcId: int, dstId: int, searchParameter: SearchParameter) :
        route = self.routeIdMap.get(srcId).get(dstId)
        costWeightage = (route.cost / self.medianCost) * searchParameter.cost
        timeWeightage = (route.time / self.medianTime) * searchParameter.time
        weight = costWeightage + timeWeightage
        return weight
    
    def getTotalCost(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> float:
        if srcId != self.srcId or dstId != self.dstId or searchParameter != self.searchParameter:
            self.shortestPath = self._dijkstra(srcId, dstId, searchParameter)

        totalCost = 0
        if self.shortestPath is not None: 
            for i in range(1, len(self.shortestPath), 1):
                currId = self.shortestPath[i - 1]
                nextId = self.shortestPath[i]
                route = self.routeIdMap.get(currId).get(nextId)
                totalCost += route.cost
        return totalCost
    
    def getTotalTime(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> float:
        if not srcId == self.srcId or not dstId == self.dstId or not searchParameter == self.searchParameter:
            self.shortestPath = self._dijkstra(srcId, dstId, searchParameter)

        totalTime = 0
        if self.shortestPath is not None: 
            for i in range(1, len(self.shortestPath), 1):
                currId = self.shortestPath[i - 1]
                nextId = self.shortestPath[i]
                route = self.routeIdMap.get(currId).get(nextId)
                totalTime += route.time
        return totalTime


    


def main():

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the relative path to the file within the Data folder
    airports_path = os.path.join('data', 'airports.dat')
    routes_path = os.path.join('data', 'routes.dat')

    # Construct the full path
    airports_location = os.path.join(script_directory, airports_path)
    routes_location = os.path.join(script_directory, routes_path)

    flight_pathing = FlightPathing(airports_path, routes_path)
    
    searchParameter = flight_pathing.createSearchParameter(0.8,0.2)
    # print(flight_pathing.getMedianDist())
    print(flight_pathing.getShortestPath("Singapore Changi Airport", "Fukuoka Airport", searchParameter)) # 1, 3363
    totalTime = flight_pathing.getTotalTime("Singapore Changi Airport", "Fukuoka Airport", searchParameter)
    totalCost = flight_pathing.getTotalCost("Singapore Changi Airport", "Fukuoka Airport", searchParameter)
    print("Time: ", totalTime)
    print("Cost: ", totalCost)
    #testing function to return objects
    print(flight_pathing.getShortestPathWithObjects("Singapore Changi Airport", "Fukuoka Airport", searchParameter))

main()

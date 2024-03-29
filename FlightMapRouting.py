import csv
import heapq
import os
from queue import PriorityQueue
import sys
import random
from collections import defaultdict

import geopy.distance
import copy

AIRCRAFT_SPEED = 860
PASSENGER_SIZE_747 = 440
random.seed(50)
KM_TO_MILE = 0.621371


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


class Vertex:
    def __init__(self, currId, prevId, weight):
        self.currId = currId
        self.prevId = prevId
        self.weight = weight

    def __eq__(self, other):
        return (self.currId, self.prevId, self.weight) == (other.currId, other.prevId, other.weight)

    def __lt__(self, other):
        return self.weight < other.weight        


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
        self.median = MedianCostAndTime(self.routeIdMap)
        self.medianCost = self.median.getMedianCost()
        self.medianTime = self.median.getMedianTime()
        self.dijkstra = Dijkstra(self.routeIdMap, self.medianCost, self.medianTime, self.getTotalAirports())
        self.astar = Astar(self.idToAirportMap, self.routeIdMap, self.medianCost, self.medianTime,
                           self.getTotalAirports())
        self.bellmanford = bellmanford(self.idToAirportMap, self.routeIdMap, self.medianCost, self.medianTime, self.getTotalAirports())

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
            if route[3] == "\\N" or route[5] == "\\N":
                continue
            src_id = int(route[3])
            dst_id = int(route[5])

            if self.idToAirportMap.get(src_id) is None or self.idToAirportMap.get(dst_id) is None:
                continue

            self.routeIdMap[src_id][dst_id] = Route(src_id, dst_id)
            self.routeIdMap[src_id][dst_id].dist = self._setDist(src_id, dst_id)
            self.routeIdMap[src_id][dst_id].cost = self._setCost(src_id, dst_id)
            self.routeIdMap[src_id][dst_id].time = self._setTime(src_id, dst_id)

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
        route = self.routeIdMap[srcId][dstId]
        baseFare = round(random.uniform(100, 200), 2)
        fuelCost = round(random.uniform(12.7, 17.68), 2) / PASSENGER_SIZE_747 * route.dist * KM_TO_MILE
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
        if shortestPath is None:
            return None
        airports = []
        for airport in shortestPath:
            airports.append(self.airportToIdMap.get(airport).airportId)
        return airports

    def getShortestPathId(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter, algorithm: str) -> list[Airport]:
        # Check for valid algorithm: dijkstra/astar/bellmanford
        algorithm = algorithm.upper()
        if not algorithm == "DIJKSTRA" and not algorithm == "ASTAR" and not algorithm == "BELLMAN-FORD":
            raise TypeError("No such algorithm supported.")

        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        # get the shortest path
        shortestPathId = []
        if algorithm == "DIJKSTRA":
            shortestPathId = self.dijkstra.getShortestPath(srcId, dstId, searchParameter)
        elif algorithm == "ASTAR":
            shortestPathId = self.astar.getShortestPath(srcId, dstId, searchParameter)
        elif algorithm == "BELLMAN-FORD":
            shortestPathId = self.bellmanford.bellmanford(srcId, dstId, searchParameter)
        return shortestPathId

    def getShortestPathStr(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter, algorithm: str):
        calculatedPathId = self.getShortestPathId(srcAirport, dstAirport, searchParameter, algorithm)
        return self._idPathToAirport(calculatedPathId)

    # returns airport objects in a list
    def getShortestPathWithObjects(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter, algorithm: str):
        calculatedPathId = self.getShortestPathId(srcAirport, dstAirport, searchParameter, algorithm)
        return self._idPathtoAirportObjects(calculatedPathId)

    def existsByAirportName(self, airportName: str) -> bool:
        if airportName is None:
            raise TypeError("Method existByAirportName(): Airport name cannot be None")
        return airportName in self.airportToIdMap

    def existsByAirportId(self, airportName: int) -> bool:
        if airportName is None:
            raise TypeError("Method existByAirportId(): Airport name cannot be None")
        return airportName in self.idToAirportMap

    def getTotalCost(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter) -> float:
        # get airport id

        if self.existsByAirportName(srcAirport) is None or self.existsByAirportName(dstAirport) is None:
            raise TypeError("Method getShortestPath(): {0} / {1} cannot be None".format(srcAirport, dstAirport))

        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        return self.dijkstra.getTotalCost(srcId, dstId, searchParameter)

    def getTotalTime(self, srcAirport: str, dstAirport: str, searchParameter: SearchParameter) -> float:
        # get airport id
        if self.existsByAirportName(srcAirport) is None or self.existsByAirportName(dstAirport) is None:
            raise TypeError("Method getShortestPath(): {0} / {1} cannot be None".format(srcAirport, dstAirport))

        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        return self.dijkstra.getTotalTime(srcId, dstId, searchParameter)


class MedianCostAndTime:
    def __init__(self, routeIdMap):
        self.costs = []
        self.time = []
        self.routeIdMap = routeIdMap
        self.calculateMedians()

    def calculateMedians(self):
        for routes in self.routeIdMap.values():
            for route in routes.values():
                self.costs.append(route.cost)
                self.time.append(route.time)

    def getMedianCost(self) -> float:
        median1, median2 = self.getMedianIndices(self.costs)
        return (self.costs[median1] + self.costs[median2]) / 2

    def getMedianTime(self) -> float:
        median1, median2 = self.getMedianIndices(self.time)
        return (self.time[median1] + self.time[median2]) / 2

    def getMedianIndices(self, arr: list) -> tuple[int, int]:
        arr.sort()
        # if Array is even length, return the average of the two middle elements
        if len(arr) % 2 == 0:  # 0 - 5, median is 2.
            return len(arr) // 2, len(arr) // 2 + 1
        # if Array is odd length, return the middle element
        else:
            return len(arr) // 2, len(arr) // 2


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
        self.nodes_searched = 0

    def _dijkstra(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> list[int]:
        self._setSearchParameters(srcId, dstId, searchParameter)
        weights = [sys.maxsize for i in range(self.totalAirport)]
        edgeTo = {}
        pq = [Vertex(srcId, -1, 0.0)]
        while pq:
            self.nodes_searched += 1
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
                heapq.heappush(pq, Vertex(nextId, currId, nextWeight))
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

    def getShortestPath(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> list[int]:
        # get airport id
        if srcId != self.srcId or dstId != self.dstId or searchParameter != self.searchParameter:
            self.shortestPath = self._dijkstra(srcId, dstId, searchParameter)

        # get the shortest path
        return self.shortestPath

    def getWeight(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        route = self.routeIdMap.get(srcId).get(dstId)
        costWeightage = (route.cost / self.medianCost) * searchParameter.cost
        timeWeightage = (route.time / self.medianTime) * searchParameter.time
        weight = costWeightage + timeWeightage
        return weight

    def _calculateTotalMetric(self, srcId: int, dstId: int, searchParameter: SearchParameter, metric: str) -> float:
        if srcId != self.srcId or dstId != self.dstId or searchParameter != self.searchParameter:
            self.shortestPath = self._dijkstra(srcId, dstId, searchParameter)

        totalMetric = 0
        if self.shortestPath is not None:
            for i in range(1, len(self.shortestPath)):
                currId = self.shortestPath[i - 1]
                nextId = self.shortestPath[i]
                route = self.routeIdMap.get(currId).get(nextId)
                if metric == "cost":
                    totalMetric += route.cost
                elif metric == "time":
                    totalMetric += route.time
        return totalMetric

    def getTotalCost(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> float:
        return self._calculateTotalMetric(srcId, dstId, searchParameter, "cost")

    def getTotalTime(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> float:
        return self._calculateTotalMetric(srcId, dstId, searchParameter, "time")


class Astar:
    def __init__(self, idToAirportMap, routeIdMap, medianCost, medianTime, totalAirports):
        self.idToAirportMap = idToAirportMap
        self.routeIdMap = routeIdMap
        self.srcId = None
        self.dstId = None
        self.medianCost = medianCost
        self.medianTime = medianTime
        self.totalAirport = totalAirports
        self.shortestPath = []
        self.searchParameter = None
        self.nodes_searched = 0

    def getWeight(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        route = self.routeIdMap.get(srcId).get(dstId)
        costWeightage = (route.cost / self.medianCost) * searchParameter.cost
        timeWeightage = (route.time / self.medianTime) * searchParameter.time
        weight = costWeightage + timeWeightage
        return weight

    def heuristic_cost_estimate(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        src_airport = self.idToAirportMap.get(srcId)
        dst_airport = self.idToAirportMap.get(dstId)
        src_coord = (src_airport.latitude, src_airport.longitude)
        dst_coord = (dst_airport.latitude, dst_airport.longitude)
        dist = geopy.distance.distance(src_coord, dst_coord).km

        baseFare = round(random.uniform(100, 200), 2)
        fuelCost = round(random.uniform(12.7, 17.68), 2) / PASSENGER_SIZE_747 * dist * KM_TO_MILE
        cost = baseFare + fuelCost

        waitingTime = random.uniform(0.5, 4)
        travellingTime = dist / AIRCRAFT_SPEED
        time = waitingTime + travellingTime

        costWeightage = (cost / self.medianCost) * searchParameter.cost
        timeWeightage = (time / self.medianTime) * searchParameter.time
        return costWeightage + timeWeightage

    def getShortestPath(self, srcId: int, dstId: int, searchParameter: SearchParameter) -> list[int]:
        open_list = PriorityQueue()
        open_list.put((0, srcId))
        came_from = {}
        g_score = {srcId: 0}

        while not open_list.empty():
            self.nodes_searched += 1
            current_cost, current = open_list.get()

            if current == dstId:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for neighbor in self.routeIdMap.get(current, {}):
                tentative_g_score = g_score[current] + self.getWeight(current, neighbor, searchParameter)
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    priority = tentative_g_score + self.heuristic_cost_estimate(neighbor, dstId, searchParameter)
                    open_list.put((priority, neighbor))
        return []
    

class bellmanford: 

    def __init__(self, idToAirportMap, routeIdMap, medianCost, medianTime, totalAirports):
        self.idToAirportMap = idToAirportMap
        self.routeIdMap = routeIdMap
        self.srcId = None
        self.dstId = None
        self.medianCost = medianCost
        self.medianTime = medianTime
        self.totalAirport = totalAirports
        self.shortestPath = []
        self.searchParameter = None
        self.nodes_searched = 0

        def __eq__(self, other):
            return self.currId == other.currId

        def __lt__(self, other):
            return self.weight < other.weight

    def getWeight(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        route = self.routeIdMap.get(srcId).get(dstId)
        costWeightage = (route.cost / self.medianCost) * searchParameter.cost
        timeWeightage = (route.time / self.medianTime) * searchParameter.time
        weight = costWeightage + timeWeightage
        return weight
    
    def bellmanford(self, srcId: int, dstId: int, searchParameter: SearchParameter):
        initAirportVertex = {i: Vertex(i, 0, sys.maxsize) for i in self.idToAirportMap}
        del initAirportVertex[srcId]
        airportVertex = {srcId: Vertex(srcId, -1, 0.0)}
        airportVertex.update(initAirportVertex)

        for _ in range(len(airportVertex) - 1):
            tempVertex = copy.deepcopy(airportVertex)
            for vertexId in tempVertex:
                for edges in self.routeIdMap.get(vertexId, {}).values():
                    self.nodes_searched += 1
                    if tempVertex[vertexId].weight + self.getWeight(edges.srcId, edges.dstId, searchParameter) < tempVertex[edges.dstId].weight:
                        tempVertex[edges.dstId].weight = tempVertex[vertexId].weight + self.getWeight(edges.srcId, edges.dstId, searchParameter)
                        tempVertex[edges.dstId].prevId = vertexId
            if tempVertex == airportVertex:
                break
            else:
                airportVertex = tempVertex
    
        # # Checks for negative cycles, this is not neccessary in this case because our graph does not have any negative edges
        # for vertexId in airportVertex:
        #     for edges in self.routeIdMap.get(vertexId, {}).values():
        #         if airportVertex[vertexId].weight + self.getWeight(edges.srcId, edges.dstId, searchParameter) < airportVertex[edges.dstId].weight:
        #             print("Negative cycle detected")
        #             return None

        # Calculate the total weight of the journey of each airport it visits

        shortest_path = []
        current_vertex = dstId
        while current_vertex != -1:
            if airportVertex[current_vertex].prevId == 0:
                break
            shortest_path.append(current_vertex)
            current_vertex = airportVertex[current_vertex].prevId

        shortest_path.reverse()

        return shortest_path



def readAirportAndRoutes():
    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))

#     # Define the relative path to the file within the Data folder
    airports_path = os.path.join('data', 'airports.dat')
    routes_path = os.path.join('data', 'routes.dat')

    return FlightPathing(airports_path, routes_path)

def main():

    #display GUI here first

    #This is the test function to test functionality of FlightMapRouting.py

    flight_pathing = readAirportAndRoutes()
    searchParameter = flight_pathing.createSearchParameter(0.8, 0.2)

    for _ in range(50):
        airportList = list(flight_pathing.idToAirportMap.values())
        airport1 = random.choice(airportList)
        airport2 = random.choice(airportList)

        dijkstraPath = flight_pathing.getShortestPathStr(airport1.name, airport2.name, searchParameter, "dijkstra")
        astarPath = flight_pathing.getShortestPathStr(airport1.name, airport2.name, searchParameter, "astar")
        bellmanford = flight_pathing.getShortestPathStr(airport1.name, airport2.name, searchParameter, "bellman-ford")
        dijkstraNodes = flight_pathing.dijkstra.nodes_searched
        astarNodes = flight_pathing.astar.nodes_searched
        bellmanfordNodes = flight_pathing.bellmanford.nodes_searched

        if dijkstraPath == []:# or dijkstraWeight == astarWeight:
            continue

        print("\nfrom: {0} To: {1}".format(airport1.name, airport2.name))

        print("Shortest path for each algorithm")
        print("Dijkstra:        ", dijkstraPath)
        print("Astar:           ", astarPath)
        print("Bellman-Ford:    ", bellmanford)

        print("Number of nodes visited by each algorithm")
        print("Dijkstra: ", dijkstraNodes)
        print("Astar:    ", astarNodes)
        print("Bellman-Ford: ", bellmanfordNodes)


# if __name__ == "__main__":
#     main()

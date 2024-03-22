import csv
import heapq
import os
from queue import PriorityQueue
import sys

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


class Route:

    def __init__(self, srcId, dstId):
        self.srcId = srcId
        self.dstId = dstId
        self.cost = None
        self.duration = None
        self.distance = None


class FlightPathing:

    def __init__(self, airportsFile, routesFile):
        self.airportToIdMap = {}
        self.idToAirportMap = {}  # id to airport
        self.routeIdMap = {}  # id to id
        self.parse_airports(airportsFile)
        self.parse_routes(routesFile)

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

    def parse_routes(self, fileLocation: str):

        file = open(fileLocation, "r", encoding="utf8")
        routes = list(csv.reader(file, delimiter=","))
        file.close()

        for route in routes:
            if route[3] == "\\N":
                continue
            if route[5] == "\\N":
                continue
            if route[3] not in self.routeIdMap:
                self.routeIdMap[int(route[3])] = []
            self.routeIdMap[int(route[3])].append(Route(int(route[3]),
                                                          int(route[5])))

    def getDist(self, srcId: int, dstId: int) -> float:
        src_airport = self.idToAirportMap.get(srcId)
        dst_airport = self.idToAirportMap.get(dstId)
        src_coord = (src_airport.latitude, src_airport.longitude)
        dst_coord = (dst_airport.latitude, dst_airport.longitude)
        return geopy.distance.distance(src_coord, dst_coord).km
    
    def getTotalAirports(self):
        return len(self.idToAirportMap)

    def _dijkstra(self, srcId: int, dstId: int) -> list[int]:
        def _traverseToSource(shortestPathTree: list[int]) -> list[int]:
            dstId = shortestPathTree[-1]
            shortestPath = []
            for i in range(len(shortestPathTree) - 1, -1, -1):
                routes = self.routeIdMap.get(shortestPathTree[i])
                for route in routes:
                    if shortestPathTree[i] != route.srcId and dstId != route.dstId:
                        continue
                    dstId = route.srcId
                    shortestPath.append(route.srcId)
            shortestPath.reverse()
            return shortestPath

        weights = [sys.maxsize for i in range(self.getTotalAirports())]
        shortestPathTree = []
        self._came_from = {}  # Dictionary to store predecessors
        pq = [(0.0, srcId)]
        while pq:
            currWeight, currId = heapq.heappop(pq)
            if currWeight >= weights[currId]:
                continue
            weights[currId] = currWeight
            shortestPathTree.append(currId)
            if currId == dstId:
                return _traverseToSource(shortestPathTree)
            for nextRoute in self.routeIdMap.get(currId):
                nextId = nextRoute.dstId
                nextWeight = currWeight + self.getDist(currId, nextId)
                heapq.heappush(pq, (nextWeight, nextId))
        return None

    
    def _idPathToAirport(self, shortestPath: list[int]) -> list[str]:
        airports = []
        for id in shortestPath:
            airports.append(self.idToAirportMap.get(id).name)
        return airports

    def _astar(self, srcId: int, dstId: int) -> list[int]:
        # Define the heuristic function (distance between two airports)
        def heuristic(id):
            dst_airport = self.idToAirportMap.get(dstId)
            dst_coord = (dst_airport.latitude, dst_airport.longitude)
            airport = self.idToAirportMap.get(id)
            coord = (airport.latitude, airport.longitude)
            return geopy.distance.distance(coord, dst_coord).km

        # Initialize the priority queue
        pq = []
        # Push the start node onto the queue
        heapq.heappush(pq, (0, srcId))
        # Initialize dictionaries to store cost and previous nodes
        cost = {srcId: 0}
        prev = {srcId: None}

        # A* algorithm
        while pq:
            current_cost, current_id = heapq.heappop(pq)
            if current_id == dstId:
                break
            for route in self.routeIdMap.get(current_id, []):
                new_cost = cost[current_id] + 1  # You can modify this to include distance or other cost metrics
                if route.dstId not in cost or new_cost < cost[route.dstId]:
                    cost[route.dstId] = new_cost
                    priority = new_cost + heuristic(route.dstId)  # A* heuristic function
                    heapq.heappush(pq, (priority, route.dstId))
                    prev[route.dstId] = current_id

        # Reconstruct the shortest path
        shortest_path = []
        current_id = dstId
        while current_id is not None:
            shortest_path.append(current_id)
            current_id = prev[current_id]

        return shortest_path[::-1]  # Reverse the path to get the correct order
    
    def getShortestPath(self, srcAirport: str, dstAirport: str, algorithm: str) -> list[str]:
        #Check for valid algorithm: dijkstra/astar
        algorithm = algorithm.upper()
        if not algorithm == "DIJKSTRA" and not algorithm == "ASTAR":
            raise TypeError("No such algorithm supported.")
        # get airport id
        if not self.existsByAirportName(srcAirport) or not self.existsByAirportName(dstAirport):
            raise TypeError("Method getShortestPath(): srcAirport / dstAirport cannot be None")
        srcId = self.airportToIdMap.get(srcAirport).airportId
        dstId = self.airportToIdMap.get(dstAirport).airportId

        # get shortest path
        shortestPathId = "No such algorithm"
        if algorithm == "DIJKSTRA":
            shortestPathId = self._dijkstra(srcId, dstId)
        elif algorithm == "ASTAR":
            shortestPathId = self._astar(srcId, dstId)
        shortestPathString = self._idPathToAirport(shortestPathId)
        return shortestPathString
    
    def existsByAirportName(self, airportName: str) -> bool:
        if airportName is None:
            raise TypeError("Method existByAirportName(): Airport name cannot be None")
        return airportName in self.airportToIdMap


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
    print("Dijkstra: ", flight_pathing.getShortestPath("Goroka Airport", "Wagga Wagga City Airport","dijkstra")) # 1, 3363
    print("Astar: ", flight_pathing.getShortestPath("Goroka Airport", "Wagga Wagga City Airport","astar")) # 1, 3363


main()

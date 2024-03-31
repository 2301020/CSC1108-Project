import customtkinter
from CTkMessagebox import CTkMessagebox
from tkintermapview import TkinterMapView
import FlightMapRouting
from ttkwidgets.autocomplete import AutocompleteCombobox
from collections import deque

import requests
import random

# https://github.com/TomSchimansky/TkinterMapView?tab=readme-ov-file#create-path-from-position-list

customtkinter.set_default_color_theme("blue")
class App(customtkinter.CTk):
    """Docstring for App.

    Args:
        customtkinter (_type_): _description_

    """
    _APP_NAME = "flight_planning_app.py"
    _WIDTH = 1200
    _HEIGHT = 800

    _AIRPORT_FILELOCATION = r"data/airports.dat"
    _ROUTES_FILELOCATION = r"data/routes.dat"

    def __init__(self, *args, **kwargs):
        """
        Initialize the UI class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """
        super().__init__(*args, **kwargs)

        self.title(self._APP_NAME)
        self.geometry(f"{self._WIDTH}x{self._HEIGHT}")
        self.minsize(self._WIDTH, self._HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.flight_pathing = FlightMapRouting.FlightPathing(
            self._AIRPORT_FILELOCATION, self._ROUTES_FILELOCATION)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.frame_left = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.frame_left.grid_columnconfigure(0, weight=1)

        self.frame_right = customtkinter.CTkFrame(self, corner_radius=0)
        self.frame_right.grid(row=0, column=1, pady=0, padx=0, sticky="nsew")
        self.frame_right.grid_columnconfigure(0, weight=1)

        self.frame_bottom = customtkinter.CTkFrame(self, corner_radius=0)
        self.frame_bottom.grid(row=1, column=0, columnspan=2,
                               pady=0, padx=0, sticky="nsew")
        self.frame_bottom.grid_columnconfigure(0, weight=1)

        self.title_label = customtkinter.CTkLabel(
            self.frame_right,
            text="Flight Planning App",
            font=("Helvetica", 20)
        )

        self.title_label.grid(column=0, row=0, sticky="EW", padx=5, pady=5)

        try:
            requests.get("https://www.google.com", timeout=5)

            self.map_widget = TkinterMapView(
                self.frame_left, width=600, height=500, corner_radius=0)
            self.map_widget.grid(column=0, row=0, sticky="EW")

            # location A (x1+x2)/2 = camera postition
            self.map_widget.set_address("Singapore")
            self.map_widget.set_zoom(3)
            self.map_widget.set_tile_server(
                "https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        except requests.ConnectionError:
            CTkMessagebox(
                title="Error", message="No internet connection. Map will not be displayed")
        except requests.Timeout:
            CTkMessagebox(
                title="Error", message="Connection timeout. Map will not be displayed")
        except AttributeError:
            pass

        self.source_label = customtkinter.CTkLabel(
            self.frame_right, text="Source Country/Airport")
        self.source_label.grid(column=0, row=1, sticky="EW", padx=5, pady=5)

        self.getAirports()
        self.source_name = customtkinter.StringVar()
        self.source_combobox = AutocompleteCombobox(
            self.frame_right, completevalues=self.airport_list, width=20, height=5, textvariable=self.source_name)
        self.source_combobox.grid(
            column=0, row=2, sticky="EW", padx=5, pady=5, columnspan=2)

        self.destination_Label = customtkinter.CTkLabel(
            self.frame_right, text="Destination Country/Airport")
        self.destination_Label.grid(
            column=0, row=3, sticky="EW", padx=5, pady=5, columnspan=2)

        self.destination_name = customtkinter.StringVar()
        self.destination_combobox = AutocompleteCombobox(
            self.frame_right, completevalues=self.airport_list, width=20, height=5, textvariable=self.destination_name)
        self.destination_combobox.grid(
            column=0, row=4, sticky="EW", padx=5, pady=5, columnspan=2)

        self.alternate_path_trip_switch = customtkinter.CTkSwitch(self.frame_right,
                                                                  text="Alternate Path (Only for Dijkstra)", progress_color="red", corner_radius=0, width=10, height=2)

        self.alternate_path_trip_switch.grid(
            column=0, row=5, sticky="EW", padx=5, pady=5)

        self.radio_frame = customtkinter.CTkFrame(
            self.frame_right, corner_radius=0)
        self.radio_frame.grid(column=0, row=6, sticky="EW",
                              padx=5, pady=5, columnspan=2)
        self.radio_frame.columnconfigure(0, weight=1)
        self.radio_frame.columnconfigure(1, weight=1)

        self.options_label = customtkinter.CTkLabel(
            self.radio_frame, text="Preference", font=("Helvetica", 15))
        self.options_label.grid(
            column=0, row=0, sticky="EW", padx=5, pady=5, columnspan=2)

        self.cost_value = customtkinter.StringVar()
        self.time_value = customtkinter.StringVar()
        self.cost_value.set("Cost: 50%")
        self.time_value.set("Time: 50%")

        self.cost_label = customtkinter.CTkLabel(
            self.radio_frame, text="Cost", font=("Helvetica", 20), textvariable=self.cost_value)
        self.cost_label.grid(column=0, row=1, sticky="E", padx=5, pady=5)

        self.time_label = customtkinter.CTkLabel(
            self.radio_frame, text="Time", font=("Helvetica", 20), textvariable=self.time_value)
        self.time_label.grid(column=1, row=1, sticky="W", padx=5, pady=5)

        self.selected_ratio_value = customtkinter.IntVar()
        self.selected_ratio_value.set(50)
        self.option_slider = customtkinter.CTkSlider(
            self.radio_frame, from_=0, to=100, number_of_steps=10, variable=self.selected_ratio_value, command=lambda value: self.ratio_calculator()
        )
        self.option_slider.grid(
            column=0, row=2, sticky="EW", padx=5, pady=5, columnspan=2)
        self.preference_label = customtkinter.CTkLabel(
            self.radio_frame, text="Preference", font=("Helvetica", 15))

        self.cost_label = customtkinter.CTkLabel(
            self.radio_frame, text="Cost", font=("Helvetica", 20))
        self.cost_label.grid(column=0, row=3, sticky="W", padx=5, pady=5)

        self.time_label = customtkinter.CTkLabel(
            self.radio_frame, text="Time", font=("Helvetica", 20))
        self.time_label.grid(column=1, row=3, sticky="E", padx=5, pady=5)
        # self.selected_radiobox = customtkinter.StringVar()
        # r1 = customtkinter.CTkRadioButton(
        #     self.radio_frame, text="Shortest Path", variable=self.selected_radiobox, value="shortest_path")
        # r2 = customtkinter.CTkRadioButton(
        #     self.radio_frame, text="Cheapest Path", variable=self.selected_radiobox, value="cheapest_path")
        # r3 = customtkinter.CTkRadioButton(
        #     self.radio_frame, text="Fastest Path", variable=self.selected_radiobox, value="fastest_path")
        # r1.grid(column=0, row=1, sticky="EW", padx=5, pady=5)
        # r2.grid(column=0, row=2, sticky="EW", padx=5, pady=5)
        # r3.grid(column=0, row=3, sticky="EW", padx=5, pady=5)

        self.algor_label = customtkinter.CTkLabel(
            self.radio_frame, text="Algorithm selection", font=("Helvetica", 15))
        self.algor_label.grid(column=0, row=4, sticky="EW",
                              padx=5, pady=5, columnspan=2)

        self.algorthim_selection = customtkinter.StringVar()
        self.algor_dropDownList = customtkinter.CTkComboBox(self.radio_frame, corner_radius=0, fg_color=None, values=[
                                                            "Astar", "Bellman-Ford", "Dijkstra"], variable=self.algorthim_selection, cursor="hand2", state="readonly")
        self.algorthim_selection.set("Astar")
        self.algor_dropDownList.grid(
            column=0, row=5, sticky="EW", padx=5, pady=10, columnspan=2)

        self.search_button = customtkinter.CTkButton(
            self.frame_right, text="Search", command=self.search)
        self.search_button.grid(
            column=0, row=7, sticky="EW", padx=5, pady=5, columnspan=2)

        self.airport_list = []
        self.airport_route = []
        self.airport_deque = deque()
        self.total_cost_deque = deque()
        self.total_time_deque = deque()
        self.toplevel_window = None

    def ratio_calculator(self):
        """
        Calculates the cost and time values based on the selected ratio value.

        Retrieves the selected ratio value from the UI and updates the cost and time values accordingly.

        Parameters:
        - self: The current instance of the UI class.

        Returns:
        - None
        """
        value = self.selected_ratio_value.get()
        self.cost_value.set(f"Cost: {100 -value}%")
        self.time_value.set(f"Time: {value}%")

    def getAirports(self):
        """
        Retrieves a sorted list of airport names.

        Returns:
            list: A sorted list of airport names.
        """
        self.airport_list = sorted(
            [airport.name for airport in self.flight_pathing.idToAirportMap.values()])    # temp class

    def search(self):
        """
        Perform a search for the shortest flight path between a source and destination airport.

        This method retrieves the source and destination airport names from the UI,
        validates them, and then calls the appropriate methods to calculate the shortest flight path.
        If a valid path is found, it displays the flight results on the UI.

        Returns:
            None
        """
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()

        airport_alt_route_string = None
        self.airport_route = []
        source = self.source_name.get()
        destination = self.destination_name.get()

        self.getAirports()
        print(source, destination)

        if not source or not destination:
            # CTkMessagebox(
            # title="Error", message="Please enter a source and destination")
            # return
            # for random testing purposes
            random.seed()
            source = random.choice(self.airport_list)
            destination = random.choice(self.airport_list)
        # elif not self.selected_radiobox.get():
        #     CTkMessagebox(title="Error", message="Please select a preference")
        #     return
        elif source == destination:
            CTkMessagebox(
                title="Error", message="Source and destination cannot be the same")
            return
        elif source not in self.airport_list or destination not in self.airport_list:
            CTkMessagebox(
                title="Error", message="Invalid source or destination")
            return

        if (self.algorthim_selection.get() == "Dijkstra" and self.alternate_path_trip_switch.get() == 1):
            airport_alt_route_string = self.flight_pathing.getAlternativePath(
                source, destination, self.get_slider_value())
            self.airport_route = self.retrieve_airport(
                airport_alt_route_string)
        elif (self.algorthim_selection.get() != "Dijkstra" and self.alternate_path_trip_switch.get() == 1):
            CTkMessagebox(
                title="Error", message="Alternate path only available for Dijkstra")
            return
        else:
            self.airport_route = self.flight_pathing.getShortestPathWithObjects(
                source, destination, self.get_slider_value(), self.algorthim_selection.get())

        if self.airport_route is None or not self.airport_route:
            CTkMessagebox(
                title="Error", message="No routes found")
            return
        self.airport_deque.append(self.airport_route)

        match self.algorthim_selection.get():
            case "Astar":
                self.total_cost_deque.append(self.total_cost(
                    self.flight_pathing.astar.shortestPath))
                self.total_time_deque.append(self.total_time(
                    self.flight_pathing.astar.shortestPath))
            case "Bellman-Ford":
                self.total_cost_deque.append(self.total_cost(
                    self.flight_pathing.bellmanford.shortestPath))
                self.total_time_deque.append(self.total_time(
                    self.flight_pathing.bellmanford.shortestPath))
            case "Dijkstra":
                self.total_cost_deque.append(self.total_cost(
                    self.flight_pathing.dijkstra.getShortestPath(self.flight_pathing.airportToIdMap.get(source).airportId, self.flight_pathing.airportToIdMap.get(destination).airportId, self.get_slider_value())))
                self.total_time_deque.append(self.total_time(
                    self.flight_pathing.dijkstra.shortestPath))

        if len(self.airport_deque) > 5:
            self.airport_deque.popleft()
            self.total_time_deque.popleft()
            self.total_cost_deque.popleft()

        print(self.airport_route)
        self.displayFlightResults()

    def retrieve_airport(self, airport_name: list[str]) -> list[FlightMapRouting.Airport]:
        """
        Retrieves a list of Airport objects based on the given airport names.

        Args:
            airport_name (list[str]): A list of airport names.

        Returns:
            list[FlightMapRouting.Airport]: A list of Airport objects corresponding to the given airport names.
        """
        airport_list = []
        for name in airport_name:
            airport_list.append(self.flight_pathing.airportToIdMap[name])
        return airport_list

    def get_slider_value(self) -> FlightMapRouting.SearchParameter:
        """
        Returns the search parameter based on the value of the slider.

        The search parameter is calculated based on the selected ratio value of the slider.
        The ratio value is divided by 100 to get the first parameter of the search parameter,
        and the difference between 100 and the ratio value divided by 100 is used as the second parameter.

        Returns:
            FlightMapRouting.SearchParameter: The search parameter based on the slider value.
        """
        value = self.selected_ratio_value.get()
        search_param = FlightMapRouting.SearchParameter(
            (100 - value) / 100, value / 100)
        return search_param

    def plotPath(self, airport: FlightMapRouting.Airport, previous_airport: FlightMapRouting.Airport):
        """
        Plot a path between two airports on the map.

        Args:
            airport (FlightMapRouting.Airport): The current airport.
            previous_airport (FlightMapRouting.Airport): The previous airport.

        Returns:
            None
        """
        marker_1 = self.map_widget.set_marker(
            airport.latitude, airport.longitude, text=airport.name)
        if previous_airport is not None:
            marker_2 = self.map_widget.set_marker(
                previous_airport.latitude, previous_airport.longitude, text=previous_airport.name)
            self.map_widget.set_path(
                [marker_1.position, marker_2.position], width=3, color="red")

    def displayFlightResults(self):
        """
        Displays the flight results on the UI.

        Args:
            airportList (list[FlightMapRouting.Airport]): A list of airports representing the flight route.

        Returns:
            None
        """
        self.flight_info = customtkinter.CTkLabel(
            self.frame_bottom, text="Possible routes", font=("Helvetica", 20))
        self.flight_info.grid(column=0, row=0, sticky="EW", padx=5, pady=5)

        self.route_list_frame = customtkinter.CTkScrollableFrame(
            self.frame_bottom, corner_radius=0)
        self.route_list_frame.grid(
            column=0, row=1, sticky="EW", padx=5, pady=5)
        self.route_list_frame.grid_columnconfigure(0, weight=1)
        self.route_list_frame.grid_columnconfigure(1, weight=7)
        self.route_list_frame.grid_rowconfigure(0, weight=2)
        self.route_list_frame.grid_rowconfigure(1, weight=2)
        self.route_list_frame.grid_rowconfigure(2, weight=2)
        self.route_list_frame.grid_rowconfigure(3, weight=2)
        self.route_list_frame.grid_rowconfigure(4, weight=2)

        # self.route_number = customtkinter.CTkLabel(
        #     self.route_list_frame, text=f"Route {0+1}")
        # self.route_number.grid(
        #     column=0, row=0, sticky="EW", padx=5, pady=5, rowspan=2)

        # self.route_frame = customtkinter.CTkFrame(
        #     self.route_list_frame, corner_radius=0)
        # self.route_frame.grid(column=1, row=0, sticky="EW",
        #                       padx=5, pady=5, rowspan=2)
        # self.route_frame.grid_columnconfigure(0, weight=6)
        # self.route_frame.grid_columnconfigure(1, weight=1)

        # airport_names = ' -> '.join([airport.name for airport in airportList])
        # self.route_list = customtkinter.CTkLabel(
        #     self.route_frame, text=airport_names  )
        # self.route_list.grid(column=0, row=0, sticky="EW", padx=15, pady=5)
        # self.more_details_button = customtkinter.CTkButton(
        #     self.route_frame, text="More details", command=lambda: self.displayRouteDetails(airportList), cursor="hand2")
        # self.more_details_button.grid(
        #     column=1, row=0, sticky="EW", padx=5, pady=5)

        for index, airportList in enumerate(reversed(self.airport_deque)):
            countdown_index = len(self.airport_deque) - 1 - index
            self.route_number = customtkinter.CTkLabel(
                self.route_list_frame, text=f"Route {countdown_index+1}")
            self.route_number.grid(
                column=0, row=index, sticky="EW", padx=5, pady=5)

            self.route_frame = customtkinter.CTkFrame(
                self.route_list_frame, corner_radius=0)
            self.route_frame.grid(column=1, row=index, sticky="EW",
                                  padx=5, pady=15)
            self.route_frame.grid_columnconfigure(0, weight=6)
            self.route_frame.grid_columnconfigure(1, weight=1)

            airport_names = ' -> '.join(
                [Airport.name for Airport in airportList])
            self.route_list = customtkinter.CTkLabel(
                self.route_frame, text=airport_names)
            self.route_list.grid(column=0, row=0, sticky="E", padx=15, pady=5)
            self.more_details_button = customtkinter.CTkButton(
                self.route_frame, text="More details",
                command=(lambda a=airportList,
                         index=countdown_index: self.displayRouteDetails(a, index)),
                cursor="hand2")
            self.more_details_button.grid(
                column=1, row=0, sticky="E", padx=5, pady=5)

        # for index, airport in enumerate(airportList):

        # if self.toplevel_window is not None or not self.toplevel_window.winfo_exists():
        #     self.toplevel_window = RouteDetails(self)
        #     self.toplevel_window.displayRouteDetails(airportList)
        # else:
        #     self.toplevel_window.displayRouteDetails(airportList)

    def displayRouteDetails(self, airportList: list[FlightMapRouting.Airport], index: int):
        """
        Displays the route details for a given list of airports.

        Args:
            airportList (list[FlightMapRouting.Airport]): A list of airports representing the route.

        Returns:
            None
        """

        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()

        if (self.toplevel_window is not None):
            self.toplevel_window.focus()
            return

        self.toplevel_window = customtkinter.CTkToplevel(self, takefocus=True)
        self.toplevel_window.bind("<Destroy>", self.on_toplevel_destroy)

        self.toplevel_window.title("Route Details")
        self.toplevel_window.geometry("500x300")
        self.toplevel_window.minsize(500, 300)
        self.toplevel_window.grid_columnconfigure(0, weight=1)
        self.toplevel_window.grid_columnconfigure(1, weight=1)
        self.toplevel_window.grid_rowconfigure(0, weight=1)

        total_cost_value = customtkinter.StringVar()
        total_cost_value.set(self.total_cost_deque[index])
        total_time_value = customtkinter.StringVar()
        total_time_value.set(self.total_time_deque[index])

        self.total_cost_label = customtkinter.CTkLabel(
            self.toplevel_window, font=("Helvetica", 20), textvariable=total_cost_value)
        self.total_cost_label.grid(
            column=0, row=0, sticky="EW", padx=5, pady=5)
        self.total_time_label = customtkinter.CTkLabel(
            self.toplevel_window, font=("Helvetica", 20), textvariable=total_time_value)
        self.total_time_label.grid(
            column=0, row=1, sticky="EW", padx=5, pady=5)

        self.flight_info_frame = customtkinter.CTkScrollableFrame(
            self.toplevel_window, corner_radius=0)
        self.flight_info_frame.grid(
            column=0, row=2, sticky="EW", padx=5, pady=5, columnspan=2)
        self.flight_info_frame.grid_columnconfigure(0, weight=1)

        previous_airport = None
        for index, airport in enumerate(airportList):
            self.plotPath(airport, previous_airport)
            self.stop_number = customtkinter.CTkLabel(
                self.flight_info_frame, text=f"Stop {index+1}", font=("Helvetica", 20))
            self.stop_number.grid(column=0, row=index,
                                  sticky="EW", padx=5, pady=5)

            airport_frame = customtkinter.CTkFrame(
                self.flight_info_frame, corner_radius=0, border_color=("Black", "White"))
            self.createAirportFrame(airport_frame, airport)
            airport_frame.grid(column=1, row=index,
                               sticky="EW", padx=5, pady=5)

            previous_airport = airport
        self.toplevel_window.after(10, self.toplevel_window.lift)

    def total_cost(self, shortestPath) -> str:
        return f"Total Estimated Cost: ${round(self.flight_pathing.getTotalCost(shortestPath),2)}"

    def total_time(self, shortestPath) -> str:
        # convert decimal time to hours and minutes
        time = self.flight_pathing.getTotalTime(shortestPath)
        hours = int(time)
        minutes = int((time - hours) * 60)
        return f"Total Estimated Time: {hours} hours {minutes} minutes"

    def createAirportFrame(self, airport_frame: customtkinter.CTkFrame, airport: FlightMapRouting.Airport) -> customtkinter.CTkFrame:
        """
        Creates and configures a frame to display airport information.

        Args:
            airport_frame (customtkinter.CTkFrame): The frame to be configured.
            airport (FlightMapRouting.Airport): The airport object containing the information to be displayed.

        Returns:
            customtkinter.CTkFrame: The configured airport frame.
        """
        airport_frame.grid_columnconfigure(0, weight=1)
        airport_frame.grid_columnconfigure(1, weight=1)
        airport_frame.grid_columnconfigure(2, weight=1)

        airport_name = customtkinter.CTkLabel(
            airport_frame, text=f"Name: {airport.name}")
        airport_name.grid(column=0, row=0, sticky="EW", padx=10, pady=5)

        airport_country = customtkinter.CTkLabel(
            airport_frame, text=f"Country: {airport.country}")
        airport_country.grid(column=0, row=1, sticky="EW", padx=5, pady=5)

        airport_city = customtkinter.CTkLabel(
            airport_frame, text=f"City: {airport.city}")
        airport_city.grid(column=0, row=2, sticky="EW", padx=5, pady=5)

        airport_IATA = customtkinter.CTkLabel(
            airport_frame, text=f"IATA: {airport.IATA}")
        airport_IATA.grid(column=0, row=3, sticky="EW", padx=5, pady=5)

        airport_ICAO = customtkinter.CTkLabel(
            airport_frame, text=f"ICAO: {airport.ICAO}")
        airport_ICAO.grid(column=0, row=4, sticky="EW", padx=5, pady=5)

        return airport_frame

    def on_toplevel_destroy(self, event):
        self.toplevel_window = None

    def on_closing(self):
        self.destroy()
        exit(0)

    def start(self):
        self.mainloop()    
    
if __name__ == "__main__":
    app = App()
    app.start()

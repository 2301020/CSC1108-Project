from typing import Tuple
import customtkinter
from CTkMessagebox import CTkMessagebox
from tkintermapview import TkinterMapView
import FlightMapRouting
from ttkwidgets.autocomplete import AutocompleteCombobox

import requests
import random

# https://github.com/TomSchimansky/TkinterMapView?tab=readme-ov-file#create-path-from-position-list

customtkinter.set_default_color_theme("blue")

# TODO: Add a class to find the airport class with the name via FlightPathing.airportToIdMap and use the airport name to get the airport object

class App(customtkinter.CTk):

    _APP_NAME = "flight_planning_app.py"
    _WIDTH = 1200
    _HEIGHT = 800

    _AIRPORT_FILELOCATION = r"data/airports.dat"
    _ROUTES_FILELOCATION = r"data/routes.dat"

    def __init__(self, *args, **kwargs):
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

       # self.source_entry = customtkinter.CTkEntry(self.frame_right)
       # self.source_entry.grid(column=0, row=2, sticky="EW", padx=5, pady=5)
        self.getAirports()
        self.source_name = customtkinter.StringVar()
        self.source_combobox = AutocompleteCombobox(
            self.frame_right, completevalues=self.airport_list, width=20, height=5, textvariable=self.source_name)
        self.source_combobox.grid(column=0, row=2, sticky="EW", padx=5, pady=5, columnspan=2)

        self.destination_Label = customtkinter.CTkLabel(
            self.frame_right, text="Destination Country/Airport")
        self.destination_Label.grid(
            column=0, row=3, sticky="EW", padx=5, pady=5, columnspan=2)

       # self.destination_entry = customtkinter.CTkEntry(self.frame_right)
       # self.destination_entry.grid(column=0, row=4, sticky="EW", padx=5, pady=5)
        self.destination_name = customtkinter.StringVar()
        self.destination_combobox = AutocompleteCombobox(
            self.frame_right, completevalues=self.airport_list, width=20, height=5, textvariable=self.destination_name)
        self.destination_combobox.grid(
            column=0, row=4, sticky="EW", padx=5, pady=5, columnspan=2)

        # self.round_trip_switch_state = customtkinter.StringVar(
        #     value="Single trip")
        # self.round_trip_switch = customtkinter.CTkSwitch(self.frame_right, textvariable=self.round_trip_switch_state, command=self.roundTripToggle,
        #                                                  onvalue="ROUND_TRIP", offvalue="SINGLE_TRIP", progress_color="red", corner_radius=0, width=10, height=2)
        # self.round_trip_switch.grid(
        #     column=0, row=5, sticky="EW", padx=5, pady=5)

        self.radio_frame = customtkinter.CTkFrame(
            self.frame_right, corner_radius=0)
        self.radio_frame.grid(column=0, row=6, sticky="EW", padx=5, pady=5, columnspan=2)
        self.radio_frame.columnconfigure(0, weight=1)
        self.radio_frame.columnconfigure(1, weight=1)

        self.options_label = customtkinter.CTkLabel(
            self.radio_frame, text="Preference", font=("Helvetica", 15))
        self.options_label.grid(column=0, row=0, sticky="EW", padx=5, pady=5, columnspan=2)
        
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
        self.option_slider.grid(column=0, row=2, sticky="EW", padx=5, pady=5, columnspan=2)
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
        self.algor_label.grid(column=0, row=4, sticky="EW", padx=5, pady=5, columnspan=2)

        self.algorthim_selection = customtkinter.StringVar()
        self.algor_dropDownList = customtkinter.CTkComboBox(self.radio_frame, corner_radius=0, fg_color=None, values=[
                                                            "Astar", "Bellman-Ford", "Dijkstra"], variable=self.algorthim_selection, cursor="hand2", state="readonly")
        self.algorthim_selection.set("Astar")
        self.algor_dropDownList.grid(
            column=0, row=5, sticky="EW", padx=5, pady=10, columnspan=2)

        self.search_button = customtkinter.CTkButton(
            self.frame_right, text="Search", command=self.search)
        self.search_button.grid(column=0, row=7, sticky="EW", padx=5, pady=5, columnspan=2)

        self.airport_list = []
        self.airport_route = []
        self.toplevel_window = None
    
    def ratio_calculator(self):
        value = self.selected_ratio_value.get()
        self.cost_value.set(f"Cost: {value}%")
        self.time_value.set(f"Time: {100 - value}%")
    
    def getAirports(self):
        self.airport_list = sorted(
            [airport.name for airport in self.flight_pathing.idToAirportMap.values()])    # temp class

    # def roundTripToggle(self):
    #     self.round_trip_switch_state.set(
    #         "Round trip" if self.round_trip_switch_state.get() == "Single trip" else "Single trip")

    def search(self):
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()
        
        airport_route_string = None
        self.airport_route = []
        source = self.source_name.get()
        destination = self.destination_name.get()

        self.getAirports()
        print(source, destination)

        if not source or not destination:
            # CTkMessagebox(
                #title="Error", message="Please enter a source and destination")
            #return
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
        
        airport_route_string = self.flight_pathing.getShortestPath(
            source, destination, self.get_slider_value(), self.algorthim_selection.get())
        if airport_route_string is None or not airport_route_string:
            CTkMessagebox(
                title="Error", message="No routes found")
            return
        self.airport_route = self.retrieve_airport(airport_route_string)

        print(self.airport_route)
        self.displayFlightResults(self.airport_route)
        # sourceLocation = self.map_widget.set_address(source, marker=True)
        # destinationLocation = self.map_widget.set_address(destination, marker=True)
        # self.map_widget.set_path([sourceLocation.position, destinationLocation.position], width=3, color="blue")
        # self.map_widget.set_position(sourceLocation.position, zoom=5, deg_y=0, deg_x=0)

    def retrieve_airport(self, airport_name: list[str]) -> list[FlightMapRouting.Airport]:
        airport_list = []
        for name in airport_name:
            airport_list.append(self.flight_pathing.airportToIdMap[name])
        return airport_list

    def get_slider_value(self) -> FlightMapRouting.SearchParameter:
        value = self.selected_ratio_value.get()
        search_param = FlightMapRouting.SearchParameter(
            value / 100, (100 - value) / 100)
        return search_param

    def plotPath(self, airport: FlightMapRouting.Airport, previous_airport: FlightMapRouting.Airport):
        marker_1 = self.map_widget.set_marker(
            airport.latitude, airport.longitude, text=airport.name)
        if previous_airport is not None:
            marker_2 = self.map_widget.set_marker(
                previous_airport.latitude, previous_airport.longitude, text=previous_airport.name)
            self.map_widget.set_path(
                [marker_1.position, marker_2.position], width=3, color="red")

    def displayFlightResults(self, airportList: list[FlightMapRouting.Airport]):
        self.flight_info = customtkinter.CTkLabel(
            self.frame_bottom, text="Possible routes")
        self.flight_info.grid(column=0, row=0, sticky="EW", padx=5, pady=5)
        
        self.route_list_frame = customtkinter.CTkScrollableFrame(
            self.frame_bottom, corner_radius=0)
        self.route_list_frame.grid(column=0, row=1, sticky="EW", padx=5, pady=5)
        self.route_list_frame.grid_columnconfigure(0, weight=1)
        self.route_list_frame.grid_columnconfigure(1, weight=4)
        self.route_number = customtkinter.CTkLabel(self.route_list_frame, text=f"Route {0+1}")
        self.route_number.grid(column=0, row=0,sticky="EW", padx=5, pady=5, rowspan=2)
        
        self.route_frame = customtkinter.CTkFrame(self.route_list_frame, corner_radius=0)
        self.route_frame.grid(column=1, row=0, sticky="EW", padx=5, pady=5, rowspan=2)
        self.route_frame.grid_columnconfigure(0, weight=6)
        self.route_frame.grid_columnconfigure(1, weight=1)
        
        airport_names = ' -> '.join([airport.name for airport in airportList])
        self.route_list = customtkinter.CTkLabel(self.route_frame, text=airport_names, )
        self.route_list.grid(column=0, row=0, sticky="EW", padx=15, pady=5)
        self.more_details_button = customtkinter.CTkButton(self.route_frame, text="More details", command=lambda: self.displayRouteDetails(airportList), cursor="hand2")
        self.more_details_button.grid(column=1, row=0, sticky="EW", padx=5, pady=5)
        
        # for index, airport in enumerate(airportList):
            
        
        # if self.toplevel_window is not None or not self.toplevel_window.winfo_exists():
        #     self.toplevel_window = RouteDetails(self)
        #     self.toplevel_window.displayRouteDetails(airportList)
        # else:
        #     self.toplevel_window.displayRouteDetails(airportList)
                
        
    def displayRouteDetails(self, airportList: list[FlightMapRouting.Airport]):
        
        if(self.toplevel_window is not None):
            self.toplevel_window.focus()
            return
        
        self.toplevel_window = customtkinter.CTkToplevel(self, takefocus=True)
        self.toplevel_window.bind("<Destroy>", self.on_toplevel_destroy)

        self.toplevel_window.title("Route Details")
        self.toplevel_window.geometry("500x300")
        self.toplevel_window.minsize(500, 300)
        self.toplevel_window.grid_columnconfigure(0, weight=1)
        self.toplevel_window.grid_rowconfigure(0, weight=1)
        
        self.flight_info_frame = customtkinter.CTkScrollableFrame(self.toplevel_window, corner_radius=0)
        self.flight_info_frame.grid(column=0, row=0, sticky="EW", padx=5, pady=5)
        self.flight_info_frame.grid_columnconfigure(0, weight=1)    
            
        previous_airport = None
        for index, airport in enumerate(airportList):
            self.plotPath(airport, previous_airport)
            self.stop_number = customtkinter.CTkLabel(
                self.flight_info_frame, text=f"Stop {index+1}", font=("Helvetica", 20))
            self.stop_number.grid(column=0, row=index,
                                  sticky="EW", padx=5, pady=5)

            airport_frame = customtkinter.CTkFrame(
                self.flight_info_frame, corner_radius=0,border_color=("Black","White"))
            self.createAirportFrame(airport_frame, airport)
            airport_frame.grid(column=1, row=index,
                               sticky="EW", padx=5, pady=5)

            previous_airport = airport
            
    def createAirportFrame(self,airport_frame: customtkinter.CTkFrame, airport: FlightMapRouting.Airport) -> customtkinter.CTkFrame:
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

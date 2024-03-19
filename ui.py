from tkinter import Tk
from tkinter import ttk
from tkintermapview import TkinterMapView

# https://github.com/TomSchimansky/TkinterMapView?tab=readme-ov-file#create-path-from-position-list

class App(Tk):

    _APP_NAME = "flight_planning_app.py"
    _WIDTH = 1200
    _HEIGHT = 800

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title(self._APP_NAME)
        self.geometry(f"{self._WIDTH}x{self._HEIGHT}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Return>", self.search)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)


        self.title_label = ttk.Label(
            self,
            text="Flight Planning App",
        )

        self.title_label.grid(column=0, row=0, sticky="EW", padx=5, pady=5)

        self.map_widget = TkinterMapView(width=700, height=500, corner_radius=0)
        self.map_widget.grid(column=0, row=1, sticky="NW",rowspan=5)

        # location A (x1+x2)/2 = camera postition
        self.map_widget.set_address("Singapore")
        self.map_widget.set_zoom(3)

        self.source_Label = ttk.Label(self, text="Source Country/Airport")
        self.source_Label.grid(column=1, row=1, sticky="EW", padx=5, pady=5)

        self.source_entry = ttk.Entry(self)
        self.source_entry.grid(column=1, row=2, sticky="EW", padx=5, pady=5)

        self.destination_Label = ttk.Label(self, text="Destination Country/Airport")
        self.destination_Label.grid(column=1, row=3, sticky="EW", padx=5, pady=5)

        self.destination_entry = ttk.Entry(self)
        self.destination_entry.grid(column=1, row=4, sticky="EW", padx=5, pady=5)

        self.search_button = ttk.Button(self, text="Search", command=self.search)
        self.search_button.grid(column=1, row=5, sticky="EW", padx=5, pady=5)


    def search(self):
        pass
        

    def plot_path(self, source, destination):
        marker_1 = self.map_widget.set_marker(source.longtitude, source.latitude, text=source.name)
        marker_2 = self.map_widget.set_marker(destination[0], destination[1], text="Kuala Lumpur Airport")

        path_1 = self.map_widget.set_path([marker_1.position, marker_2.position],width=3, color="red")

    def displayFlightResults(self, source, destination):
        self.flight_info = ttk.Label(self, text="Flight Information")
        self.flight_info.grid(column=1, row=3, sticky="E", padx=5, pady=5)

        self.flight_starting_country = ttk.Label(self, text=f"Starting Country: {source.name}")
        self.flight_starting_country.grid(column=1, row=4, sticky="E", padx=5, pady=5)

# marker_1 = map_widget.set_marker(1.3558572118659549,103.98638538648154, text="Changi Airport")
# marker_2 = map_widget.set_marker(3.1578589977287805,101.70339753766487, text="Kuala Lumpur Airport")

# path_1 = map_widget.set_path([marker_1.position, marker_2.position],width=3, color="red")
    def on_closing(self):
        self.destroy()
        exit(0)

    def start(self):
        self.mainloop()

if __name__ == "__main__":
    app = App()
    app.start()


# -*- coding: utf-8 -*-

from Tkinter import *
from tube_map import tube_map
from utracer_data import utracer_data
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from graphing import single_axis_graph, multi_axis_graph
from data_element import data_element
from button_frame import button_frame
from collections import OrderedDict
from action_type import *
from globals import *
from utility import *
from range import range
import os

COL_BG = 'ivory'
COL_SELECT = 'red'
DATA_DIRECTORY = 'data/'

class main_panel(Frame) :

    def __init__(self) :
        self.tube_map = None
        Frame.__init__(self, bg=COL_BG)
        self.pack()
        self.master.title('Tube Data')
        self.control = Frame(self, bg=COL_BG, width=CONTROL_WIDTH, height=CONTROL_HEIGHT)
        self.control.pack(anchor=N, side=LEFT, expand=False)
        self.data_source_frame = LabelFrame(self.control, text="Tube Data File", bg=COL_BG)
        self.data_source_frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY, fill=X)
        self.data_source = Entry(self.data_source_frame)
        self.data_source.pack(side=LEFT, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.data_source.bind('<Return>', self.data_change)
        self.op = StringVar()
        self.op.trace('w', self.op_change)
        lf = LabelFrame(self.control, text="Curves to Plot", bg=COL_BG)
        lf.pack(anchor=W, side=TOP, padx=GLOBAL_PADX, pady=GLOBAL_PADY, fill=X)
        self.plot_params_frame = LabelFrame(self.control, text="Parameters", bg=COL_BG, height=PARAMS_HEIGHT)
        self.plot_params_frame.pack(anchor=W, side=TOP, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.button_frame = button_frame(self.control,
                                         ('Plot', self.plot),
                                         ('Quit', self.quit),
                                         ('Configure', self.configure),
                                         ('Apply', self.apply_config),
                                         ('Cancel', self.cancel_config))
        self.canvas_frame = Frame(self, bg=COL_BG, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas_frame.pack(side=RIGHT, expand=False)
        self.canvas = None
        self.operations = OrderedDict()
        for a in (("Plate Curves", plate_action),
                  ("Grid Curves", grid_action),
                  ("Derivatives", deriv_action)) :
            self.operations[a[0]] = a[1](self.plot_params_frame, self.button_frame, self.get_tube_map)
        for op in self.operations.iterkeys() :
            Radiobutton(lf, text = op, padx=GLOBAL_PADX, bg=COL_BG, \
                        variable=self.op, anchor=W, value=op, indicatoron=0 \
                        ).pack(side=TOP, anchor=W, fill=X)
        self.configure_action = config_action(self.plot_params_frame, self.button_frame)
        self.current_action = self.operations["Plate Curves"]
        self.previous_action = self.current_action
        self.current_action.install()

    def plot(self) :
        if self.current_action :
            self.show_graph(self.current_action.plot())

    def get_tube_map(self) :
        return self.tube_map

    def apply_config(self) :
        self.data_path = self.configure_action['data_path']
        self.cancel_config()

    def cancel_config(self) :
        self.install_action(self.previous_action)
        self.previous_action = self.current_action
        
    def configure(self) :
        self.install_action(self.configure_action)

    def op_change(self, *args) :
        self.install_action(self.operations[self.op.get()])

    def install_action(self, action) :
        self.previous_action = self.current_action
        if self.current_action :
            self.current_action.uninstall()
        self.current_action = action
        self.current_action.install()

    def data_change(self, *args) :
        utd = utracer_data(DATA_DIRECTORY + self.data_source.get())
        self.tube_map = tube_map(utd, title=os.path.basename(self.data_source.get()).split('.')[0].upper())
        for op in self.operations.values() :
            op.reset_data()

    def show_graph(self, graph) :
        try :
            self.canvas.get_tk_widget().delete("all")
            self.canvas._tkcanvas.pack_forget()
        except : pass
        self.canvas = FigureCanvasTkAgg(graph.figure, master=self.canvas_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=RIGHT, fill=BOTH, expand=1)

if __name__=='__main__' :
    mp = main_panel()
    mp.mainloop()


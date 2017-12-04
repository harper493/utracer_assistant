# -*- coding: utf-8 -*-

from Tkinter import *
from tube_map import tube_map
from utracer_data import utracer_data
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from graphing import single_axis_graph, multi_axis_graph
from data_element import data_element
from collections import OrderedDict
from globals import *
from utility import *
from range import range

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
        self.operations = OrderedDict()
        self.operations["Plate Curves"] = self.plate
        self.operations["Grid Curves"] = self.grid
        self.operations["Derivatives"] = self.deriv
        lf = LabelFrame(self.control, text="Curves to Plot", bg=COL_BG)
        lf.pack(anchor=W, side=TOP, padx=GLOBAL_PADX, pady=GLOBAL_PADY, fill=X)
        for op in self.operations.iterkeys() :
            Radiobutton(lf, text = op, padx=GLOBAL_PADX, bg=COL_BG, \
                        variable=self.op, anchor=W, value=op, indicatoron=0 \
                        ).pack(side=TOP, anchor=W, fill=X)
        self.plot_params_frame = LabelFrame(self.control, text="Plot Parameters", bg=COL_BG, height=PARAMS_HEIGHT)
        self.plot_params_frame.pack(anchor=W, side=TOP, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.buttons = Frame(self.control, bg='beige')
        self.buttons.pack(anchor=S, side=BOTTOM)
        self.make_button('Plot', self.plot)
        self.make_button('Quit', self.quit)
        self.make_button('Configure', self.configure)
        self.canvas_frame = Frame(self, bg=COL_BG, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas_frame.pack(side=RIGHT, expand=False)
        self.canvas = None
        self.plate_frame = Frame(self.plot_params_frame, bg=COL_BG, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.grid_frame = Frame(self.plot_params_frame, bg=COL_BG, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.deriv_frame = Frame(self.plot_params_frame, bg=COL_BG, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.make_plate_data()
        self.make_grid_data()
        self.make_deriv_data()
        self.plot_fn = None
        self.plot_params = None

    def make_button(self, label, command) :
        Button(self.buttons, text=label, command=command, \
               bg='gold'). \
            pack(side=LEFT, padx=4, pady=3)

    def plot(self) :
        if self.plot_fn :
            self.plot_fn()

    def configure(self) :
        return None

    def plate(self) :
        self.plate_frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.plot_params = self.plate_frame
        self.plate_data.display()
        self.plot_fn = self.plot_plate

    def make_plate_data(self) :
        self.plate_data = data_element(
            parent = self.plate_frame,
            attributes = (('min_va', 'Min Va', { 'dflt':0 }),
                          ('max_va', 'Max Va', { 'dflt':round(self.get_tm_data(tube_map.va_max), 2) }),
                          ('min_vg', 'Min Vg', { 'dflt':round(self.get_tm_data(tube_map.vg_min), 2) }),
                          ('max_vg', 'Max Vg', { 'dflt':0 }),
                          ('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max), 2) })),
            format = (('min_va', 'max_va'),
                      ('min_vg', 'max_vg'),
                      ('min_ia', 'max_ia'),))

    def grid(self) :
        self.grid_frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.plot_params = self.grid_frame
        self.grid_data.display()
        self.plot_fn = self.plot_grid

    def make_grid_data(self) :
        self.grid_data = data_element(
            parent = self.grid_frame,
            attributes = (('min_vg', 'Min Vg', { 'dflt':round(self.get_tm_data(tube_map.vg_min), 2) }),
                          ('max_vg', 'Max Vg', { 'dflt':0 }),
                          ('min_va', 'Min Va', { 'dflt':0 }),
                          ('max_va', 'Max Va', { 'dflt':round(self.get_tm_data(tube_map.va_max), 2) }),
                          ('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max), 2) })),
            format = (('min_vg', 'max_vg'),
                      ('min_va', 'max_va'),
                      ('min_ia', 'max_ia'),))

    def deriv(self) :
        self.deriv_frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.plot_params = self.deriv_frame
        self.deriv_data.display()
        self.plot_fn = self.plot_deriv

    def make_deriv_data(self) :
        self.deriv_data = data_element(
            parent = self.deriv_frame,
            attributes = (('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max)/2, 2) }),
                          ('va', '*Fixed Va', { 'dflt':0 }),
                          ('vg', '*Fixed Vg', { 'dflt':0 }),
                          ('eb', '*Fixed Eb', { 'dflt':0 }),
                          ('rl', 'Rl (KΩ)', { 'dflt':0 }),
                          ('show_va_vg', '?Show Va & Vg')),
            format = (('min_ia', 'max_ia'), ('va',), ('vg',), ('eb', 'rl'), ('show_va_vg',)))

    def get_tm_data(self, fn) :
        if self.tube_map :
            return fn(self.tube_map)
        else :
            return 0

    def op_change(self, *args) :
        if self.plot_params :
            self.plot_params.pack_forget()
        self.operations[self.op.get()]()

    def data_change(self, *args) :
        utd = utracer_data(DATA_DIRECTORY + self.data_source.get())
        self.tube_map = tube_map(utd)
        self.make_plate_data()
        self.make_grid_data()
        self.make_deriv_data()

    def show_graph(self, graph) :
        try :
            self.canvas.get_tk_widget().delete("all")
            self.canvas._tkcanvas.pack_forget()
        except : pass
        self.canvas = FigureCanvasTkAgg(graph.figure, master=self.canvas_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=RIGHT, fill=BOTH, expand=1)

    def plot_plate(self) :
        curves = []
        labels = []
        d = self.plate_data
        x_values = range(d['min_va'], d['max_va'])
        y_axis = range(d['min_ia'], d['max_ia'])
        if d.is_updated('min_vg') or d.is_updated('max_vg') :
            vg_values = range(d['min_vg'], d['max_vg'])
        else :
            vg_values = self.tube_map.vg_values()
        for vg in vg_values :
            curves.append([self.tube_map(va, vg) for va in x_values])
            labels.append("Vg = %.1f" % (vg,))
        graph = single_axis_graph(x_values=x_values, y_values=curves, labels=labels, x_label="Va",
                                  y_label="Ia (mA)", y_axis=y_axis,
                                  title=self.data_source.get(), subtitle=u"Plate Curves")
        graph.finish()
        self.show_graph(graph)

    def plot_grid(self) :
        curves = []
        labels = []
        d = self.grid_data
        x_values = range(d['min_vg'], d['max_vg'])
        y_axis = range(d['min_ia'], d['max_ia'])
        if d.is_updated('min_va') or d.is_updated('max_va') :
            va_values = range(d['min_va'], d['max_va'])
        else :
            va_values = self.tube_map.va_values()
        for va in va_values :
            curves.append([self.tube_map(va, vg) for vg in x_values])
            labels.append("Va = %.0f" % (va,))
        graph = single_axis_graph(x_values=x_values, y_values=curves, labels=labels, x_label="Vg",
                                  y_label="Ia (mA)", y_axis=y_axis,
                                  title=self.data_source.get(), subtitle=u"Grid Curves")

    def plot_deriv(self) :
        eb = va = vg = rl = 0
        method = self.deriv_data.get_radio_value()
        d = self.deriv_data
        ia = range(d['min_ia'], d['max_ia'])
        if method=='eb' :
            eb, rl = d['eb'], d['rl']
            note = u"Eb = %.0f V Rl=%.1f KΩ" % (eb, rl)
        elif method=='vg':
            vg = d['vg']
            note = "Vg = %.2f V" % (vg,)
        else :                  # must be 'va'
            va = d['va']
            note = "Va = %.0f V" % (va,)
        derivs = self.tube_map.get_derivatives(Eb=eb, Va=va, Vg=vg, Rl=rl, Ia=ia)
        labels = ["Gm (mA/V)", u"Rp (KΩ)", u"µ"]
        if d['show_va_vg'] :
            labels += ["Va", "Vg"]
        graph = multi_axis_graph(x_values=derivs[0], y_values=derivs[1:len(labels) + 1],
                                 labels=labels, x_label="Ia (ma)", title=self.data_source.get(),
                                 subtitle=u"Gm, Rp and µ", note=note)
        graph.finish()
        self.show_graph(graph)

mp = main_panel()
mp.mainloop()


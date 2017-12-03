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
        try :
            f = self.plate_frame
        except AttributeError :
            self.plate_frame = Frame(self.plot_params_frame, bg=COL_BG, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
            self.plate_data = data_element(
                parent = self.plate_frame,
                attributes = (('min_va', 'Min Va', { 'dflt':0 }),
                              ('max_va', 'Max Va', { 'dflt':round(self.tube_map.va_max(), 2) }),
                              ('min_vg', 'Min Vg', { 'dflt':round(self.tube_map.vg_min(), 2) }),
                              ('max_vg', 'Max Vg', { 'dflt':0 }),
                              ('min_ia', 'Min Ia', { 'dflt':0 }),
                              ('max_ia', 'Max Ia', { 'dflt':round(self.tube_map.ia_max(), 2) })),
                format = (('min_va', 'max_va'),
                          ('min_vg', 'max_vg'),
                          ('min_ia', 'max_ia'),))
        self.plate_frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.plot_params = self.plate_frame
        self.plate_data.display()
        self.plot_fn = self.plot_plate

    def grid(self) :
        print 'Grid'

    def deriv(self) :
        print 'Deriv'

    def op_change(self, *args) :
        if self.plot_params :
            self.plot_params.pack_forget()
        self.operations[self.op.get()]()

    def data_change(self, *args) :
        utd = utracer_data(DATA_DIRECTORY + self.data_source.get())
        self.tube_map = tube_map(utd)

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

mp = main_panel()
mp.mainloop()


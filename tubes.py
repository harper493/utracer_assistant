from Tkinter import *
from tube_map import tube_map
from utracer_data import utracer_data
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from graphing import single_axis_graph, multi_axis_graph
#from data_element import data_element

COL_BG = 'ivory'
DATA_DIRECTORY = 'data/'

class main_panel(Frame) :

    def __init__(self) :
        self.tube_map = None
        Frame.__init__(self, bg='beige')
        self.pack()
        self.master.title('Tube Data')
        self.control = Frame(self, bg=COL_BG)
        self.control.pack(anchor=W, side=LEFT)
        self.op = StringVar()
        self.op.trace('w', self.op_change)
        self.operations = { "Plate Curves" : self.plate, "Grid Curves" : self.grid, "Derivatives" : self.deriv }
        lf = LabelFrame(self.control, text="Values to Plot", bg=COL_BG)
        lf.pack(anchor=W, side=TOP, padx=8, pady=4)
        for op in self.operations.iterkeys() :
            Radiobutton(lf, text = op, padx=5, bg=COL_BG, \
                        variable=self.op, anchor='w', value=op).pack(side=TOP, anchor=W, fill=X)
        self.data_source_frame = Frame(self.control, bg=COL_BG)
        self.data_source_frame.pack(side=TOP, anchor=W, fill=X)
        Label(self.data_source_frame, text="Tube Data File", bg=COL_BG).grid(padx=5)
        self.data_source = Entry(self.data_source_frame)
        self.data_source.grid(row=0, column=1, padx=5)
        self.data_source.bind('<Return>', self.data_change)
        self.buttons = Frame(self.control, bg='beige')
        self.buttons.pack(anchor=W, side=TOP)
        self.make_button('Plot', self.plot)
        self.make_button('Quit', self.quit)
        self.make_button('Configure', self.configure)
        self.plot_fn = None

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
        self.plot_fn = self.plot_plate

    def grid(self) :
        print 'Grid'

    def deriv(self) :
        print 'Deriv'

    def op_change(self, *args) :
        self.operations[self.op.get()]()

    def data_change(self, *args) :
        utd = utracer_data(DATA_DIRECTORY + self.data_source.get())
        self.tube_map = tube_map(utd)

    def show_graph(self, graph) :
        self.canvas = FigureCanvasTkAgg(graph.figure, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.canvas._tkcanvas.pack(side=RIGHT, fill=BOTH, expand=1)

    def plot_plate(self) :
        curves = []
        labels = []
        x_values = self.tube_map.va_values()
        for vg in self.tube_map.vg_values() :
            curves.append([self.tube_map(va, vg) for va in x_values])
            labels.append("Vg = %.1f" % (vg,))
        graph = single_axis_graph(x_values=x_values, y_values=curves, labels=labels, x_label="Va", y_label="Ia (mA)",
                              title=self.data_source.get(), subtitle=u"Plate Curves")
        graph.finish()
        self.show_graph(graph)

mp = main_panel()
mp.mainloop()


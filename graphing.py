from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
from utility import *
import scipy
import numpy as np
from range import range
import sys

color_list = [ 'red', 'lime', 'mediumblue', 'orange', 'purple', 'turquoise',
               'green', 'yellow', 'brown', 'deepskyblue', 'hotpink', 'peru', 'tomato',
               'olive']

class graph_base(object) :

    arg_table = { \
    'x_values': [],
    'y_values' : [[]],
    'y_axis' : None,
    'x_label' : '',
    'y_label' : '',
    'labels' : [],
    'title' : '',
    'subtitle' : '',
    'titlepos' : None,
    'note' : None,
    }

    def __init__(self, **kwargs):
        construct(self, graph_base.arg_table, kwargs)
        self.figure, self.subplot = plt.subplots()
        self.legends = []
        #self.figure.set_size_inches(9,7, forward=True)

    def add_plot(self, subplot, x, y, label=None, color='black'):
        new_x = np.linspace(min(x), max(x), num=len(x) * 10, endpoint=True)
        interp = scipy.interpolate.interp1d(x, y, kind='cubic')
        p, = subplot.plot(new_x, interp(new_x), label=label, color=color)
        return p

    def add_legend(self) :
        if self.legends:
            z = zip(*self.legends)
            self.legend = self.subplot.legend(handles=z[0], labels=z[1], loc="best")
        else :
            self.legend = self.subplot.legend(loc="best")
        self.legend.get_frame().set_alpha(0.3)

    def add_legend_item(self, label, color):
        self.legends.append((plt.Line2D((0,1),(0,0), color=color), label))
        
    def add_title(self):
        if self.title :
            text = self.title
            if self.subtitle :
                text += ': '
                text += self.subtitle
            self.subplot.title.set_position(self.titlepos or (0.5, 1.05))
            self.subplot.title.set_text(text)
            self.subplot.title.set_size(14)
            self.subplot.title.set_weight("bold")

    def add_note(self):
        if self.note :
            self.subplot.text(0.5, 0.9, self.note, transform=self.subplot.transAxes, fontsize=12, fontweight="bold")

    def _do_x_axis(self) :
        if isinstance(self.x_values, range) :
            self.x_values = self.x_values.values()
        self.x_max = round(max(self.x_values), 2)
        self.x_min = round(min(self.x_values), 2, round_up=False)
        self.subplot.set_xlim(self.x_min, self.x_max)
        self.subplot.set_xlabel(self.x_label)

    def _do_y_axis(self, values=None):
        values = values or self.y_values
        if isinstance(values, range) :
            values = self.values.values()
        if self.y_axis :
            self.y_min, self.y_max = min(self.y_axis), max(self.y_axis)
        else :
            self.y_max = round(max([max(y) for y in values]), 2)
            self.y_min = round(min([min(y) for y in values]), 2, round_up=False)
        if len(self.labels) < len(values):
            self.labels += [''] * (len(values) - len(self.labels))
        self.subplot.set_ylim(self.y_min, self.y_max)
        if self.y_label :
            self.subplot.set_ylabel(self.y_label)

    def finish(self):
        self.add_title()
        self.add_note()
        self.add_legend()

    def show(self) :
        self.finish()
        plt.show()

    def colors(self) :
        while True :
            for c in color_list :
                yield c

class single_axis_graph(graph_base) :

    def __init__(self, **kwargs) :
        graph_base.__init__(self, **kwargs)
        self._do_x_axis()
        self._do_y_axis()
        for lab, y, c in zip(self.labels, self.y_values, self.colors()):
            self.add_plot(self.subplot, self.x_values, y, lab, color=c)

class multi_axis_graph(graph_base) :

    def __init__(self, **kwargs) :
        graph_base.__init__(self, **kwargs)
        self.figure.subplots_adjust(right=0.65)
        self.subplots = [ self.subplot ]
        offset = 1
        for l in self.labels[1:] :
            sp = self.subplot.twinx()
            self.subplots.append(sp)
            sp.spines['right'].set_position(('axes', offset))
            sp.set_frame_on(True)
            sp.patch.set_visible(False)
            offset += 0.16
        self._do_x_axis()
        legends = []
        for sp, l, y, c in zip(self.subplots, self.labels, self.y_values, self.colors()) :
            p = self.add_plot(sp, self.x_values, y, l, color=c)
            ymin = round(min(min(y), 0), 1, round_up=False)
            ymax = 0 if max(y)<=0 else round(max(y), 1)
            sp.set_ylim(ymin, ymax)
            sp.set_ylabel(l, color=c)
            sp.tick_params('y', colors=c)
            self.add_legend_item(l, c)


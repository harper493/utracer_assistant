from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
from utility import *
import scipy
import numpy as np
from range import range

class graph_base(object) :

    arg_table = { \
    'x_values': [],
    'y_values' : [[]],
    'x_axis' : None,
    'x_label' : '',
    'labels' : [],
    'title' : '',
    'subtitle' : '',
    'titlepos' : None,
    'note' : None,
    }

    def __init__(self, **kwargs):
        construct(self, graph_base.arg_table, kwargs)
        self.subplot = host_subplot(111, axes_class=AA.Axes)

    def add_plot(self, x, y, label=None):
        print '^^^', x, label, y
        new_x = np.linspace(min(x), max(x), num=len(x) * 10, endpoint=True)
        interp = scipy.interpolate.interp1d(x, y, kind='cubic')
        p, = self.subplot.plot(new_x, interp(new_x), label=label)
        return p

    def add_legend(self) :
        self.legend = self.subplot.legend(loc="best")
        self.legend.get_frame().set_alpha(0.3)
        
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
        self.y_max = round(max([max(y) for y in values]), 2)
        self.y_min = round(min([min(y) for y in values]), 2, round_up=False)
        if len(self.labels) < len(values):
            self.labels += [''] * (len(values) - len(self.labels))
        self.subplot.set_ylim(self.y_min, self.y_max)

    def show(self):
        self.add_title()
        self.add_legend()
        self.add_note()
        plt.show()

class single_axis_graph(graph_base) :

    def __init__(self, **kwargs) :
        graph_base.__init__(self, **kwargs)
        self._do_x_axis()
        self._do_y_axis()
        for lab, y in zip(self.labels, self.y_values):
            self.add_plot(self.x_values, y, lab)


class multi_axis_graph(graph_base) :

    def __init__(self, **kwargs) :
        graph_base.__init__(self, **kwargs)
        self._do_x_axis()
        plt.subplots_adjust(right=0.75)
        offset = 0
        self.y_plots = []
        for l in self.labels[1:]:
            par = self.subplot.twinx()
            self.y_plots.append(par)
            new_fixed_axis = par.get_grid_helper().new_fixed_axis
            par.axis["right"] = new_fixed_axis(loc="right", axes=par,
                                                   offset=(offset, 0))
            offset += 40
            par.axis["right"].toggle(all=True)
            par.set_ylabel(l)
        self._do_y_axis()
        p = self.add_plot(self.x_values, self.y_values[0], self.labels[0])
        self.subplot.set_ylabel(self.labels[0])
        self.subplot.axis["left"].label.set_color(p.get_color())
        for par, l, y in zip(self.y_plots, self.labels[1:], self.y_values[1:]) :
            p = self.add_plot(self.x_values, y, l)
            par.set_ylim(0, round(max(y)))
            par.axis["right"].label.set_color(p.get_color())
        self.add_legend()


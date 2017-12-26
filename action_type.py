# -*- coding: utf-8 -*-

from Tkinter import *
from globals import *
from utility import *
from graphing import single_axis_graph, multi_axis_graph
from data_element import data_element
from tube_map import tube_map
from range import range

class action_type(object) :

    def __init__(self, parent_frame, button_frame) :
        self.parent_frame, self.button_frame = parent_frame, button_frame
        self.frame = Frame(parent_frame, bg=BGCOL_BG, padx=GLOBAL_PADX, pady=GLOBAL_PADY)

    def install(self) :
        self.frame.pack(side=TOP, anchor=W, padx=GLOBAL_PADX, pady=GLOBAL_PADY)
        self.data.display()

    def uninstall(self) :
        self.frame.forget()

    def plot(self) :
        return None

    def apply(self) :
        return None

    def reset_data(self) :
        pass

class plot_action(action_type) :

    def __init__(self, parent_frame, button_frame, get_tube_map) :
        super(plot_action, self).__init__(parent_frame, button_frame)
        self.get_tube_map = get_tube_map

    def install(self) :
        if self.get_tube_map() :
            self.button_frame.show('Plot', 'Configure')
        else :
            self.button_frame.show('Configure')
        super(plot_action, self).install()

    def get_tm_data(self, fn) :
        if self.get_tube_map() :
            return fn(self.get_tube_map())
        else :
            return 0

class plate_action(plot_action) :

    def __init__(self, parent_frame, button_frame, get_tube_map) :
        super(plate_action, self).__init__(parent_frame, button_frame, get_tube_map)
        self.reset_data()

    def reset_data(self) :
        self.data = data_element(self.frame,
            attributes = (('min_va', 'Min Va', { 'dflt':0 }),
                          ('max_va', 'Max Va', { 'dflt':round(self.get_tm_data(tube_map.va_max), 2) }),
                          ('min_vg', 'Min Vg', { 'dflt':round(self.get_tm_data(tube_map.vg_min), 2) }),
                          ('max_vg', 'Max Vg', { 'dflt':0 }),
                          ('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max), 2) })),
            format = (('min_va', 'max_va'),
                      ('min_vg', 'max_vg'),
                      ('min_ia', 'max_ia'),))

    def plot(self) :
        curves = []
        labels = []
        d = self.data
        x_values = range(d['min_va'], d['max_va'])
        y_axis = range(d['min_ia'], d['max_ia'])
        if d.is_updated('min_vg') or d.is_updated('max_vg') :
            vg_values = range(d['min_vg'], d['max_vg'])
        else :
            vg_values = self.get_tube_map().vg_values()
        for vg in vg_values :
            curves.append([self.get_tube_map()(va, vg) for va in x_values])
            labels.append("Vg = %.1f" % (vg,))
        graph = single_axis_graph(x_values=x_values, y_values=curves, labels=labels, x_label="Va",
                                  y_label="Ia (mA)", y_axis=y_axis,
                                  title=self.get_tube_map().title, subtitle=u"Plate Curves")
        graph.finish()
        return graph

class grid_action(plot_action) :

    def __init__(self, parent_frame, button_frame, get_tube_map) :
        super(grid_action, self).__init__(parent_frame, button_frame, get_tube_map)
        self.reset_data()

    def reset_data(self) :
        self.data = data_element(self.frame,
            attributes = (('min_vg', 'Min Vg', { 'dflt':round(self.get_tm_data(tube_map.vg_min), 2) }),
                          ('max_vg', 'Max Vg', { 'dflt':0 }),
                          ('min_va', 'Min Va', { 'dflt':0 }),
                          ('max_va', 'Max Va', { 'dflt':round(self.get_tm_data(tube_map.va_max), 2) }),
                          ('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max), 2) })),
            format = (('min_vg', 'max_vg'),
                      ('min_va', 'max_va'),
                      ('min_ia', 'max_ia'),))

    def plot(self) :
        curves = []
        labels = []
        d = self.data
        x_values = range(d['min_vg'], d['max_vg'])
        y_axis = range(d['min_ia'], d['max_ia'])
        if d.is_updated('min_va') or d.is_updated('max_va') :
            va_values = range(d['min_va'], d['max_va'])
        else :
            va_values = self.get_tube_map().va_values()
        for va in va_values :
            curves.append([self.get_tube_map()(va, vg) for vg in x_values])
            labels.append("Va = %.0f" % (va,))
        graph = single_axis_graph(x_values=x_values, y_values=curves, labels=labels, x_label="Vg",
                                  y_label="Ia (mA)", y_axis=y_axis,
                                  title=self.get_tube_map().title, subtitle=u"Grid Curves")
        graph.finish()
        return graph

class deriv_action(plot_action) :

    def __init__(self, parent_frame, button_frame, get_tube_map) :
        super(deriv_action, self).__init__(parent_frame, button_frame, get_tube_map)
        self.reset_data()

    def reset_data(self) :
        self.data = data_element(self.frame,
            attributes = (('min_ia', 'Min Ia', { 'dflt':0 }),
                          ('max_ia', 'Max Ia', { 'dflt':round(self.get_tm_data(tube_map.ia_max)/2, 2) }),
                          ('va', '*Fixed Va', { 'dflt':0 }),
                          ('vg', '*Fixed Vg', { 'dflt':0 }),
                          ('eb', '*Fixed Eb', { 'dflt':0 }),
                          ('rl', 'Rl (KΩ)', { 'dflt':0 }),
                          ('show_va_vg', '?Show Va & Vg')),
            format = (('min_ia', 'max_ia'), ('va',), ('vg',), ('eb', 'rl'), ('show_va_vg',)))

    def plot(self) :
        eb = va = vg = rl = 0
        d = self.data
        method = d.get_radio_value()
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
        derivs = self.get_tube_map().get_derivatives(Eb=eb, Va=va, Vg=vg, Rl=rl, Ia=ia)
        labels = ["Gm (mA/V)", u"Rp (KΩ)", u"µ"]
        if d['show_va_vg'] :
            labels += ["Va", "Vg"]
        graph = multi_axis_graph(x_values=derivs[0], y_values=derivs[1:len(labels) + 1],
                                 labels=labels, x_label="Ia (ma)", title=self.get_tube_map().title,
                                 subtitle=u"Gm, Rp and µ", note=note)
        graph.finish()
        return graph

class config_action(action_type) :

    def __init__(self, parent_frame, button_frame) :
        super(config_action, self).__init__(parent_frame, button_frame)
        self.data = data_element(self.frame,
            attributes = (('data_path', 'Data Path', { 'datatype':'str', 'dflt':'./data/' }),),
            format = (('data_path',),))
        self.apply()

    def install(self) :
        self.button_frame.show('Apply', 'Cancel')
        super(config_action, self).install()

    def apply(self) :
        self.data_path = self.data['data_path']

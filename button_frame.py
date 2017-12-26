from Tkinter import *
from globals import *
from utility import *
from collections import OrderedDict

class button_frame(object) :

    class button(object) :

        def __init__(self, parent, label, fn) :
            self.tk_button = Button(parent, text=label, command=fn, bg=BGCOL_BUTTON)
            self.active = False

        def activate(self) :
            if not self.active :
                self.tk_button.pack(side=LEFT, padx=4, pady=3)
                self.active = True

        def deactivate(self) :
            if self.active :
                self.tk_button.forget()
                self.active = False

    def __init__(self, parent, *buttons) :
        self.frame = Frame(parent, bg=BGCOL_BG)
        self.frame.pack(anchor=S, side=BOTTOM)
        self.buttons = OrderedDict()
        self.add_buttons(buttons)

    def add_button(self, label, fn) :
        self.buttons[label] = button_frame.button(self.frame, label, fn)

    def add_buttons(self, buttons) :
        for b in buttons :
            self.add_button(b[0], b[1])

    def show(self, *button_list) :
        for l, b in self.buttons.items() :
            if l in button_list or l=='Quit' :
                b.activate()
            else :
                b.deactivate()
                
            

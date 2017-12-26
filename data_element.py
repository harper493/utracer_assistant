import re
import operator
from globals import *
from Tkinter import *

class data_element(object) :

    def __init__(self, parent=None, title='', attributes=None, format=None) :
        self.children = {}
        self.attributes = {}
        self.display_format = format or []
        self.parent = parent
        self.title = title
        self.radioval = StringVar()
        if attributes :
            self.add_attributes(attributes)

    def add_child(self, name, child) :
        self.children[name] = child
        setattr(self, name, child)

    def add_attribute(self, name, attr) :
        self.attributes[name] = attr
        setattr(self, name, attr.value)

    def set_attribute(self, name, value) :
        self.attributes[name].set_value(value)
        setattr(self, name, self.attributes[name].value)

    def set_attributes(**attrs) :
        for aname, val in attrs.iteritems() :
            self.attributes[aname].set_value(val)
            setattr(self, aname, self.attributes[aname].value)

    def add_attributes(self, attrs) :
        for a in attrs :
            attr = self._make_attribute(a)
            self.attributes[a[0]] = attr
            setattr(self, a[0], attr)

    def _make_attribute(self, params) :
        try :
            t = params[2]['datatype']
        except (KeyError, IndexError) :
            t = 'float'
        if params[1][0]=='?' :
            return data_attribute_check(params)
        elif t=='float' :
            return data_attribute_float(params) 
        elif t=='choice' :
            return data_attribute_choice(params)
        elif t=='str' :
            return data_attribute(params)
        else :
            raise NameError, "unknown data attribute type '%s'" % t

    def get_attribute_value(self, aname) :
        attr = self.attributes[aname]
        return attr.get_value()

    def __getitem__(self, aname) :
        return self.get_attribute_value(aname)

    def get_radio_value(self) :
        rv = self.radioval.get()
        for n,attr in self.attributes.items() :
            if rv==attr.descr[1:] :
                return n
        return ''

    def is_updated(self, aname) :
        return self.attributes[aname].updated

    def load_config(self, path) :
        f = open(path, 'r')
        for line in f :
            m = re.match(r'\s*(?:(#.*)|(\w+)\s*=\s*(.*))?', line)
            if m.group(2) :
                self._process_config_line(m.group(2), m.group(3))

    def _process_config_line(self, tag, value) :
        m = re.match(r'([^.]+)(:?\.(.*))?', tag)
        if m :
            if m.group(2) :
                try :
                    child = self.children[m.group(1)]
                except KeyError :
                    child = None
                if child :
                    child.process_config_line(m.group(2), value)
            else :
                try :
                    attr = self.attributes[m.group(1)]
                except KeyError :
                    attr = None
                if attr :
                    attr.set_value(value)
        else :
            raise ValueError, "bad config line, tag='%s', value='%s'" % (tag, value)

    def save_config(self, path) :
        f = open (path, 'w')
        f.write(self.make_config())

    def make_config(self, prefix='') :
        result = []
        plist = [prefix] if len(prefix) else []
        for cname, c in self.children.iteritems() :
            result.append(c.make_config('.'.join(plist+[cname])))
        for aname, a in self.attributes.iteritems() :
            result.append("%s=%s" % ('.'.join(plist+[aname]), a.get_value()))
        return '\n'.join(result)

    def display(self, start_row=0) :
        row = start_row
        maxcols = max([2*len(r) for r in self.display_format])
        for r in self.display_format :
            if len(r)==1 and r[0][0]=='$' :
                Label(self.parent, text=r[0][1:], bg=BGCOL_LABEL) . \
                    grid(row=row, columnspan=maxcols, padx=GLOBAL_TITLE_PADX, pady=GLOBAL_TITLE_PADY, \
                         sticky=E+W)
            else :
                col = 0
                for a in r :
                    attr = self.attributes[a]
                    if attr.descr[0]=='*' :
                        attr.label = Radiobutton(self.parent, text=attr.descr[1:], bg=BGCOL_BG,
                                    variable=self.radioval, anchor=W, value=attr.descr[1:])
                    elif attr.descr[0]=='?' :
                        var = IntVar()
                        attr.label = Checkbutton(self.parent, text=attr.descr[1:], bg=BGCOL_BG,
                                                 anchor=W, variable=var)
                        attr.label.var = var
                    elif attr.descr=='!' :
                        attr.label = Button(self.parent, text=attr.descr[1:], command=attr.command, bg=BGCOL_BG,
                                            anchor=W)
                    else :
                        attr.label = Label(self.parent, text=attr.descr, bg=BGCOL_BG)
                    attr.label.grid(row=row, column=col, padx=GLOBAL_LABEL_PADX, pady=GLOBAL_PADY, sticky=W)
                    if attr.descr[0]!='?' and attr.descr[0]!='!' :
                        attr.make_widget(self.parent). \
                            grid(row=row, column=col+1, padx=GLOBAL_LABEL_PADX, pady=GLOBAL_PADY, sticky=W)
                    col += 2
            row += 1
        return row

    def apply(self) :
        for a in self.attributes.itervalues() :
            a.apply()
        self.update()

    def dialog(self, parent) :
        self.top = Toplevel(parent, bg=BGCOL_BG)
        self.top.title(self.title)
        body = Frame(self.top, bg=BGCOL_BG)
        body.pack(side=TOP)
        self.display(body)
        buttons = Frame(self.top, bg=BGCOL_BG)
        buttons.pack(side=BOTTOM, expand=YES)
        Button(buttons, text='Cancel', command=self.top.quit, bg=BGCOL_BUTTON). \
            pack(side=LEFT, padx=10, pady=4)
        Button(buttons, text='Done', command=self.done, bg=BGCOL_BUTTON). \
            pack(side=LEFT, padx=10, pady=4)
        self.top.mainloop()

    def done(self) :
        self.apply()
        self.top.quit()
        self.top.destroy()
        self.top = None

    def update(self) :
        return
        for a in self.attributes.iterkeys() :
            setattr(self, a, self.attributes[a])
    

class data_attribute(object) :

    def __init__(self, params) :
        self.name, self.descr = params[0], params[1]
        self.type, self.dflt, self.range, self.validator, self.choices, self.command = \
            str, None, None, None, None, None
        self.readonly = False
        self.width = GLOBAL_ENTRY_WIDTH
        if len(params)>=3 :
            for pname, pval in params[2].iteritems() :
                if pname=='datatype' :
                    self.datatype = pval
                elif pname=='dflt' :
                    self.dflt = pval
                elif pname=='range' :
                    self.range = pval
                elif pname=='validator' :
                    self.validator = pval
                elif pname=='readonly' :
                    self.readonly = pval
                elif pname=='width' :
                    self.width = pval
                elif pname=='choices' :
                    self.choices = pval
                elif pname=='command' :
                    self.command = pval
        self.value = self.dflt
        self.updated = False
        self.widget = None
        self.var = None

    def validate(self, value) :
        v = self.make_value(value)
        if v is None :
            return False
        if self.validator and not self.validator(v) :
            return False
        if self.range :
            minval = self.range[0]
            maxval = self.range[1]
            if minval and minval>v :
                return False
            if maxval and maxval<v :
                return False
        return True
                    
    def make_widget(self, parent) :
        self.var = StringVar()
        self.var.set(str(self.value))
        self.var.trace('w', self.update)
        state = 'readonly' if self.readonly else NORMAL
        self.make_my_widget(parent)
        self.update(None, None, None)
        return self.widget

    def make_my_widget(self, parent) :
        self.widget = Entry(parent, textvariable=self.var, width=self.width)

    def set_value(self, value) :
        if value :
            if self.validate(value) :
                self.value = self.make_value(value)
        else :
            self.value = self.dflt
        if self.var :
            self.var.set(str(self.value))

    def get_value(self) :
        if self.var :
            self.set_value(self.var.get())
        return self.value

    def get_widget_value(self) :
        if self.widget :
            return self.widget.get()
        else :
            return None

    def make_value(self, value) :
        try :
            return self.type(value)
        except ValueError :
            return None

    def clear_widget(self) :
        self.widget = None
        self.var = None

    def update(self, name, index, mode) :
        if self.widget :
            if self.name is not None :
                self.updated = True
            if self.validate(self.get_widget_value()) :
                self.widget.config(background=BGCOL_GOOD)
            else :
                self.widget.config(background=BGCOL_BAD)

    def apply(self) :
        self.set_value(self.get_widget_value())

class data_attribute_scalar(data_attribute) :

    def __init__(self, params) :
        data_attribute.__init__(self, params)

class data_attribute_check(data_attribute) :

    def __init__(self, params) :
        data_attribute.__init__(self, params)
        self.type = bool

    def make_my_widget(self, parent) :
        self.widget = None

    def get_value(self) :
        if self.label :
            return self.label.var.get() != 0
        else :
            return None

class data_attribute_float(data_attribute_scalar) :

    def __init__(self, params) :
        self.type = float
        data_attribute_scalar.__init__(self, params)

    def make_value(self, value) :
        try :
            return float(value)
        except ValueError :
            return None

class data_attribute_choice(data_attribute) :

    def __init__(self, params) :
        data_attribute_scalar.__init__(self, params)

    def make_value(self, value) :
        try :
            if value in self.choices :
                return str(value)
            else :
                return None
        except ValueError :
            return None

    def make_my_widget(self, parent) :
        self.widget = Listbox(width=self.width)
        select = None
        for c in sorted(self.choices) :
            self.widget.insert(END, c)
            if self.value == c :
                select = self.widget.size()-1
        if select :
            self.widget.see(select)
            self.widget.activate(select)

    def get_widget_value(self) :
        try :
            return self.widget.get(self.widget.curselection()[0])
        except :
            return None




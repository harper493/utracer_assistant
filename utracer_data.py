import csv
import os
import re

class utracer_data(object) :
    
    def __init__(self, filename) :
        self._make_filename(filename)
        rowno = 1
        with open(self.filename, 'rb') as f :
            reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
            self.data = []
            for row in reader :
                if rowno==1:
                    anode_down = 'Va' in row
                else :
                    if rowno == 2:
                        row = ' '.join(' '.join(row).split())
                        row = re.sub(r"V\w*\s*=\s*(\S*)\s*V", r"\1", row).split()
                        row = [0] + row
                    row = [float(r) for r in row if r]
                    row = [r if abs(r) > 0.001 else 0 for r in row]
                    self.data.append(row)
                rowno += 1
        if not anode_down :
            r = [[ d[0] for d in self.data[1:]]]
            for i,v in enumerate(zip(*self.data[1:])[1:]) :
                r.append([self.data[0][i]] + list(v))
            self.data = r
        self.make_axes()
        if self.vg[0] > self.vg[-1] :
            self.vg = self.vg[::-1]
            self.data = [ d[::-1] for d in self.data ]

    def make_axes(self):
        self.vg = [-d for d in self.data[0]]
        self.va = [d[0] for d in self.data[1:]]
        self.data = [d[1:] for d in self.data[1:]]

    def get(self):
        return (self.va, self.vg, self.data)

    def _make_filename(self, filename):
        if not (filename.endswith('.txt') or filename.endswith('.utd')) :
            for ext in [ '.utd', '.txt' ] :
                if os.path.exists(filename + ext) :
                    filename += ext
                    break
        f = open(filename, 'rb')              # will throw if file does not exist
        f.close()
        self.filename = filename


